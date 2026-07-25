"""Bootstrap confidence bands for impulse responses.

Two resampling schemes, both regenerating the series recursively from the
estimated VAR and then re-estimating on each artificial sample:

``"resid"``
    iid resampling of the reduced-form residual *rows*, preserving the
    contemporaneous correlation across equations.
``"wild"``
    Rademacher wild bootstrap: each residual row is multiplied by +1 or -1 with
    equal probability. Robust to conditional heteroskedasticity, which is the
    usual reason to prefer it on monthly financial data.

Bands are percentile bands over the bootstrap distribution. No bias correction
is applied; see ``docs/roadmap.md``.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .model import VARmodel

METHODS = ("resid", "wild")


@dataclass
class BootstrapIRF:
    """Point estimate and percentile bands, all ``(horizon+1, nvar, nshock)``.

    ``draws`` is ``(nkept, horizon+1, nvar, nshock)``.
    """

    irf: np.ndarray
    lower: np.ndarray
    upper: np.ndarray
    draws: np.ndarray
    ci: float
    ndiscarded: int

    @property
    def median(self) -> np.ndarray:
        return np.median(self.draws, axis=0)


def _resample(
    resid: np.ndarray, method: str, rng: np.random.Generator
) -> np.ndarray:
    neff = resid.shape[0]
    if method == "resid":
        return resid[rng.integers(0, neff, size=neff)]
    if method == "wild":
        return resid * rng.choice([-1.0, 1.0], size=(neff, 1))
    raise ValueError(f"unknown bootstrap method {method!r}; expected one of {METHODS}")


def bootstrap_irf(
    model: VARmodel,
    horizon: int = 40,
    ident: str = "chol",
    nboot: int = 1000,
    method: str = "resid",
    ci: float = 0.90,
    seed: int | None = None,
    drop_unstable: bool = True,
) -> BootstrapIRF:
    """Percentile bootstrap bands around ``model.irf(horizon, ident)``.

    Parameters
    ----------
    nboot : int
        Number of bootstrap replications.
    ci : float
        Central coverage, e.g. ``0.90`` for 5th-95th percentile bands.
    drop_unstable : bool
        Discard replications whose re-estimated companion matrix has a root
        outside the unit circle. Such draws produce explosive IRFs that dominate
        the percentiles at long horizons. The count is reported in
        ``ndiscarded``; a large value means the point estimate sits close to the
        stability boundary and the bands should not be trusted.

    Notes
    -----
    Cost is ``nboot`` independent re-estimations. This loop, together with the
    rejection sampling used by sign restrictions, is what the planned JAX
    backend is for; the numpy path is deliberately kept as the reference
    implementation.
    """
    if not 0.0 < ci < 1.0:
        raise ValueError(f"ci must be in (0, 1), got {ci}")
    if nboot < 2:
        raise ValueError(f"nboot must be >= 2, got {nboot}")

    rng = np.random.default_rng(seed)
    point = model.irf(horizon, ident)
    y0 = model.y[: model.nlags]

    draws = []
    ndiscarded = 0
    for _ in range(nboot):
        y_star = model.simulate(_resample(model.resid, method, rng), y0)
        boot = VARmodel(
            y_star,
            model.nlags,
            det=model.det,
            exog=model.exog,
            dof_adjust=model.dof_adjust,
        )
        if drop_unstable and not boot.is_stable():
            ndiscarded += 1
            continue
        try:
            draws.append(boot.irf(horizon, ident))
        except np.linalg.LinAlgError:
            # A singular draw is uninformative, not fatal; count and move on.
            ndiscarded += 1

    if len(draws) < 2:
        raise RuntimeError(
            f"only {len(draws)} of {nboot} bootstrap replications were usable; "
            "the estimated VAR is probably explosive or near-singular"
        )

    stacked = np.stack(draws)
    tail = 100 * (1 - ci) / 2
    lower, upper = np.percentile(stacked, [tail, 100 - tail], axis=0)
    return BootstrapIRF(
        irf=point,
        lower=lower,
        upper=upper,
        draws=stacked,
        ci=ci,
        ndiscarded=ndiscarded,
    )
