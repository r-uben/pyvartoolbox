"""Uhlig (2005) and Antolin-Diaz & Rubio-Ramirez (2018) against MATLAB.

These two replications are rejection samplers, so they cannot be matched
draw-for-draw: the acceptance sequence depends on an RNG stream numpy cannot
reproduce. Claiming otherwise would be dishonest.

What *can* be checked exactly, and is what these tests do, is everything except
the random number generator. The fixtures hold the impact matrices MATLAB
actually accepted (generated with ``inference = 0``, so every rotation is taken
around the point estimate):

1. Our acceptance predicate accepts every matrix MATLAB accepted. A disagreement
   would mean the sign-checking or column-matching logic differs.
2. Our impulse responses computed from those same matrices reproduce MATLAB's.
3. Our reduced-form estimates match, so the rotations are being applied to the
   same covariance.

This is weaker than the 1e-10 agreement of the deterministic schemes, and is
labelled as such in the README. It is not a claim that the samplers produce
identical draws.
"""

from pathlib import Path

import numpy as np
import pytest

from pyvartoolbox import VARmodel
from pyvartoolbox.sign import _match, _narrative_holds

FIXTURES = Path(__file__).parent / "fixtures"

# Column 0 is the contractionary monetary policy shock; the other five are
# unrestricted, exactly as in both papers.
SIGN = np.array(
    [
        [0.0, 0, 0, 0, 0, 0],
        [-1.0, 0, 0, 0, 0, 0],
        [-1.0, 0, 0, 0, 0, 0],
        [0.0, 0, 0, 0, 0, 0],
        [-1.0, 0, 0, 0, 0, 0],
        [1.0, 0, 0, 0, 0, 0],
    ]
)
SR_HOR = 6


def _load(case, name):
    if name in ("data", "iv", "narrperiod"):
        from conftest import load_data

        return load_data(f"{case}_{name}")
    return np.atleast_2d(
        np.loadtxt(FIXTURES / f"{case}_{name}.csv", delimiter=",", ndmin=2)
    )


def _load_stack(case, name, ndim):
    flat = _load(case, name)
    shape = _load(case, f"{name}shape")[0].astype(int)
    return flat.reshape(*shape[:ndim], order="F")


@pytest.fixture(scope="module")
def uhlig():
    y = _load("uhlig2005", "data")
    model = VARmodel(y, nlags=12, det=1)
    Ball = _load_stack("uhlig2005", "Ball", 3)
    return model, Ball


@pytest.fixture(scope="module")
def adrr():
    y = _load("adrr2018", "data")
    # The paper excludes the constant.
    model = VARmodel(y, nlags=12, det=0)
    Ball = _load_stack("adrr2018", "Ball", 3)
    period = int(_load("adrr2018", "narrperiod")[0, 0])
    return model, Ball, period


class TestUhlig:
    def test_accepted_matrices_factorise_our_sigma(self, uhlig):
        """If this fails the rotations are being applied to a different
        covariance and nothing downstream is comparable."""
        model, Ball = uhlig
        for i in range(Ball.shape[2]):
            B = Ball[:, :, i]
            np.testing.assert_allclose(B @ B.T, model.sigma, atol=1e-8)

    def test_our_predicate_accepts_every_matlab_draw(self, uhlig):
        """The core check: MATLAB's accepted rotations must clear our sign and
        column-matching logic too."""
        model, Ball = uhlig
        psi = model.wold(SR_HOR - 1)
        for i in range(Ball.shape[2]):
            B = Ball[:, :, i]
            candidate = np.transpose(psi @ B, (1, 2, 0))
            assert _match(candidate, SIGN) is not None, f"draw {i} rejected"

    def test_restrictions_actually_hold_over_the_horizons(self, uhlig):
        model, Ball = uhlig
        psi = model.wold(SR_HOR - 1)
        restricted = SIGN[:, 0] != 0
        for i in range(Ball.shape[2]):
            irf = psi @ Ball[:, :, i]
            signed = irf[:, restricted, 0] * SIGN[restricted, 0]
            assert signed.min() >= -1e-9, f"draw {i} violates its own restriction"

    def test_impulse_responses_match(self, uhlig):
        """Our Wold recursion applied to MATLAB's B must give MATLAB's IRFs."""
        model, Ball = uhlig
        ref = _load_stack("uhlig2005", "IRall", 4)
        nsteps, _, _, ndraws = ref.shape
        psi = model.wold(nsteps - 1)
        for i in range(ndraws):
            np.testing.assert_allclose(psi @ Ball[:, :, i], ref[:, :, :, i], atol=1e-8)


class TestADRR:
    def test_accepted_matrices_factorise_our_sigma(self, adrr):
        model, Ball, _ = adrr
        for i in range(Ball.shape[2]):
            B = Ball[:, :, i]
            np.testing.assert_allclose(B @ B.T, model.sigma, atol=1e-8)

    def test_our_predicate_accepts_every_matlab_draw(self, adrr):
        model, Ball, _ = adrr
        psi = model.wold(SR_HOR - 1)
        for i in range(Ball.shape[2]):
            candidate = np.transpose(psi @ Ball[:, :, i], (1, 2, 0))
            assert _match(candidate, SIGN) is not None, f"draw {i} rejected"

    def test_narrative_constraints_hold_on_every_accepted_draw(self, adrr):
        """Both ADRR restrictions at October 1979: the monetary policy shock was
        positive, and it was the dominant driver of the funds rate."""
        from pyvartoolbox.sign import NarrativeDominance, NarrativeSign

        model, Ball, period = adrr
        narrative = [
            NarrativeSign(period=period - 1, shock=0, sign=1),
            NarrativeDominance(period=period - 1, shock=0, variable=5),
        ]
        ok = sum(
            _narrative_holds(Ball[:, :, i], model.resid, model.nlags, narrative)
            for i in range(Ball.shape[2])
        )
        assert ok == Ball.shape[2], f"{Ball.shape[2] - ok} draws failed"

    def test_narrative_is_binding(self, adrr):
        """Sanity check on the previous test: flipping the required sign must
        reject everything, otherwise the constraint is not being evaluated."""
        from pyvartoolbox.sign import NarrativeSign

        model, Ball, period = adrr
        flipped = [NarrativeSign(period=period - 1, shock=0, sign=-1)]
        ok = sum(
            _narrative_holds(Ball[:, :, i], model.resid, model.nlags, flipped)
            for i in range(Ball.shape[2])
        )
        assert ok == 0


def test_no_constant_specification_is_respected():
    """ADRR excludes the constant; a silent constant would shift every residual
    and invalidate the narrative checks."""
    y = _load("adrr2018", "data")
    assert VARmodel(y, nlags=12, det=0).ncoef == 12 * y.shape[1]
