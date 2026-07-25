"""Sign-restriction identification (port of ``SignRestrictions.m``).

Draws orthonormal rotations of the Cholesky factor until one satisfies a sign
pattern. Unlike the other schemes this is a *set* identification: there is no
single answer, only a distribution over admissible impact matrices.

Restrictions are given as an ``(nvar, nshock)`` array of ``+1`` (response must be
non-negative), ``-1`` (non-positive), and ``0`` (unrestricted). Restrictions can
be imposed on impact only (``sr_hor=1``) or over the first ``sr_hor`` horizons.

Structured as fixed-size batched draws with an acceptance mask rather than an
early-exit loop, so that the planned JAX backend is a backend swap rather than a
rewrite. The matching step stays in Python because it is inherently sequential
per draw.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .ident import _cholesky
from .posterior import draw_posterior


@dataclass
class SignRestrictedIRF:
    """Distribution of impulse responses over accepted rotations.

    ``draws`` is ``(naccepted, horizon+1, nvar, nshock)``. Percentile bands are
    computed pointwise across draws.
    """

    draws: np.ndarray
    lower: np.ndarray
    median: np.ndarray
    upper: np.ndarray
    ci: float
    naccepted: int
    nattempted: int

    @property
    def acceptance_rate(self) -> float:
        return self.naccepted / self.nattempted if self.nattempted else 0.0


def haar_rotation(nvar: int, rng: np.random.Generator) -> np.ndarray:
    """Draw uniformly from the orthogonal group (Haar measure).

    QR of a Gaussian matrix, with the sign of each column fixed so that ``R`` has
    a non-negative diagonal. Without that normalisation the draw is not Haar —
    LAPACK's sign convention is arbitrary and would bias the sampler.
    """
    q, r = np.linalg.qr(rng.standard_normal((nvar, nvar)))
    return q * np.sign(np.diag(r))


def _match(candidate: np.ndarray, restrictions: np.ndarray) -> np.ndarray | None:
    """Greedily assign candidate columns to shocks, flipping signs as needed.

    ``candidate`` is ``(nvar, nvar)`` when restrictions apply on impact only, or
    ``(nvar, nvar, nhor)`` when they apply over horizons. Returns the reordered
    and sign-corrected impact matrix, or ``None`` if any shock is unmatchable.

    Greedy first-match rather than an exhaustive assignment search: this mirrors
    upstream, and since the rotation is redrawn on failure the sampler still
    covers the identified set.
    """
    nvar, nshock = restrictions.shape
    available = list(range(nvar))
    order = np.empty(nshock, dtype=int)
    flip = np.ones(nshock)

    for s in range(nshock):
        want = restrictions[:, s]
        for col in available:
            check = candidate[:, col]
            if check.ndim == 1:
                check = check[:, None]
            # A violation is a restricted element whose sign is wrong. Zeros in
            # `want` contribute nothing, which is what leaves them unrestricted.
            if not np.any(check * want[:, None] < 0):
                order[s], flip[s] = col, 1.0
                break
            if not np.any(-check * want[:, None] < 0):
                order[s], flip[s] = col, -1.0
                break
        else:
            return None
        available.remove(order[s])

    return order, flip


def draw_rotation(
    model,
    restrictions: np.ndarray,
    rng: np.random.Generator,
    sr_hor: int = 1,
    max_rot: int = 500,
) -> tuple[np.ndarray | None, int]:
    """Draw rotations until one satisfies ``restrictions``.

    Returns ``(B0inv, ntried)``; ``B0inv`` is ``None`` if ``max_rot`` rotations
    were exhausted without a match.
    """
    restrictions = np.asarray(restrictions, dtype=float)
    nvar = model.nvar
    if restrictions.shape[0] != nvar:
        raise ValueError(
            f"restrictions has {restrictions.shape[0]} rows but the VAR has "
            f"{nvar} variables"
        )
    if restrictions.shape[1] > nvar:
        raise ValueError("cannot restrict more shocks than there are variables")
    if not np.isin(restrictions, (-1.0, 0.0, 1.0)).all():
        raise ValueError("restrictions must contain only -1, 0 and +1")

    P = _cholesky(model.sigma)
    psi = model.wold(sr_hor - 1) if sr_hor > 1 else None

    for ntried in range(1, max_rot + 1):
        B = P @ haar_rotation(nvar, rng)
        if psi is None:
            candidate = B
        else:
            # (nvar, nshock, nhor): every restricted horizon must comply.
            candidate = np.transpose(psi @ B, (1, 2, 0))
        matched = _match(candidate, restrictions)
        if matched is not None:
            order, flip = matched
            return B[:, order] * flip, ntried
    return None, max_rot


def sign_restricted_irf(
    model,
    restrictions: np.ndarray,
    horizon: int = 40,
    ndraws: int = 1000,
    sr_hor: int = 1,
    max_rot: int = 500,
    ci: float = 0.90,
    seed: int | None = None,
    posterior: bool = True,
) -> SignRestrictedIRF:
    """Impulse responses over the sign-identified set.

    Parameters
    ----------
    ndraws : int
        Number of accepted rotations to collect.
    sr_hor : int
        Number of horizons over which restrictions must hold, counting impact.
    max_rot : int
        Rotations attempted per draw before giving up on that draw.
    posterior : bool
        If True (default), redraw the VAR coefficients from their flat-prior
        posterior before each rotation, as upstream's ``SR.m`` does. Bands then
        reflect parameter *and* identification uncertainty.

        Set False to hold the coefficients at their OLS estimates and vary only
        the rotation. The resulting bands describe the identified set alone and
        are **not** comparable to published sign-restriction figures — useful for
        seeing how much of the width is identification rather than estimation.
    """
    if not 0.0 < ci < 1.0:
        raise ValueError(f"ci must be in (0, 1), got {ci}")

    rng = np.random.default_rng(seed)
    psi_fixed = None if posterior else model.wold(horizon)

    accepted, attempted = [], 0
    for _ in range(ndraws):
        if posterior:
            drawn = draw_posterior(model, rng)
            psi = drawn.wold(horizon)
        else:
            drawn, psi = model, psi_fixed
        B, ntried = draw_rotation(drawn, restrictions, rng, sr_hor, max_rot)
        attempted += ntried
        if B is not None:
            accepted.append(psi @ B)

    if len(accepted) < 2:
        raise RuntimeError(
            f"only {len(accepted)} of {ndraws} draws found an admissible "
            "rotation; the sign pattern is likely infeasible for this data, or "
            "max_rot is too small"
        )

    draws = np.stack(accepted)
    tail = 100 * (1 - ci) / 2
    lower, median, upper = np.percentile(
        draws, [tail, 50, 100 - tail], axis=0
    )
    return SignRestrictedIRF(
        draws=draws,
        lower=lower,
        median=median,
        upper=upper,
        ci=ci,
        naccepted=len(accepted),
        nattempted=attempted,
    )
