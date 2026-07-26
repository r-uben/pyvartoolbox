import numpy as np
import pytest

from pyvartoolbox import DET_NONE, DET_TREND, VARmodel, make_lags, make_xy


class TestLagConstruction:
    def test_layout(self):
        y = np.arange(12, dtype=float).reshape(6, 2)
        lags = make_lags(y, nlags=2)
        assert lags.shape == (4, 4)
        # Row 0 corresponds to t = 2, so [y_1, y_0].
        np.testing.assert_allclose(lags[0], [2, 3, 0, 1])
        np.testing.assert_allclose(lags[-1], [8, 9, 6, 7])

    def test_trend_starts_at_one_on_estimation_sample(self):
        y = np.arange(20, dtype=float).reshape(10, 2)
        _, X, names = make_xy(y, nlags=3, det=DET_TREND)
        assert names == ["const", "trend"]
        np.testing.assert_allclose(X[:, -1], np.arange(1, 8))

    def test_rejects_too_short_sample(self):
        with pytest.raises(ValueError, match="more than nlags"):
            make_lags(np.zeros((3, 2)), nlags=3)


class TestEstimation:
    def test_recovers_known_coefficients(self, var1, y_var1):
        """Single long sample: loose tolerance, since one draw carries real
        sampling error. The Monte Carlo test below is the sharp one."""
        A, c, sigma = var1
        m = VARmodel(y_var1, nlags=1)
        np.testing.assert_allclose(m.ar_coefs[0], A[0], atol=0.05)
        np.testing.assert_allclose(m.det_coefs[:, 0], c, atol=0.1)
        np.testing.assert_allclose(m.sigma, sigma, atol=0.1)

    def test_estimator_is_unbiased_in_monte_carlo(self, var1):
        """Averaging over replications collapses sampling error, so a surviving
        discrepancy would indicate a layout or orientation bug rather than
        noise. OLS on a VAR is biased in finite samples at order 1/T, which at
        T=2000 is well inside this tolerance."""
        from conftest import simulate_var

        A, c, sigma = var1
        fits = [
            VARmodel(simulate_var(A, c, sigma, nobs=2000, seed=s), nlags=1)
            for s in range(30)
        ]
        est = np.array([m.ar_coefs[0] for m in fits])
        np.testing.assert_allclose(est.mean(axis=0), A[0], atol=0.01)

    def test_shapes(self, y_var1):
        m = VARmodel(y_var1, nlags=4)
        assert m.nvar == 2
        assert m.neff == y_var1.shape[0] - 4
        assert m.ncoef == 2 * 4 + 1
        assert m.ar_coefs.shape == (4, 2, 2)
        assert m.beta.shape == (9, 2)

    def test_residuals_orthogonal_to_regressors(self, y_small):
        m = VARmodel(y_small, nlags=2)
        np.testing.assert_allclose(m.X.T @ m.resid, 0.0, atol=1e-8)

    def test_simulate_reproduces_sample(self, y_small):
        """Feeding the fitted residuals back through the recursion must return
        the original series exactly. This pins down the orientation of both the
        AR blocks and the deterministic block."""
        m = VARmodel(y_small, nlags=3, det=DET_TREND)
        rebuilt = m.simulate(m.resid, y_small[:3])
        np.testing.assert_allclose(rebuilt, y_small, atol=1e-8)

    def test_no_deterministic_terms(self, y_small):
        m = VARmodel(y_small, nlags=2, det=DET_NONE)
        assert m.ncoef == 4
        assert m.det_coefs.shape == (2, 0)

    def test_exog_enters_contemporaneously(self, y_small):
        z = np.linspace(0, 1, y_small.shape[0])
        m = VARmodel(y_small, nlags=2, exog=z)
        assert m.ncoef == 2 * 2 + 1 + 1
        assert m.det_names == ["exog1", "const"]

    def test_rejects_overparameterised_sample(self):
        with pytest.raises(ValueError, match="usable observations"):
            VARmodel(np.random.default_rng(0).standard_normal((12, 3)), nlags=3)


class TestDynamics:
    def test_wold_matches_companion_powers(self, y_small):
        m = VARmodel(y_small, nlags=3)
        k = m.nvar
        F = m.companion()
        psi = m.wold(horizon=10)
        Fh = np.eye(k * m.nlags)
        for h in range(11):
            np.testing.assert_allclose(psi[h], Fh[:k, :k], atol=1e-10)
            Fh = Fh @ F

    def test_stable_dgp_is_stable(self, y_small):
        m = VARmodel(y_small, nlags=1)
        assert m.is_stable()
        assert m.max_eig() < 1.0

    def test_wold_decays_for_stable_var(self, y_small):
        m = VARmodel(y_small, nlags=2)
        psi = m.wold(horizon=200)
        assert np.abs(psi[-1]).max() < 1e-6


class TestIdentification:
    def test_cholesky_impact_reproduces_sigma(self, y_small):
        m = VARmodel(y_small, nlags=2)
        irf = m.irf(horizon=5)
        np.testing.assert_allclose(irf[0] @ irf[0].T, m.sigma, atol=1e-10)

    def test_cholesky_impact_is_lower_triangular(self, y_small):
        m = VARmodel(y_small, nlags=2)
        impact = m.irf(horizon=1)[0]
        assert impact[0, 1] == pytest.approx(0.0, abs=1e-12)

    def test_longrun_restriction_holds(self, y_small):
        """Under 'longrun', the cumulated response of variable 0 to shock 1
        must vanish."""
        m = VARmodel(y_small, nlags=2)
        cum = m.irf(horizon=500, ident="longrun").sum(axis=0)
        assert cum[0, 1] == pytest.approx(0.0, abs=1e-6)
        # Still a valid decomposition of the covariance.
        impact = m.irf(horizon=0, ident="longrun")[0]
        np.testing.assert_allclose(impact @ impact.T, m.sigma, atol=1e-10)

    def test_vd_shares_sum_to_one(self, y_small):
        m = VARmodel(y_small, nlags=2)
        vd = m.vd(horizon=20)
        np.testing.assert_allclose(vd.sum(axis=2), 1.0, atol=1e-10)
        assert vd.min() >= 0.0

    def test_vd_impact_of_first_shock_on_first_variable(self, y_small):
        """With a recursive ordering the first variable's impact-horizon
        variance is entirely its own shock."""
        m = VARmodel(y_small, nlags=2)
        assert m.vd(horizon=3)[0, 0, 0] == pytest.approx(1.0)

    def test_planned_scheme_raises_not_implemented(self, y_small):
        m = VARmodel(y_small, nlags=2)
        with pytest.raises(NotImplementedError, match="sign restrictions"):
            m.irf(horizon=5, ident="sign")

    def test_set_identified_scheme_points_at_the_sampler(self, y_small):
        """A set-identified name must not read as "missing feature".

        `impact_matrix` returns one `B`; a set-identified scheme has none, so
        the error has to send the user to the sampler rather than imply the
        scheme is unimplemented."""
        from pyvartoolbox.ident import impact_matrix

        m = VARmodel(y_small, nlags=2)
        for scheme in ("sign", "narrative", "signiv"):
            with pytest.raises(NotImplementedError, match="sign_restricted_irf"):
                impact_matrix(m, scheme)

    def test_unknown_scheme_raises_value_error(self, y_small):
        m = VARmodel(y_small, nlags=2)
        with pytest.raises(ValueError, match="unknown identification"):
            m.irf(horizon=5, ident="nonsense")


class TestProxyIV:
    """Behaviour of the external-instrument scheme that the GK2015 fixture in
    test_reference.py does not exercise."""

    @pytest.fixture
    def setup(self, y_small):
        rng = np.random.default_rng(0)
        m = VARmodel(y_small, nlags=2)
        # Instrument correlated with the first structural shock, aligned on the
        # full sample with a leading gap.
        z = np.full(y_small.shape[0], np.nan)
        z[10:] = m.resid[8:, 0] + 0.5 * rng.standard_normal(len(m.resid) - 8)
        return m, z

    def test_identifies_only_the_first_shock(self, setup):
        m, z = setup
        irf = m.irf(horizon=10, ident="iv", iv=z)
        assert np.abs(irf[:, :, 0]).max() > 0
        np.testing.assert_allclose(irf[:, :, 1:], 0.0)

    def test_completion_is_invertible_and_preserves_the_iv_column(self, setup):
        """The completion exists only so B is invertible for the HD backout.

        Note what it is *not*: a factorisation of sigma. The orthonormal
        completion satisfies B @ B.T == sigma, but the identified column is then
        restored exactly on top of it, which breaks that identity unless the IV
        impact happens to have unit norm in the Cholesky basis. Upstream makes
        the same trade deliberately — exact shock-1 IRFs are worth more than a
        tidy covariance identity, because the other columns are meaningless
        anyway."""
        from pyvartoolbox.ident import impact_matrix

        m, z = setup
        B = impact_matrix(m, "iv", iv=z)
        assert np.linalg.matrix_rank(B) == m.nvar
        assert np.isfinite(np.linalg.inv(B)).all()
        # Columns 1: remain a valid orthonormal completion in the Cholesky basis.
        P = np.linalg.cholesky(m.sigma)
        Qtail = np.linalg.solve(P, B[:, 1:])
        np.testing.assert_allclose(Qtail.T @ Qtail, np.eye(m.nvar - 1), atol=1e-10)

    def test_vd_shares_are_bounded(self, setup):
        m, z = setup
        vd = m.vd(horizon=10, ident="iv", iv=z)
        assert 0.0 <= vd[:, :, 0].min() and vd[:, :, 0].max() <= 1.0

    def test_misaligned_instrument_rejected(self, setup):
        m, z = setup
        with pytest.raises(ValueError, match="aligned on the full sample"):
            m.irf(ident="iv", iv=z[:-5])

    def test_interior_gap_rejected(self, setup):
        m, z = setup
        z = z.copy()
        z[50] = np.nan
        with pytest.raises(ValueError, match="interior missing values"):
            m.irf(ident="iv", iv=z)

    def test_no_overlap_rejected(self, setup):
        m, z = setup
        with pytest.raises(ValueError, match="no overlapping sample"):
            m.irf(ident="iv", iv=np.full_like(z, np.nan))
