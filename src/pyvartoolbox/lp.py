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
    #: First-stage F statistic per horizon; NaN under OLS.
    first_stage_f: np.ndarray | None = None


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
    iv: np.ndarray | None = None,
    nlags_iv: int = 0,
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
    iv : array (nobs,), optional
        External instrument. When given, ``treat`` is treated as an *endogenous*
        treatment and each horizon is estimated by 2SLS rather than OLS, with
        Frisch-Waugh partialling of the controls out of outcome, treatment and
        instruments within the horizon-specific sample.
    nlags_iv : int
        Lags of the instrument to add as extra instruments. Must not exceed
        ``nlags``. With ``nlags_iv = 0`` the model is just identified and the
        Newey-West bandwidth is the horizon; otherwise the bandwidth is fixed at
        ``nlags_iv``, matching upstream (and Stata's ``vce(hac nw nlags_iv)``).

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

    do_iv = iv is not None
    if do_iv:
        iv = np.asarray(iv, dtype=float)
        if iv.ndim == 1:
            iv = iv[:, None]
        if iv.shape[0] != endo.shape[0]:
            raise ValueError(
                f"iv has {iv.shape[0]} rows, expected {endo.shape[0]} to align"
            )
        if nlags_iv > nlags:
            raise ValueError(
                f"nlags_iv ({nlags_iv}) cannot exceed nlags ({nlags}): the extra "
                "instrument lags would reach outside the trimmed sample"
            )
        # Under IV the normalisation applies to the endogenous treatment.
        d_norm = 1.0 if unit_shock else s.std(ddof=1)
        shock = s
    elif unit_shock:
        d_norm = 1.0
        shock = s
    else:
        # Standardisation with ddof=1, matching MATLAB's zscore.
        d_norm = 1.0
        shock = (s - s.mean()) / s.std(ddof=1)

    RHS = np.column_stack([shock, controls])
    conf = NormalDist().inv_cdf(1 - (1 - ci) / 2)

    ir = np.full(horizon + 1, np.nan)
    se = np.full(horizon + 1, np.nan)
    nobs = np.zeros(horizon + 1, dtype=int)
    fstat = np.full(horizon + 1, np.nan)
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
        if not do_iv:
            X = RHS[:n_h]
            beta, *_ = np.linalg.lstsq(X, Y, rcond=None)
            resid = Y - X @ beta
            # Bandwidth h: the horizon-h residual is MA(h) by construction.
            ir[h] = beta[0]
            se[h] = newey_west_se(X, resid, h)[0]
            betas.append(beta)
        else:
            C = controls[:n_h]
            r_y = _partial(Y, C)
            r_d = _partial(s[:n_h], C)

            # Column k holds lag k of the instrument over the trimmed window.
            Z = np.column_stack(
                [iv[nlags - k : nlags + n_h - k, 0] for k in range(nlags_iv + 1)]
            )
            r_z = _partial(Z, C)

            d_hat = r_z @ np.linalg.lstsq(r_z, r_d, rcond=None)[0]
            denom = d_hat @ r_d
            if denom == 0:
                raise ValueError(
                    f"instrument is uncorrelated with the treatment at horizon {h}"
                )
            b = (d_hat @ r_y) / denom
            eps = r_y - b * r_d

            # Just-identified: bandwidth is the horizon. Overidentified: fixed at
            # nlags_iv, matching upstream.
            bw = nlags_iv if nlags_iv > 0 else h
            g = d_hat * eps
            se_h = newey_west_se(np.ones((n_h, 1)), g - g.mean(), bw)[0] / abs(
                denom / n_h
            )

            ir[h] = b * d_norm
            se[h] = se_h * d_norm
            betas.append(np.array([b]))
            fstat[h] = _first_stage_f(r_d, r_z)

        nobs[h] = n_h

    return LocalProjection(
        ir=ir,
        se=se,
        lower=ir - conf * se,
        upper=ir + conf * se,
        ci=ci,
        nobs=nobs,
        beta=betas,
        first_stage_f=fstat if do_iv else None,
    )


def _partial(y: np.ndarray, controls: np.ndarray) -> np.ndarray:
    """Residualise ``y`` on ``controls`` (Frisch-Waugh)."""
    if controls.shape[1] == 0:
        return y
    return y - controls @ np.linalg.lstsq(controls, y, rcond=None)[0]


def _first_stage_f(r_d: np.ndarray, r_z: np.ndarray) -> float:
    """Joint F statistic for the instruments in the residualised first stage."""
    n, kz = r_z.shape
    resid = r_d - r_z @ np.linalg.lstsq(r_z, r_d, rcond=None)[0]
    rss_unrestricted = resid @ resid
    rss_restricted = r_d @ r_d
    if n <= kz or rss_unrestricted <= 0:
        return float("nan")
    return float(
        ((rss_restricted - rss_unrestricted) / kz) / (rss_unrestricted / (n - kz))
    )
