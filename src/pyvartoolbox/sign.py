"""Sign-restriction identification (port of ``SignRestrictions.m``).

Draws orthonormal rotations of the Cholesky factor until one satisfies a sign
pattern. Unlike the other schemes this is a *set* identification: there is no
single answer, only a distribution over admissible impact matrices.

Restrictions are given as an ``(nvar, nshock)`` array of ``+1`` (response must be
non-negative), ``-1`` (non-positive), and ``0`` (unrestricted). Restrictions can
be imposed on impact only (``sr_hor=1``) or over the first ``sr_hor`` horizons.

Deliberately not accelerated: a JAX backend for the rotations was implemented,
measured, and removed. See ``docs/roadmap.md`` ticket 07 for the numbers.
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

    # One rotation at a time, deliberately. Batching was tried, together with a
    # JAX backend for the batch; see docs/roadmap.md ticket 07. Typical
    # acceptance rates are high enough that a batch is mostly wasted work, and
    # the rotations are small QR decompositions where numpy beats JAX's dispatch
    # overhead by a wide margin.
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
    narrative: list | None = None,
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
    narrative : list of NarrativeSign or NarrativeDominance, optional
        Narrative sign restrictions in the manner of Antolin-Diaz and
        Rubio-Ramirez (2018): constraints on the structural shocks at specific
        dates, applied on top of the sign pattern.

        Note that upstream — and therefore this port — applies these as a
        *rejection* filter: a draw violating any narrative constraint is
        discarded. The original paper instead reweights accepted draws by an
        importance weight. The two agree on the support of the posterior but not
        on its shape, so results here will not exactly reproduce the paper's.
    """
    if not 0.0 < ci < 1.0:
        raise ValueError(f"ci must be in (0, 1), got {ci}")

    rng = np.random.default_rng(seed)
    psi_fixed = None if posterior else model.wold(horizon)

    accepted, attempted = [], 0
    sign_ok = 0
    for _ in range(ndraws):
        if posterior:
            drawn = draw_posterior(model, rng)
            psi = drawn.wold(horizon)
        else:
            drawn, psi = model, psi_fixed
        B, ntried = draw_rotation(drawn, restrictions, rng, sr_hor, max_rot)
        attempted += ntried
        if B is None:
            continue
        sign_ok += 1
        if narrative and not _narrative_holds(
            B, drawn.resid, drawn.nlags, narrative
        ):
            continue
        accepted.append(psi @ B)

    if len(accepted) < 2:
        # Distinguish the two very different failure modes, because the fix is
        # different: an infeasible sign pattern versus narrative constraints
        # that no admissible rotation happens to satisfy.
        if sign_ok < 2:
            raise RuntimeError(
                f"only {sign_ok} of {ndraws} draws found a rotation satisfying "
                "the sign pattern; it is likely infeasible for this data, or "
                "max_rot is too small"
            )
        raise RuntimeError(
            f"{sign_ok} of {ndraws} draws satisfied the sign pattern but only "
            f"{len(accepted)} also satisfied the narrative constraints; the "
            "narrative restrictions are likely inconsistent with the sign "
            "pattern on this sample"
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


@dataclass
class NarrativeSign:
    """The structural shock ``shock`` at ``period`` must have sign ``sign``.

    ``period`` indexes the original sample, not the residual sample; the lag
    trim is applied internally.
    """

    period: int
    shock: int
    sign: int


@dataclass
class NarrativeDominance:
    """Shock ``shock`` must be the dominant driver of ``variable`` at ``period``.

    "Dominant" in the Antolin-Diaz and Rubio-Ramirez (2018) sense: the absolute
    contribution of this shock exceeds the summed absolute contributions of all
    the others.
    """

    period: int
    shock: int
    variable: int


def _narrative_holds(B, resid, nlags, narrative) -> bool:
    """Check narrative constraints against the structural shocks implied by B."""
    eps = np.linalg.solve(B, resid.T).T  # (neff, nshock)

    for r in narrative:
        t = r.period - nlags
        if not 0 <= t < eps.shape[0]:
            raise IndexError(
                f"narrative period {r.period} falls outside the estimation "
                f"sample, which starts at observation {nlags}"
            )
        if isinstance(r, NarrativeSign):
            if r.sign * eps[t, r.shock] <= 0:
                return False
        else:
            contrib = np.abs(B[r.variable, :] * eps[t, :])
            if contrib[r.shock] <= contrib.sum() - contrib[r.shock]:
                return False
    return True
