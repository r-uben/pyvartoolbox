"""Posterior draws of the VAR coefficients.

Like the bootstrap and the rotation sampler, this cannot be fixture-matched
against MATLAB — it consumes an RNG stream. The tests check the distributional
properties that make the draw correct.
"""

import numpy as np
import pytest

from pyvartoolbox import VARmodel
from pyvartoolbox.posterior import draw_posterior, wishart
from pyvartoolbox.sign import sign_restricted_irf


@pytest.fixture
def model(y_var1):
    return VARmodel(y_var1, nlags=1)


class TestWishart:
    def test_mean_is_df_times_scale(self):
        """The defining moment. Averaging over draws collapses sampling error,
        so a surviving discrepancy means the Bartlett construction is wrong."""
        rng = np.random.default_rng(0)
        scale = np.array([[2.0, 0.3], [0.3, 1.0]])
        df = 20
        draws = np.array([wishart(scale, df, rng) for _ in range(20000)])
        np.testing.assert_allclose(draws.mean(axis=0), df * scale, rtol=0.05)

    def test_draws_are_symmetric_positive_definite(self):
        rng = np.random.default_rng(1)
        scale = np.array([[2.0, 0.3], [0.3, 1.0]])
        for _ in range(50):
            W = wishart(scale, 5, rng)
            np.testing.assert_allclose(W, W.T, atol=1e-12)
            assert np.all(np.linalg.eigvalsh(W) > 0)

    def test_variance_matches_the_wishart_formula(self):
        """Var(W_ij) = df (S_ij^2 + S_ii S_jj). Catches a sampler that gets the
        mean right but the spread wrong."""
        rng = np.random.default_rng(2)
        S = np.array([[2.0, 0.3], [0.3, 1.0]])
        df = 12
        draws = np.array([wishart(S, df, rng) for _ in range(40000)])
        for i in range(2):
            for j in range(2):
                expected = df * (S[i, j] ** 2 + S[i, i] * S[j, j])
                assert np.isclose(draws[:, i, j].var(), expected, rtol=0.06)

    def test_insufficient_degrees_of_freedom_rejected(self):
        with pytest.raises(ValueError, match="degrees of freedom"):
            wishart(np.eye(3), 2, np.random.default_rng(0))


class TestPosteriorDraw:
    def test_draw_is_centred_on_the_ols_estimate(self, model):
        rng = np.random.default_rng(0)
        draws = np.array([draw_posterior(model, rng).beta for _ in range(3000)])
        np.testing.assert_allclose(draws.mean(axis=0), model.beta, atol=0.02)

    def test_sigma_draw_is_centred_near_the_estimate(self, model):
        rng = np.random.default_rng(1)
        draws = np.array([draw_posterior(model, rng).sigma for _ in range(3000)])
        np.testing.assert_allclose(draws.mean(axis=0), model.sigma, rtol=0.1)

    def test_coefficient_spread_matches_the_kronecker_covariance(self, model):
        """Sampling as beta_hat + Lx Z Ls' must reproduce sigma (x) (X'X)^-1
        without ever forming that Kronecker product."""
        rng = np.random.default_rng(2)
        draws = np.array([draw_posterior(model, rng).beta for _ in range(6000)])
        XtXi = np.linalg.inv(model.X.T @ model.X)
        # Variance of coefficient (i, j) is sigma_jj * XtXi_ii, in expectation
        # over the sigma draw.
        emp = draws.var(axis=0)
        expected = np.outer(np.diag(XtXi), np.diag(model.sigma))
        np.testing.assert_allclose(emp, expected, rtol=0.15)

    def test_drawn_model_behaves_like_a_model(self, model):
        rng = np.random.default_rng(3)
        drawn = draw_posterior(model, rng)
        assert drawn.ar_coefs.shape == model.ar_coefs.shape
        assert drawn.companion().shape == model.companion().shape
        assert drawn.irf(horizon=5).shape == model.irf(horizon=5).shape
        np.testing.assert_allclose(drawn.resid, model.Y - model.X @ drawn.beta)

    def test_original_model_is_not_mutated(self, model):
        before = model.beta.copy()
        draw_posterior(model, np.random.default_rng(4))
        np.testing.assert_array_equal(model.beta, before)


def test_posterior_bands_are_wider_than_identification_alone(y_small):
    """The reason posterior=True is the default: holding coefficients fixed
    understates uncertainty, because it drops estimation error entirely."""
    m = VARmodel(y_small, nlags=2)
    R = np.array([[1.0, -1.0], [1.0, 1.0]])
    kw = dict(horizon=6, ndraws=400, seed=0)
    ident_only = sign_restricted_irf(m, R, posterior=False, **kw)
    full = sign_restricted_irf(m, R, posterior=True, **kw)
    assert np.mean(full.upper - full.lower) > np.mean(
        ident_only.upper - ident_only.lower
    )
