"""Numerical primitives shared by the identification schemes.

Small by design: only the routines that more than one scheme needs, kept here so
that ``sign.py`` does not have to reach back into ``ident.py`` for them.
"""

from __future__ import annotations

import numpy as np


def cholesky(sigma: np.ndarray) -> np.ndarray:
    """Lower-triangular Cholesky factor, with a readable failure mode."""
    try:
        return np.linalg.cholesky(sigma)
    except np.linalg.LinAlgError as exc:
        raise np.linalg.LinAlgError(
            "residual covariance is not positive definite; the VAR is likely "
            "over-parameterised (too many lags for the sample) or contains a "
            "linearly dependent series"
        ) from exc


def orthonormal_completion(q1: np.ndarray, nvar: int) -> np.ndarray:
    """Orthonormal basis whose first column is ``q1`` (assumed unit norm).

    QR of ``[q1, I]`` gives the completion; the sign of the first column is then
    fixed to ``q1``'s own direction, since LAPACK's sign convention is arbitrary.
    """
    Q, _ = np.linalg.qr(np.column_stack([q1, np.eye(nvar)]))
    if Q[:, 0] @ q1 < 0:
        Q[:, 0] = -Q[:, 0]
    return Q
