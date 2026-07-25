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
        with pytest.raises(NotImplementedError, match="proxy SVAR"):
            m.irf(horizon=5, ident="iv")

    def test_unknown_scheme_raises_value_error(self, y_small):
        m = VARmodel(y_small, nlags=2)
        with pytest.raises(ValueError, match="unknown identification"):
            m.irf(horizon=5, ident="nonsense")
