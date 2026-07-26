"""Set-identified schemes and the sampler over the identified set.

Port of ``SignRestrictions.m``. Draws orthonormal rotations of the Cholesky
factor until one satisfies a sign pattern.

Which module a scheme lives in
------------------------------
This module holds the **set-identified** schemes — sign restrictions, narrative
sign restrictions, and sign restrictions combined with an instrument. Their
assumptions admit a whole family of admissible impact matrices rather than one,
so the answer is a *distribution*: ``sign_restricted_irf`` samples the set and
reports percentile bands across accepted draws. ``ident.py`` holds the
**point-identified** schemes, where the assumptions pin down a single ``B0inv``
and ``impact_matrix`` can return it. That is the whole rule, and it is why
``impact_matrix(model, "sign")`` raises and redirects here: the scheme is
implemented, but not as a function returning one matrix.

Every draw is a full square ``B0inv``, since the narrative check and the
historical decomposition both need to invert it. A plain sign draw is
``P @ Q`` with ``Q`` orthonormal, so it satisfies ``sigma == B @ B.T`` exactly.
The sign+IV path is the exception: it restores the instrument-identified column
0 on top of the rotation, so the identity need not hold — for the same reason,
and under the same condition, as ``ident._complete``: the restored column is
only approximately unit-norm in the Cholesky basis when the instrument is
observed on a shorter sample than ``sigma``.

Restrictions are given as an ``(nvar, nshock)`` array of ``+1`` (response must be
non-negative), ``-1`` (non-positive), and ``0`` (unrestricted). Restrictions can
be imposed on impact only (``sr_hor=1``) or over the first ``sr_hor`` horizons.

Deliberately not accelerated: a JAX backend for the rotations was implemented,
measured, and removed. See ``docs/roadmap.md`` ticket 07 for the numbers.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ._linalg import cholesky, orthonormal_completion
from .ident import proxy_iv
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


def _match(
    candidate: np.ndarray, restrictions: np.ndarray, start: int = 0
) -> np.ndarray | None:
    """Greedily assign candidate columns to shocks, flipping signs as needed.

    ``candidate`` is ``(nvar, nvar)`` when restrictions apply on impact only, or
    ``(nvar, nvar, nhor)`` when they apply over horizons. Returns the reordered
    and sign-corrected impact matrix, or ``None`` if any shock is unmatchable.

    Greedy first-match rather than an exhaustive assignment search: this mirrors
    upstream, and since the rotation is redrawn on failure the sampler still
    covers the identified set.
    """
    nvar, nshock = restrictions.shape
    # Columns before `start` are already identified (by an instrument) and are
    # held fixed rather than offered to the matcher.
    available = list(range(start, nvar))
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
    b_iv: np.ndarray | None = None,
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
    start = 0 if b_iv is None else 1
    if restrictions.shape[1] > nvar - start:
        raise ValueError(
            "cannot restrict more shocks than there are free columns "
            f"({nvar - start} available, {restrictions.shape[1]} restricted)"
        )
    if not np.isin(restrictions, (-1.0, 0.0, 1.0)).all():
        raise ValueError("restrictions must contain only -1, 0 and +1")

    P = cholesky(model.sigma)
    psi = model.wold(sr_hor - 1) if sr_hor > 1 else None

    # One rotation at a time, deliberately. Batching was tried, together with a
    # JAX backend for the batch; see docs/roadmap.md ticket 07. Typical
    # acceptance rates are high enough that a batch is mostly wasted work, and
    # the rotations are small QR decompositions where numpy beats JAX's dispatch
    # overhead by a wide margin.
    if b_iv is not None:
        # Express the instrument-identified impact in the Cholesky basis and
        # complete it to an orthonormal basis. Only the orthogonal complement is
        # then rotated, so column 0 survives every draw unchanged.
        q1 = np.linalg.solve(P, np.asarray(b_iv, dtype=float).ravel())
        Q0 = orthonormal_completion(q1 / np.linalg.norm(q1), nvar)

    for ntried in range(1, max_rot + 1):
        if b_iv is None:
            B = P @ haar_rotation(nvar, rng)
        else:
            rot = np.eye(nvar)
            rot[1:, 1:] = haar_rotation(nvar - 1, rng)
            B = P @ Q0 @ rot
            B[:, 0] = b_iv  # restore the IV impact exactly

        if psi is None:
            candidate = B
        else:
            # (nvar, nshock, nhor): every restricted horizon must comply.
            candidate = np.transpose(psi @ B, (1, 2, 0))
        matched = _match(candidate, restrictions, start)
        if matched is not None:
            order, flip = matched
            # Always return a full square matrix: pre-identified columns first,
            # then the restricted shocks, then whatever columns the restrictions
            # did not name. Truncating to the restricted shocks would leave B
            # singular, and the narrative check and historical decomposition both
            # need to invert it.
            used = set(order.tolist()) | set(range(start))
            rest = [c for c in range(nvar) if c not in used]
            cols = np.concatenate([np.arange(start), order, rest]).astype(int)
            flips = np.concatenate([np.ones(start), flip, np.ones(len(rest))])
            return B[:, cols] * flips, ntried
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
    iv: np.ndarray | None = None,
    max_reject: int = 200,
) -> SignRestrictedIRF:
    """Impulse responses over the sign-identified set.

    Parameters
    ----------
    ndraws : int
        Number of accepted rotations to collect. Sampling continues until this
        many draws pass every filter, not merely until this many are attempted.
    sr_hor : int
        Number of horizons over which restrictions must hold, counting impact.
    max_rot : int
        Rotations attempted per draw before giving up on that draw.
    max_reject : int
        Attempts allowed per requested draw before giving up entirely. Guards
        against an infeasible specification looping forever; raise it when a
        narrative filter has a very low acceptance rate.
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
    iv : array (nobs,), optional
        External instrument. Combines the two schemes as upstream's
        ``ident="sign+iv"`` does: shock 0 is identified by the instrument and
        held fixed across rotations, and the sign pattern identifies the
        remaining shocks within its orthogonal complement. ``restrictions`` then
        has at most ``nvar - 1`` columns, describing those remaining shocks.
    """
    if not 0.0 < ci < 1.0:
        raise ValueError(f"ci must be in (0, 1), got {ci}")

    rng = np.random.default_rng(seed)
    psi_fixed = None if posterior else model.wold(horizon)

    # Keep going until `ndraws` rotations are actually accepted, as upstream's
    # SR.m does. Attempting exactly ndraws times instead would silently return
    # far fewer under a narrative filter, whose acceptance rate can be a few
    # percent. The cap stops an infeasible specification from looping forever.
    max_attempts = max(ndraws * max_reject, ndraws)
    accepted, attempted = [], 0
    sign_ok = 0
    tries = 0
    while len(accepted) < ndraws and tries < max_attempts:
        tries += 1
        if posterior:
            drawn = draw_posterior(model, rng)
            psi = drawn.wold(horizon)
        else:
            drawn, psi = model, psi_fixed
        b_iv = None
        if iv is not None:
            b_iv = proxy_iv(drawn, iv)[:, 0]
        B, ntried = draw_rotation(
            drawn, restrictions, rng, sr_hor, max_rot, b_iv=b_iv
        )
        attempted += ntried
        if B is None:
            continue
        sign_ok += 1
        if narrative and not _narrative_holds(
            B, drawn.resid, drawn.nlags, narrative
        ):
            continue
        accepted.append(psi @ B)

    if len(accepted) < ndraws and len(accepted) >= 2:
        import warnings

        warnings.warn(
            f"collected {len(accepted)} of {ndraws} requested draws after "
            f"{tries} attempts; raise max_reject for tighter restrictions",
            RuntimeWarning,
            stacklevel=2,
        )

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
