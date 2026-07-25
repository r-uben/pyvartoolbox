import numpy as np
import pytest

from pyvartoolbox import VARmodel, bootstrap_irf


@pytest.fixture
def fitted(y_small):
    return VARmodel(y_small, nlags=2)


class TestBootstrap:
    def test_shapes_and_ordering(self, fitted):
        res = bootstrap_irf(fitted, horizon=12, nboot=100, seed=0)
        assert res.irf.shape == (13, 2, 2)
        assert res.lower.shape == res.upper.shape == res.irf.shape
        assert res.draws.shape[1:] == res.irf.shape
        assert np.all(res.lower <= res.upper)

    def test_reproducible_under_seed(self, fitted):
        a = bootstrap_irf(fitted, horizon=6, nboot=50, seed=42)
        b = bootstrap_irf(fitted, horizon=6, nboot=50, seed=42)
        np.testing.assert_array_equal(a.draws, b.draws)

    def test_different_seeds_differ(self, fitted):
        a = bootstrap_irf(fitted, horizon=6, nboot=50, seed=1)
        b = bootstrap_irf(fitted, horizon=6, nboot=50, seed=2)
        assert not np.allclose(a.draws, b.draws)

    def test_bands_contain_point_estimate_on_impact(self, fitted):
        res = bootstrap_irf(fitted, horizon=12, nboot=300, seed=3)
        own = (slice(None), [0, 1], [0, 1])
        assert np.all(res.lower[own] <= res.irf[own] + 1e-9)
        assert np.all(res.irf[own] <= res.upper[own] + 1e-9)

    def test_wider_ci_gives_wider_bands(self, fitted):
        narrow = bootstrap_irf(fitted, horizon=8, nboot=300, seed=5, ci=0.68)
        wide = bootstrap_irf(fitted, horizon=8, nboot=300, seed=5, ci=0.95)
        assert np.all(wide.upper - wide.lower >= narrow.upper - narrow.lower - 1e-12)

    def test_wild_bootstrap_runs(self, fitted):
        res = bootstrap_irf(fitted, horizon=8, nboot=100, method="wild", seed=0)
        assert res.draws.shape[0] > 90
        assert np.isfinite(res.lower).all()

    def test_bands_tighten_with_sample_size(self, var1):
        from conftest import simulate_var

        A, c, sigma = var1
        widths = []
        for nobs in (120, 2000):
            m = VARmodel(simulate_var(A, c, sigma, nobs=nobs, seed=17), nlags=1)
            r = bootstrap_irf(m, horizon=4, nboot=200, seed=0)
            widths.append(np.mean(r.upper - r.lower))
        assert widths[1] < widths[0]

    def test_unknown_method_rejected(self, fitted):
        with pytest.raises(ValueError, match="unknown bootstrap method"):
            bootstrap_irf(fitted, nboot=10, method="jackknife")

    def test_invalid_ci_rejected(self, fitted):
        with pytest.raises(ValueError, match="ci must be"):
            bootstrap_irf(fitted, nboot=10, ci=1.5)
