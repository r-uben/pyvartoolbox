"""Reduced-form VAR estimation by OLS (port of ``VARmodel.m``)."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from ._lag import DET_CONST, make_xy


@dataclass
class VARmodel:
    """A reduced-form VAR(p) estimated equation-by-equation with OLS.

    Because every equation shares the same regressors, equation-by-equation OLS
    is the system's GLS estimator, so a single least-squares solve suffices.

    Parameters
    ----------
    y : array (nobs, nvar)
        Endogenous series in columns, ordered as you want them ordered for a
        recursive identification.
    nlags : int
        Lag order.
    det : int
        Deterministic terms: 0 none, 1 constant, 2 constant+trend,
        3 constant+trend+trend^2.
    exog : array (nobs, nexog), optional
        Exogenous regressors, entering contemporaneously.
    dof_adjust : bool
        Divide the residual covariance by ``neff - ncoef`` rather than ``neff``.
    """

    y: np.ndarray
    nlags: int
    det: int = DET_CONST
    exog: np.ndarray | None = None
    dof_adjust: bool = True

    # Filled by __post_init__.
    beta: np.ndarray = field(init=False)
    resid: np.ndarray = field(init=False)
    sigma: np.ndarray = field(init=False)
    Y: np.ndarray = field(init=False)
    X: np.ndarray = field(init=False)
    det_names: list[str] = field(init=False)

    def __post_init__(self) -> None:
        self.y = np.asarray(self.y, dtype=float)
        if self.y.ndim == 1:
            self.y = self.y[:, None]

        self.Y, self.X, self.det_names = make_xy(
            self.y, self.nlags, self.det, self.exog
        )

        neff, ncoef = self.X.shape
        if neff <= ncoef:
            raise ValueError(
                f"{neff} usable observations for {ncoef} coefficients per equation; "
                "reduce nlags or lengthen the sample"
            )

        # lstsq rather than a normal-equations solve: VAR regressors are highly
        # collinear by construction, and squaring the condition number matters.
        self.beta, *_ = np.linalg.lstsq(self.X, self.Y, rcond=None)
        self.resid = self.Y - self.X @ self.beta
        denom = neff - ncoef if self.dof_adjust else neff
        self.sigma = (self.resid.T @ self.resid) / denom

    @property
    def nvar(self) -> int:
        return self.y.shape[1]

    @property
    def neff(self) -> int:
        """Observations actually used in estimation."""
        return self.Y.shape[0]

    @property
    def ncoef(self) -> int:
        """Coefficients per equation."""
        return self.X.shape[1]

    @property
    def ar_coefs(self) -> np.ndarray:
        """Autoregressive matrices as an ``(nlags, nvar, nvar)`` array.

        ``ar_coefs[j]`` is ``A_{j+1}`` in ``y_t = sum_j A_j y_{t-j} + ...``.
        """
        k, p = self.nvar, self.nlags
        # beta rows are stacked [y_{t-1} block; y_{t-2} block; ...]; each block is
        # (nvar, nvar) with regressors on rows, so transpose to get A_j.
        return self.beta[: k * p].reshape(p, k, k).transpose(0, 2, 1)

    @property
    def det_coefs(self) -> np.ndarray:
        """Coefficients on exogenous and deterministic terms, ``(nvar, nextra)``."""
        return self.beta[self.nvar * self.nlags :].T

    def companion(self) -> np.ndarray:
        """Companion matrix ``F`` of the VAR(1) representation, ``(k*p, k*p)``."""
        k, p = self.nvar, self.nlags
        F = np.zeros((k * p, k * p))
        F[:k] = np.hstack(list(self.ar_coefs))
        if p > 1:
            F[k:, : k * (p - 1)] = np.eye(k * (p - 1))
        return F

    def max_eig(self) -> float:
        """Largest eigenvalue modulus of the companion matrix.

        ``< 1`` means the estimated VAR is stable.
        """
        return float(np.max(np.abs(np.linalg.eigvals(self.companion()))))

    def is_stable(self, tol: float = 1e-10) -> bool:
        return self.max_eig() < 1.0 - tol

    def wold(self, horizon: int) -> np.ndarray:
        """Reduced-form Wold/MA coefficients ``Psi_0 .. Psi_horizon``.

        Returns ``(horizon + 1, nvar, nvar)`` with ``Psi_0 = I``. Computed by the
        recursion ``Psi_h = sum_{j=1}^{min(h,p)} A_j Psi_{h-j}`` rather than by
        powering the companion matrix, which is both cheaper and better behaved
        numerically at long horizons.
        """
        if horizon < 0:
            raise ValueError(f"horizon must be >= 0, got {horizon}")
        k, p = self.nvar, self.nlags
        A = self.ar_coefs
        psi = np.zeros((horizon + 1, k, k))
        psi[0] = np.eye(k)
        for h in range(1, horizon + 1):
            for j in range(1, min(h, p) + 1):
                psi[h] += A[j - 1] @ psi[h - j]
        return psi

    def irf(self, horizon: int = 40, ident: str = "chol") -> np.ndarray:
        """Structural impulse responses, ``(horizon + 1, nvar, nshock)``.

        ``irf[h, i, j]`` is the response of variable ``i`` at horizon ``h`` to a
        one-standard-deviation structural shock ``j``. See :mod:`pyvartoolbox.ident`
        for the available ``ident`` schemes.
        """
        from .ident import impact_matrix

        B0inv = impact_matrix(self, ident)
        return self.wold(horizon) @ B0inv

    def vd(self, horizon: int = 40, ident: str = "chol") -> np.ndarray:
        """Forecast error variance decomposition, ``(horizon + 1, nvar, nshock)``.

        Entries are shares in ``[0, 1]`` summing to one across shocks for each
        variable and horizon.
        """
        theta = self.irf(horizon, ident)
        contrib = np.cumsum(theta**2, axis=0)
        total = contrib.sum(axis=2, keepdims=True)
        return contrib / total

    def simulate(
        self, resid: np.ndarray, y0: np.ndarray, X_extra: np.ndarray | None = None
    ) -> np.ndarray:
        """Recursively regenerate a series from residuals and initial conditions.

        ``y0`` supplies the ``nlags`` presample rows. ``X_extra`` is the block of
        exogenous/deterministic regressors for the ``neff`` simulated periods,
        defaulting to the estimation sample's own. Used by the bootstrap.
        """
        k, p = self.nvar, self.nlags
        if y0.shape != (p, k):
            raise ValueError(f"y0 must have shape {(p, k)}, got {y0.shape}")
        if X_extra is None:
            X_extra = self.X[:, k * p :]

        neff = resid.shape[0]
        A = self.ar_coefs
        d = self.det_coefs
        out = np.empty((p + neff, k))
        out[:p] = y0
        for t in range(neff):
            val = resid[t].copy()
            for j in range(1, p + 1):
                val += A[j - 1] @ out[p + t - j]
            if d.size:
                val += d @ X_extra[t]
            out[p + t] = val
        return out
