"""JAX backend: agreement with numpy, and the float64 requirement.

The backends share their resample draws, generated in numpy, so these are exact
comparisons rather than distributional ones. Skipped entirely when JAX is not
installed — it is an optional dependency.
"""

import numpy as np
import pytest

from pyvartoolbox import VARmodel, bootstrap_irf
from pyvartoolbox._jax import available

pytestmark = pytest.mark.skipif(not available(), reason="jax not installed")


@pytest.fixture
def model(y_small):
    return VARmodel(y_small, nlags=2)


class TestParity:
    @pytest.mark.parametrize("ident", ["chol", "longrun"])
    def test_matches_numpy_draw_for_draw(self, model, ident):
        kw = dict(horizon=8, nboot=40, seed=0, ident=ident)
        a = bootstrap_irf(model, backend="numpy", **kw)
        b = bootstrap_irf(model, backend="jax", **kw)
        assert a.draws.shape == b.draws.shape
        np.testing.assert_allclose(a.draws, b.draws, rtol=0, atol=1e-10)

    def test_matches_numpy_for_the_wild_bootstrap(self, model):
        kw = dict(horizon=6, nboot=40, seed=1, method="wild")
        a = bootstrap_irf(model, backend="numpy", **kw)
        b = bootstrap_irf(model, backend="jax", **kw)
        np.testing.assert_allclose(a.draws, b.draws, rtol=0, atol=1e-10)

    def test_bands_agree(self, model):
        kw = dict(horizon=6, nboot=60, seed=2)
        a = bootstrap_irf(model, backend="numpy", **kw)
        b = bootstrap_irf(model, backend="jax", **kw)
        np.testing.assert_allclose(a.lower, b.lower, atol=1e-10)
        np.testing.assert_allclose(a.upper, b.upper, atol=1e-10)

    def test_same_draws_are_discarded(self, model):
        kw = dict(horizon=4, nboot=60, seed=3)
        a = bootstrap_irf(model, backend="numpy", **kw)
        b = bootstrap_irf(model, backend="jax", **kw)
        assert a.ndiscarded == b.ndiscarded


class TestPrecision:
    def test_x64_is_enabled(self):
        """float32 would silently corrupt long-horizon responses, because the
        companion recursion compounds the error."""
        from pyvartoolbox._jax import _setup

        _, jnp = _setup()
        assert jnp.zeros(1).dtype == np.float64

    def test_long_horizon_agreement_survives(self, model):
        """The case float32 would break: 200 horizons of compounding."""
        kw = dict(horizon=200, nboot=10, seed=4)
        a = bootstrap_irf(model, backend="numpy", **kw)
        b = bootstrap_irf(model, backend="jax", **kw)
        np.testing.assert_allclose(a.draws, b.draws, rtol=0, atol=1e-10)


class TestValidation:
    def test_unsupported_scheme_rejected(self, model):
        with pytest.raises(ValueError, match="JAX backend supports"):
            bootstrap_irf(model, horizon=4, nboot=5, ident="iv", backend="jax")

    def test_unknown_backend_rejected(self, model):
        with pytest.raises(ValueError, match="backend must be"):
            bootstrap_irf(model, horizon=4, nboot=5, backend="cuda")
