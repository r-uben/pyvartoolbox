"""Structural identification: mapping reduced-form residuals to shocks.

Every scheme returns ``B0inv``, the ``(nvar, nvar)`` impact matrix satisfying
``sigma = B0inv @ B0inv.T``. Structural IRFs are then ``Psi_h @ B0inv``.

Implemented
-----------
``"chol"``
    Zero contemporaneous restrictions. Recursive ordering given by the column
    order of ``y``; the Cholesky factor is lower triangular.
``"longrun"``
    Zero long-run restrictions in the manner of Blanchard and Quah (1989). The
    cumulative effect of shock ``j`` on variable ``i`` is zero for ``i < j``.

Not yet implemented
-------------------
Sign restrictions, narrative sign restrictions, external instruments
(proxy SVAR), instruments combined with sign restrictions, and exogenous
variable identification. See ``docs/roadmap.md``; these are the schemes that
motivate the port, since ``statsmodels`` covers neither proxy SVARs nor
narrative restrictions.
"""

from __future__ import annotations

import numpy as np

SCHEMES = ("chol", "longrun")

_PLANNED = {
    "sign": "sign restrictions",
    "narrative": "narrative sign restrictions",
    "iv": "external instruments (proxy SVAR)",
    "signiv": "external instruments combined with sign restrictions",
    "exog": "exogenous variable identification",
}


def _cholesky(sigma: np.ndarray) -> np.ndarray:
    """Lower-triangular Cholesky factor, with a readable failure mode."""
    try:
        return np.linalg.cholesky(sigma)
    except np.linalg.LinAlgError as exc:
        raise np.linalg.LinAlgError(
            "residual covariance is not positive definite; the VAR is likely "
            "over-parameterised (too many lags for the sample) or contains a "
            "linearly dependent series"
        ) from exc


def chol(model) -> np.ndarray:
    """Zero contemporaneous restrictions."""
    return _cholesky(model.sigma)


def longrun(model) -> np.ndarray:
    """Zero long-run restrictions (Blanchard-Quah).

    The long-run multiplier of the reduced form is ``C1 = (I - sum_j A_j)^-1``.
    Requiring the *cumulative* structural response to be lower triangular gives
    ``C1 @ B0inv = chol(C1 @ sigma @ C1.T)``.

    The series are expected to be entered in the form the restriction applies to
    (typically first differences), so that "long run" means the cumulated
    response.
    """
    k = model.nvar
    A_sum = model.ar_coefs.sum(axis=0)
    lr = np.eye(k) - A_sum
    if np.linalg.matrix_rank(lr) < k:
        raise np.linalg.LinAlgError(
            "I - sum(A_j) is singular: the VAR has a unit root, so long-run "
            "restrictions are not identified. Difference the data first."
        )
    C1 = np.linalg.inv(lr)
    return np.linalg.solve(C1, _cholesky(C1 @ model.sigma @ C1.T))


_DISPATCH = {"chol": chol, "longrun": longrun}


def impact_matrix(model, ident: str = "chol") -> np.ndarray:
    """Return ``B0inv`` for the requested identification scheme."""
    if ident in _DISPATCH:
        return _DISPATCH[ident](model)
    if ident in _PLANNED:
        raise NotImplementedError(
            f"identification scheme {ident!r} ({_PLANNED[ident]}) is on the "
            f"roadmap but not implemented yet; available now: {SCHEMES}"
        )
    raise ValueError(
        f"unknown identification scheme {ident!r}; expected one of {SCHEMES}"
    )
