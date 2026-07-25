"""Sign restrictions.

These cannot be fixture-matched against MATLAB: the sampler consumes an RNG
stream that numpy cannot reproduce. What *is* checkable, and is what these tests
do, is that the sampler has the properties the method requires — the rotation is
Haar-uniform, every accepted draw satisfies the restrictions it was given, and
the resulting impact matrices remain valid factorisations of sigma.
"""

import numpy as np
import pytest

from pyvartoolbox import VARmodel
from pyvartoolbox.sign import draw_rotation, haar_rotation, sign_restricted_irf


@pytest.fixture
def model(y_small):
    return VARmodel(y_small, nlags=2)


class TestHaarRotation:
    def test_is_orthonormal(self):
        rng = np.random.default_rng(0)
        for _ in range(20):
            Q = haar_rotation(4, rng)
            np.testing.assert_allclose(Q @ Q.T, np.eye(4), atol=1e-12)

    def test_reflections_and_rotations_are_equally_likely(self):
        """Haar measure on O(n) puts equal mass on both components, so the
        determinant should be -1 about half the time. A sampler that forgot the
        sign normalisation, or that forced det = +1, would fail this."""
        rng = np.random.default_rng(4)
        dets = np.array([np.linalg.det(haar_rotation(3, rng)) for _ in range(2000)])
        np.testing.assert_allclose(np.abs(dets), 1.0, atol=1e-10)
        assert 0.4 < np.mean(dets > 0) < 0.6

    def test_distribution_is_isotropic(self):
        """A Haar draw applied to a fixed vector is uniform on the sphere, so
        each coordinate of the result has mean zero."""
        rng = np.random.default_rng(2)
        e = np.zeros(3)
        e[0] = 1.0
        pts = np.array([haar_rotation(3, rng) @ e for _ in range(4000)])
        np.testing.assert_allclose(pts.mean(axis=0), 0.0, atol=0.05)
        np.testing.assert_allclose(np.linalg.norm(pts, axis=1), 1.0, atol=1e-12)


class TestRestrictionsAreSatisfied:
    def test_impact_signs_hold(self, model):
        rng = np.random.default_rng(0)
        R = np.array([[1.0, -1.0], [1.0, 1.0]])
        for _ in range(25):
            B, _ = draw_rotation(model, R, rng)
            assert B is not None
            restricted = R != 0
            assert np.all(B[restricted] * R[restricted] >= 0)

    def test_impact_matrix_still_factorises_sigma(self, model):
        rng = np.random.default_rng(0)
        R = np.array([[1.0, -1.0], [1.0, 1.0]])
        B, _ = draw_rotation(model, R, rng)
        np.testing.assert_allclose(B @ B.T, model.sigma, atol=1e-10)

    def test_multi_horizon_restrictions_hold_at_every_horizon(self, model):
        rng = np.random.default_rng(3)
        R = np.array([[1.0, 0.0], [0.0, 1.0]])
        B, _ = draw_rotation(model, R, rng, sr_hor=4)
        assert B is not None
        irf = model.wold(3) @ B
        assert np.all(irf[:, 0, 0] >= -1e-12)
        assert np.all(irf[:, 1, 1] >= -1e-12)

    def test_zeros_leave_a_response_unrestricted(self, model):
        """A fully unrestricted column must accept the first candidate, so the
        search should terminate immediately."""
        rng = np.random.default_rng(0)
        R = np.zeros((2, 2))
        _, ntried = draw_rotation(model, R, rng)
        assert ntried == 1

    def test_both_shocks_may_share_a_sign_pattern(self, model):
        """Worth pinning down, because it is a natural thing to get wrong: the
        columns of B = P @ Q are *not* orthogonal — only Q's are — so nothing
        stops two shocks from both loading positively on every variable."""
        rng = np.random.default_rng(0)
        R = np.array([[1.0, 1.0], [1.0, 1.0]])
        B, _ = draw_rotation(model, R, rng, max_rot=50)
        assert B is not None
        assert np.all(B >= 0)

    def test_exhausted_budget_returns_none(self, y_var1):
        """A demanding pattern over many horizons has vanishing acceptance
        probability, which exercises the give-up path."""
        rng = np.random.default_rng(0)
        wide = VARmodel(np.column_stack([y_var1, y_var1[::-1]]), nlags=2)
        R = np.array([[1.0, -1.0, 1.0, -1.0]] * 4)
        B, ntried = draw_rotation(wide, R, rng, sr_hor=12, max_rot=40)
        assert B is None
        assert ntried == 40


class TestValidation:
    def test_wrong_row_count_rejected(self, model):
        with pytest.raises(ValueError, match="but the VAR has"):
            draw_rotation(model, np.ones((3, 2)), np.random.default_rng(0))

    def test_too_many_shocks_rejected(self, model):
        with pytest.raises(ValueError, match="more shocks than"):
            draw_rotation(model, np.ones((2, 3)), np.random.default_rng(0))

    def test_non_ternary_entries_rejected(self, model):
        with pytest.raises(ValueError, match="only -1, 0 and"):
            bad = np.array([[0.5, 0.0], [0.0, 1.0]])
            draw_rotation(model, bad, np.random.default_rng(0))


class TestBands:
    def test_shapes_and_ordering(self, model):
        R = np.array([[1.0, -1.0], [1.0, 1.0]])
        res = sign_restricted_irf(model, R, horizon=8, ndraws=100, seed=0)
        assert res.draws.shape == (res.naccepted, 9, 2, 2)
        assert np.all(res.lower <= res.median)
        assert np.all(res.median <= res.upper)
        assert 0 < res.acceptance_rate <= 1

    def test_reproducible_under_seed(self, model):
        R = np.array([[1.0, -1.0], [1.0, 1.0]])
        a = sign_restricted_irf(model, R, horizon=4, ndraws=50, seed=7)
        b = sign_restricted_irf(model, R, horizon=4, ndraws=50, seed=7)
        np.testing.assert_array_equal(a.draws, b.draws)

    def test_every_accepted_draw_satisfies_the_restrictions(self, model):
        R = np.array([[1.0, -1.0], [1.0, 1.0]])
        res = sign_restricted_irf(model, R, horizon=4, ndraws=80, seed=1)
        impact = res.draws[:, 0, :, :]
        restricted = R != 0
        assert np.all(impact[:, restricted] * R[restricted] >= -1e-12)

    def test_unreachable_pattern_raises(self, y_var1):
        wide = VARmodel(np.column_stack([y_var1, y_var1[::-1]]), nlags=2)
        R = np.array([[1.0, -1.0, 1.0, -1.0]] * 4)
        with pytest.raises(RuntimeError, match="satisfying the sign pattern"):
            sign_restricted_irf(wide, R, horizon=4, ndraws=5, sr_hor=12, max_rot=20)


class TestNarrativeRestrictions:
    """Antolin-Diaz and Rubio-Ramirez (2018) constraints, applied as upstream
    applies them: a rejection filter on top of the sign pattern."""

    R = np.array([[1.0, -1.0], [1.0, 1.0]])

    def test_sign_restriction_on_a_date_is_enforced(self, model):
        from pyvartoolbox.sign import NarrativeSign

        narr = [NarrativeSign(period=40, shock=0, sign=1)]
        res = sign_restricted_irf(
            model, self.R, horizon=4, ndraws=60, seed=0, narrative=narr
        )
        assert res.naccepted > 0

    def test_narrative_filter_only_removes_draws(self, model):
        """Adding a narrative constraint can never raise the acceptance count
        for a fixed seed and draw budget."""
        from pyvartoolbox.sign import NarrativeSign

        kw = dict(horizon=4, ndraws=80, seed=3)
        plain = sign_restricted_irf(model, self.R, **kw)
        narrowed = sign_restricted_irf(
            model,
            self.R,
            narrative=[NarrativeSign(period=40, shock=0, sign=1)],
            **kw,
        )
        assert narrowed.naccepted <= plain.naccepted

    def test_opposite_narrative_signs_partition_the_draws(self, model):
        """A draw satisfying "shock 0 is positive at t" cannot also satisfy
        "shock 0 is negative at t", so together they can never accept more than
        the unfiltered sampler. On this sample one direction is never satisfied
        at all, which is why each call is guarded."""
        from pyvartoolbox.sign import NarrativeSign

        kw = dict(horizon=2, ndraws=120, seed=5)

        def count(sign):
            try:
                return sign_restricted_irf(
                    model, self.R, narrative=[NarrativeSign(40, 0, sign)], **kw
                ).naccepted
            except RuntimeError:
                return 0

        plain = sign_restricted_irf(model, self.R, **kw)
        assert count(1) + count(-1) <= plain.naccepted

    def test_dominance_constraint_runs_and_filters(self, model):
        from pyvartoolbox.sign import NarrativeDominance

        kw = dict(horizon=4, ndraws=100, seed=7)
        plain = sign_restricted_irf(model, self.R, **kw)
        dom = sign_restricted_irf(
            model,
            self.R,
            narrative=[NarrativeDominance(period=40, shock=0, variable=0)],
            **kw,
        )
        assert dom.naccepted <= plain.naccepted

    def test_out_of_sample_period_rejected(self, model):
        from pyvartoolbox.sign import NarrativeSign

        with pytest.raises(IndexError, match="outside the estimation sample"):
            sign_restricted_irf(
                model,
                self.R,
                horizon=2,
                ndraws=5,
                seed=0,
                narrative=[NarrativeSign(period=100000, shock=0, sign=1)],
            )
