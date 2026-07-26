"""Point-identified structural schemes, and the ``impact_matrix`` dispatcher.

Which module a scheme lives in
------------------------------
The split between this module and ``sign.py`` is point identification versus set
identification, and nothing else:

* **Point-identified** schemes — here. The assumptions pin down a *single*
  impact matrix, so a function can return one ``(nvar, nvar)`` array.
* **Set-identified** schemes — ``sign.py``. The assumptions admit a whole family
  of admissible impact matrices, so the answer is a *distribution*, produced by
  sampling the identified set with ``sign_restricted_irf``.

That is the distinction a user has to grasp before anything else in the package
makes sense, so it is also the one the file layout encodes. It is not a split by
source paper, by computational cost, or by how recently a scheme was added.

``impact_matrix`` dispatches over this module alone, because its contract is to
return one ``B0inv``, and a set-identified scheme has none to return. Asking it
for ``"sign"`` therefore raises and points at ``sign_restricted_irf`` — the
scheme is implemented, just not through a function of this shape.

Every scheme here returns ``B0inv``, the ``(nvar, nvar)`` impact matrix, and
structural IRFs are ``Psi_h @ B0inv``. ``chol`` and ``longrun`` satisfy
``sigma == B0inv @ B0inv.T`` exactly. ``iv`` need not: it restores the
instrument-identified column on top of a numerical completion, and that column
is only approximately unit-norm in the Cholesky basis whenever the instrument is
observed on a shorter sample than ``sigma``. When the instrument spans the full
VAR sample the identity happens to hold to machine precision; when it does not,
the gap is real and is accepted deliberately. See ``_complete``.

Implemented
-----------
``"chol"``
    Zero contemporaneous restrictions. Recursive ordering given by the column
    order of ``y``; the Cholesky factor is lower triangular.
``"longrun"``
    Zero long-run restrictions in the manner of Blanchard and Quah (1989). The
    cumulative effect of shock ``j`` on variable ``i`` is zero for ``i < j``.
``"iv"``
    External instruments (proxy SVAR). Point-identified but *partial*: only the
    first shock is identified. See ``PARTIAL``.

Not yet implemented
-------------------
Exogenous variable identification; see ``docs/roadmap.md``.
"""

from __future__ import annotations

import numpy as np

from ._linalg import cholesky, orthonormal_completion

SCHEMES = ("chol", "longrun", "iv")

#: Schemes that identify only the first structural shock. The remaining columns
#: of ``B0inv`` are a numerical completion with no economic content, so IRFs and
#: variance decompositions for those shocks are zeroed before being returned.
PARTIAL = frozenset({"iv"})

#: Set-identified schemes. These are implemented — in ``sign.py``, as samplers
#: over the identified set — but they have no single ``B0inv``, so they are
#: unreachable through ``impact_matrix`` by construction rather than by omission.
_SET_IDENTIFIED = {
    "sign": "sign restrictions",
    "narrative": "narrative sign restrictions",
    "signiv": "external instruments combined with sign restrictions",
}

#: Point-identified schemes that would belong here once written.
_PLANNED = {
    "exog": "exogenous variable identification",
}


def chol(model) -> np.ndarray:
    """Zero contemporaneous restrictions."""
    return cholesky(model.sigma)


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
    return np.linalg.solve(C1, cholesky(C1 @ model.sigma @ C1.T))


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
    P = cholesky(sigma)
    q1 = np.linalg.solve(P, b1)
    # b1 comes from the IV sample while sigma comes from the VAR sample, so the
    # norm is only approximately one; normalise before completing.
    q1 = q1 / np.linalg.norm(q1)
    B = P @ orthonormal_completion(q1, nvar)
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
    """Return ``B0inv`` for the requested point-identified scheme.

    Extra keyword arguments are passed to the scheme: ``iv=`` is required by
    ``ident="iv"``.

    Only point-identified schemes are reachable here. A set-identified scheme
    has no single ``B0inv`` to return, so naming one raises and points at
    ``sign_restricted_irf`` instead.
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
    if ident in _SET_IDENTIFIED:
        raise NotImplementedError(
            f"identification scheme {ident!r} ({_SET_IDENTIFIED[ident]}) is "
            "set-identified: it admits a family of admissible impact matrices "
            "rather than a single one, so there is no B for impact_matrix to "
            "return. The scheme itself is implemented — call "
            "sign_restricted_irf(model, restrictions, ...), which samples the "
            "identified set and returns a distribution of impulse responses. "
            f"impact_matrix covers the point-identified schemes only: {SCHEMES}"
        )
    if ident in _PLANNED:
        raise NotImplementedError(
            f"identification scheme {ident!r} ({_PLANNED[ident]}) is on the "
            f"roadmap but not implemented yet; available now: {SCHEMES}"
        )
    raise ValueError(
        f"unknown identification scheme {ident!r}; expected one of {SCHEMES}"
    )
