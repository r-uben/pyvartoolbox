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

SCHEMES = ("chol", "longrun", "iv")

#: Schemes that identify only the first structural shock. The remaining columns
#: of ``B0inv`` are a numerical completion with no economic content, so IRFs and
#: variance decompositions for those shocks are zeroed before being returned.
PARTIAL = frozenset({"iv"})

_PLANNED = {
    "sign": "sign restrictions",
    "narrative": "narrative sign restrictions",
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


def _ols(y: np.ndarray, x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """OLS of ``y`` on ``[1, x]``. Returns ``(coefs, fitted)``, constant first."""
    X = np.column_stack([np.ones(len(x)), x])
    coefs, *_ = np.linalg.lstsq(X, y, rcond=None)
    return coefs, X @ coefs


def _complete(b1: np.ndarray, sigma: np.ndarray) -> np.ndarray:
    """Complete an identified first column to a full invertible ``B0inv``.

    Columns 2 onward are an orthonormal completion in the Cholesky basis. They
    carry no economic content and exist only so that ``B0inv`` is invertible —
    the historical decomposition needs ``eps = B0inv \\ u``.

    The identified column is restored exactly at the end. That deliberately
    breaks ``B0inv @ B0inv.T == sigma``, since the IV impact is estimated on a
    different sample than ``sigma`` and so is only approximately unit-norm in
    the Cholesky basis. Exact shock-1 impulse responses are the thing worth
    preserving; the covariance identity over meaningless columns is not.
    Upstream's ``complete_B`` makes the same trade.
    """
    nvar = sigma.shape[0]
    P = _cholesky(sigma)
    q1 = np.linalg.solve(P, b1)
    # b1 comes from the IV sample while sigma comes from the VAR sample, so the
    # norm is only approximately one; normalise before completing.
    q1 = q1 / np.linalg.norm(q1)
    Q, _ = np.linalg.qr(np.column_stack([q1, np.eye(nvar)]))
    if Q[:, 0] @ q1 < 0:
        Q[:, 0] = -Q[:, 0]
    B = P @ Q
    B[:, 0] = b1
    return B


def proxy_iv(model, iv: np.ndarray) -> np.ndarray:
    """External-instrument (proxy SVAR) identification.

    The instrument identifies the shock to the **first** variable in ``y``, so
    ordering matters even though the scheme is not recursive. Follows the
    two-stage construction of Gertler and Karadi (2015): project the first
    reduced-form residual on the instrument, regress the remaining residuals on
    the fitted values to get impact ratios, then scale by the shock standard
    deviation implied by their footnote-4 correction.

    ``iv`` is aligned on the *full* sample of ``y``; its first ``nlags``
    observations are dropped to match the residual sample, and leading/trailing
    missing rows are then trimmed.
    """
    iv = np.asarray(iv, dtype=float)
    if iv.ndim == 1:
        iv = iv[:, None]
    if iv.shape[0] != model.y.shape[0]:
        raise ValueError(
            f"iv has {iv.shape[0]} rows but y has {model.y.shape[0]}; the "
            "instrument must be aligned on the full sample, missing values "
            "included as NaN"
        )

    up = model.resid[:, 0]
    uq = model.resid[:, 1:]
    z = iv[model.nlags :]

    keep = ~np.isnan(np.column_stack([up, z])).any(axis=1)
    if not keep.any():
        raise ValueError("instrument and VAR residuals share no overlapping sample")
    idx = np.flatnonzero(keep)
    if not np.all(np.diff(idx) == 1):
        raise ValueError(
            "instrument has interior missing values; only leading and trailing "
            "gaps are supported, since the two-stage regression needs a "
            "contiguous overlap"
        )

    p = up[idx]
    q = uq[idx]
    Z = z[idx]

    first_coefs, p_hat = _ols(p, Z)
    ratios = np.array([_ols(q[:, i], p_hat)[0][1] for i in range(q.shape[1])])

    # Shock-size normalisation (Gertler and Karadi 2015, footnote 4). The
    # covariance is taken on the IV subsample, which is why it is not model.sigma.
    pq = np.column_stack([p, q])
    centred = pq - pq.mean(axis=0)
    sigma_b = centred.T @ centred / (len(pq) - model.ncoef)

    S11 = sigma_b[0, 0]
    S21 = sigma_b[1:, 0]
    S22 = sigma_b[1:, 1:]
    r = ratios
    Q_mat = np.outer(r, r) * S11 - (np.outer(S21, r) + np.outer(r, S21)) + S22
    d = S21 - r * S11
    sp = np.sqrt(S11 - d @ np.linalg.solve(Q_mat, d))

    b1 = np.concatenate([[1.0], ratios]) * sp * np.sign(first_coefs[1])
    return _complete(b1, model.sigma)


_DISPATCH = {"chol": chol, "longrun": longrun, "iv": proxy_iv}


def impact_matrix(model, ident: str = "chol", **kwargs) -> np.ndarray:
    """Return ``B0inv`` for the requested identification scheme.

    Extra keyword arguments are passed to the scheme: ``iv=`` is required by
    ``ident="iv"``.
    """
    if ident in _DISPATCH:
        try:
            return _DISPATCH[ident](model, **kwargs)
        except TypeError as exc:
            if "iv" in str(exc) or "argument" in str(exc):
                raise TypeError(
                    f"identification scheme {ident!r} was given the wrong "
                    f"arguments: {exc}"
                ) from exc
            raise
    if ident in _PLANNED:
        raise NotImplementedError(
            f"identification scheme {ident!r} ({_PLANNED[ident]}) is on the "
            f"roadmap but not implemented yet; available now: {SCHEMES}"
        )
    raise ValueError(
        f"unknown identification scheme {ident!r}; expected one of {SCHEMES}"
    )
