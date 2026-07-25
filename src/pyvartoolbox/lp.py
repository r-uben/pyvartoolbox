"""Local projections (port of ``LPmodel.m``, OLS branch).

Estimates the response of an outcome to a shock horizon by horizon, with a
separate regression at each horizon rather than by iterating a VAR. Inference
uses Newey-West standard errors with bandwidth equal to the horizon, which is
the natural choice because the projection residual at horizon ``h`` is MA(h) by
construction.

Univariate by design: one outcome at a time. Lags of the outcome are *not*
added automatically — pass the outcome among ``ctrl`` if you want to control for
its own lags, which is the usual specification.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from statistics import NormalDist

import numpy as np

from ._lag import make_lags


def newey_west_se(X: np.ndarray, resid: np.ndarray, nlags: int) -> np.ndarray:
    """Newey-West standard errors with Bartlett weights ``(L+1-a)/(L+1)``.

    No small-sample degrees-of-freedom correction, matching upstream's
    ``OLSmodel``. ``nlags=0`` reduces to the heteroskedasticity-robust
    (White) sandwich.
    """
    if nlags < 0:
        raise ValueError(f"nlags must be >= 0, got {nlags}")
    n = X.shape[0]
    if nlags >= n:
        # Beyond this the autocovariance terms have no overlapping observations
        # left, and the lag loop would silently index past the sample.
        raise ValueError(
            f"bandwidth {nlags} needs more than {nlags} observations, got {n}"
        )
    XtXi = np.linalg.pinv(X.T @ X)
    h = X * resid[:, None]

    G = h.T @ h
    for a in range(1, nlags + 1):
        w = (nlags + 1 - a) / (nlags + 1)
        za = h[a:].T @ h[: n - a]
        G = G + w * (za + za.T)

    return np.sqrt(np.diag(XtXi @ G @ XtXi))


@dataclass
class LocalProjection:
    """Impulse responses from local projections, indexed by horizon 0..horizon.

    ``ir[h]`` is the response at horizon ``h`` to the normalised shock. ``lower``
    and ``upper`` are Newey-West bands at coverage ``ci``.
    """

    ir: np.ndarray
    se: np.ndarray
    lower: np.ndarray
    upper: np.ndarray
    ci: float
    nobs: np.ndarray
    beta: list = field(default_factory=list)


def local_projection(
    endo: np.ndarray,
    treat: np.ndarray,
    ctrl: np.ndarray | None = None,
    nlags: int = 4,
    det: int = 1,
    horizon: int = 20,
    ci: float = 0.95,
    unit_shock: bool = False,
    long_diff: bool = False,
) -> LocalProjection:
    """Estimate a local projection of ``endo`` on ``treat``.

    Parameters
    ----------
    endo : array (nobs,)
        Outcome variable.
    treat : array (nobs,)
        Shock or treatment, entering contemporaneously.
    ctrl : array (nobs, nctrl), optional
        Controls, entering with lags ``1..nlags``. Contemporaneous values are
        *not* included.
    nlags : int
        Lag order for the controls, and the leading trim of the sample.
    det : int
        0 none, 1 constant, 2 constant and trend.
    horizon : int
        Maximum horizon; the result has ``horizon + 1`` entries covering
        ``0..horizon``. Upstream's ``LPopt.nsteps = H`` corresponds to
        ``horizon = H - 1``.
    unit_shock : bool
        If False (default) the shock is standardised, so responses are to a
        one-standard-deviation shock, matching ``LPopt.impact = 0``.
    long_diff : bool
        Project the long difference ``y_{t+h} - y_{t-1}`` rather than the level
        ``y_{t+h}``. Standard when the outcome is a log level and the object of
        interest is the cumulative response.

    Notes
    -----
    Bands are pointwise and use the normal quantile, as upstream does; they are
    not joint bands over horizons.
    """
    endo = np.asarray(endo, dtype=float).ravel()
    treat = np.asarray(treat, dtype=float).ravel()
    if endo.shape != treat.shape:
        raise ValueError(
            f"endo has {endo.shape[0]} observations but treat has {treat.shape[0]}"
        )
    if not 0.0 < ci < 1.0:
        raise ValueError(f"ci must be in (0, 1), got {ci}")
    if det not in (0, 1, 2):
        raise ValueError(f"det must be 0, 1 or 2, got {det}")
    if horizon < 0:
        raise ValueError(f"horizon must be >= 0, got {horizon}")

    y = endo[nlags:]
    s = treat[nlags:]
    neff = y.shape[0]

    blocks = []
    if det >= 1:
        blocks.append(np.ones((neff, 1)))
    if det == 2:
        blocks.append(np.arange(1, neff + 1, dtype=float)[:, None])

    if ctrl is not None:
        ctrl = np.asarray(ctrl, dtype=float)
        if ctrl.ndim == 1:
            ctrl = ctrl[:, None]
        if ctrl.shape[0] != endo.shape[0]:
            raise ValueError(
                f"ctrl has {ctrl.shape[0]} rows, expected {endo.shape[0]} to align"
            )
        blocks.append(make_lags(ctrl, nlags))

    controls = np.hstack(blocks) if blocks else np.empty((neff, 0))

    if unit_shock:
        shock = s
    else:
        # Population-style standardisation with ddof=1, matching MATLAB zscore.
        shock = (s - s.mean()) / s.std(ddof=1)

    RHS = np.column_stack([shock, controls])
    conf = NormalDist().inv_cdf(1 - (1 - ci) / 2)

    ir = np.full(horizon + 1, np.nan)
    se = np.full(horizon + 1, np.nan)
    nobs = np.zeros(horizon + 1, dtype=int)
    betas = []

    # y_{t-1} aligned to the same trimmed sample as y_t.
    base = endo[nlags - 1 : -1] if long_diff else None

    for h in range(horizon + 1):
        Y = y[h:]
        if long_diff:
            Y = Y - base[: Y.shape[0]]
        n_h = Y.shape[0]
        # The Newey-West bandwidth at horizon h is h, so the sample must exceed
        # both the regressor count and the bandwidth.
        if n_h <= max(RHS.shape[1], h):
            raise ValueError(
                f"horizon {h} leaves {n_h} observations for {RHS.shape[1]} "
                f"regressors and a bandwidth of {h}; shorten the horizon or "
                "the lag order"
            )
        X = RHS[:n_h]
        beta, *_ = np.linalg.lstsq(X, Y, rcond=None)
        resid = Y - X @ beta
        # Bandwidth h: the horizon-h projection residual is MA(h) by construction.
        ir[h] = beta[0]
        se[h] = newey_west_se(X, resid, h)[0]
        nobs[h] = n_h
        betas.append(beta)

    return LocalProjection(
        ir=ir,
        se=se,
        lower=ir - conf * se,
        upper=ir + conf * se,
        ci=ci,
        nobs=nobs,
        beta=betas,
    )
