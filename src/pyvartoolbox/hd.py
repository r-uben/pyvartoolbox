"""Historical decomposition (port of ``compute_HD.m``).

Splits each observed series into the cumulated contribution of every structural
shock plus the contributions of the initial condition and the deterministic
terms. The components sum back to the data exactly, which is the property the
tests assert.

All components are padded with ``NaN`` over the first ``nlags`` periods, which
have no decomposition because they are the presample.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class HistoricalDecomposition:
    """Components of a historical decomposition, all aligned on the full sample.

    ``shock`` is ``(nobs, nvar, nshock)``; the rest are ``(nobs, nvar)``.
    ``shock[t, i, j]`` is the contribution of structural shock ``j`` to variable
    ``i`` at time ``t``.
    """

    shock: np.ndarray
    init: np.ndarray
    const: np.ndarray
    trend: np.ndarray
    total: np.ndarray

    @property
    def deterministic(self) -> np.ndarray:
        """Constant plus trend, the usual way these are reported together."""
        return self.const + self.trend

    def check(self, y: np.ndarray, atol: float = 1e-8) -> bool:
        """True if the components reproduce ``y`` over the decomposed sample."""
        rebuilt = self.total
        mask = ~np.isnan(rebuilt).any(axis=1)
        return bool(np.allclose(rebuilt[mask], np.asarray(y)[mask], atol=atol))


def compute_hd(model, ident: str = "chol", **kwargs) -> HistoricalDecomposition:
    """Decompose the sample into structural-shock and deterministic components.

    Requires an invertible impact matrix, since the structural shocks are backed
    out as ``eps = B0inv \\ u``. Partially identifying schemes such as
    ``ident="iv"`` therefore use the numerical completion, and only the
    identified shock's contribution is interpretable.
    """
    from .ident import impact_matrix

    B = impact_matrix(model, ident, **kwargs)
    k, p = model.nvar, model.nlags
    kp = k * p
    neff = model.neff
    nobs = model.y.shape[0]

    F = model.companion()
    eps = np.linalg.solve(B, model.resid.T)  # (nshock, neff)

    B_big = np.zeros((kp, k))
    B_big[:k] = B

    # Contribution of each shock, accumulated through the companion recursion.
    shock = np.full((nobs, k, k), np.nan)
    for j in range(k):
        state = np.zeros(kp)
        for t in range(neff):
            forcing = np.zeros(k)
            forcing[j] = eps[j, t]
            state = B_big @ forcing + F @ state
            shock[p + t, :, j] = state[:k]

    # Initial condition: the presample state propagated forward with no forcing.
    # One fewer NaN row than the other components, because the state at t=0 is
    # aligned to the last presample period rather than to a decomposed period.
    init = np.full((nobs, k), np.nan)
    state = model.X[0, :kp].copy()
    init[p - 1] = state[:k]
    for t in range(neff):
        state = F @ state
        init[p + t] = state[:k]

    det = dict(zip(model.det_names, model.det_coefs.T, strict=True))

    def _propagate(forcing_at: callable) -> np.ndarray:
        out = np.full((nobs, k), np.nan)
        state = np.zeros(kp)
        for t in range(neff):
            f = np.zeros(kp)
            f[:k] = forcing_at(t)
            state = f + F @ state
            out[p + t] = state[:k]
        return out

    zeros = np.full((nobs, k), np.nan)
    zeros[p:] = 0.0

    if "const" in det:
        const = _propagate(lambda t: det["const"])
    else:
        const = zeros.copy()

    if "trend" in det:
        # Trend forcing grows with the period index, matching the trend column
        # built in _lag.make_xy (which starts at 1 on the estimation sample).
        trend = _propagate(lambda t: det["trend"] * (t + 1))
    else:
        trend = zeros.copy()

    total = np.full((nobs, k), np.nan)
    total[p:] = (
        np.nansum(shock[p:], axis=2) + init[p:] + const[p:] + trend[p:]
    )

    return HistoricalDecomposition(
        shock=shock, init=init, const=const, trend=trend, total=total
    )
