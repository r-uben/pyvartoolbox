"""Local projections, validated against the MATLAB reference (JT2025).

The fixture reproduces `GO_JT2025.m` section 2: Jorda and Taylor (2025), CPI
response to a Romer-Romer monetary shock, 1985q1-2007q4, 4 lags, constant,
long-difference LHS, unit shock, 18 horizons, 95% Newey-West bands.
"""

from pathlib import Path

import numpy as np
import pytest

from pyvartoolbox.lp import local_projection, newey_west_se

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> np.ndarray:
    if name == "data":
        from conftest import load_data

        return load_data("jt2025_data")
    return np.atleast_2d(
        np.loadtxt(FIXTURES / f"jt2025_{name}.csv", delimiter=",", ndmin=2)
    )


@pytest.fixture
def jt():
    data = _load("data")
    endo, treat, ctrl = data[:, 0], data[:, 1], data[:, 2:]
    # Upstream's nsteps = 18 covers horizons 0..17.
    return local_projection(
        endo,
        treat,
        ctrl,
        nlags=4,
        det=1,
        horizon=17,
        ci=0.95,
        unit_shock=True,
        long_diff=True,
    )


class TestAgainstMatlab:
    def test_impulse_responses(self, jt):
        np.testing.assert_allclose(jt.ir, _load("IR").ravel(), rtol=0, atol=1e-9)

    def test_newey_west_standard_errors(self, jt):
        np.testing.assert_allclose(jt.se, _load("seNW").ravel(), rtol=0, atol=1e-9)

    def test_confidence_bands(self, jt):
        np.testing.assert_allclose(jt.lower, _load("INF").ravel(), rtol=0, atol=1e-9)
        np.testing.assert_allclose(jt.upper, _load("SUP").ravel(), rtol=0, atol=1e-9)

    def test_sample_shrinks_by_one_per_horizon(self, jt):
        np.testing.assert_array_equal(np.diff(jt.nobs), -1)


class TestNeweyWest:
    def test_zero_bandwidth_is_the_white_sandwich(self):
        rng = np.random.default_rng(0)
        X = np.column_stack([np.ones(200), rng.standard_normal(200)])
        resid = rng.standard_normal(200)
        XtXi = np.linalg.inv(X.T @ X)
        h = X * resid[:, None]
        white = np.sqrt(np.diag(XtXi @ (h.T @ h) @ XtXi))
        np.testing.assert_allclose(newey_west_se(X, resid, 0), white, atol=1e-12)

    def test_bartlett_weights_decline_to_zero(self):
        """A bandwidth-L estimator must ignore lag L+1 entirely: extending the
        bandwidth by one adds a term with weight 1/(L+2), not a jump."""
        rng = np.random.default_rng(1)
        X = np.column_stack([np.ones(300), rng.standard_normal(300)])
        resid = rng.standard_normal(300)
        se = [newey_west_se(X, resid, L)[1] for L in range(6)]
        assert all(np.isfinite(se))
        assert max(np.abs(np.diff(se))) < 0.5 * se[0]

    def test_serial_correlation_inflates_the_standard_error(self):
        """The point of Newey-West: with positively autocorrelated residuals the
        robust standard error should exceed the naive one."""
        rng = np.random.default_rng(2)
        n = 500
        X = np.column_stack([np.ones(n), rng.standard_normal(n)])
        e = np.zeros(n)
        for t in range(1, n):
            e[t] = 0.8 * e[t - 1] + rng.standard_normal()
        assert newey_west_se(X, e, 10)[0] > newey_west_se(X, e, 0)[0]

    def test_negative_bandwidth_rejected(self):
        with pytest.raises(ValueError, match="nlags must be >= 0"):
            newey_west_se(np.ones((5, 1)), np.ones(5), -1)


class TestBehaviour:
    def test_standardised_shock_scales_responses(self):
        """impact=0 divides the shock by its standard deviation, so responses
        scale by exactly that factor relative to a unit shock."""
        data = _load("data")
        endo, treat, ctrl = data[:, 0], data[:, 1], data[:, 2:]
        kw = dict(ctrl=ctrl, nlags=4, horizon=6, long_diff=True)
        unit = local_projection(endo, treat, unit_shock=True, **kw)
        std = local_projection(endo, treat, unit_shock=False, **kw)
        sd = treat[4:].std(ddof=1)
        np.testing.assert_allclose(std.ir, unit.ir * sd, rtol=1e-10)

    def test_long_diff_differs_from_levels(self):
        data = _load("data")
        endo, treat, ctrl = data[:, 0], data[:, 1], data[:, 2:]
        kw = dict(ctrl=ctrl, nlags=4, horizon=6, unit_shock=True)
        assert not np.allclose(
            local_projection(endo, treat, long_diff=True, **kw).ir,
            local_projection(endo, treat, long_diff=False, **kw).ir,
        )

    def test_horizon_zero_is_a_single_regression(self):
        data = _load("data")
        endo, treat = data[:, 0], data[:, 1]
        res = local_projection(endo, treat, nlags=4, horizon=0, unit_shock=True)
        assert res.ir.shape == (1,)
        assert res.nobs[0] == endo.shape[0] - 4

    def test_mismatched_lengths_rejected(self):
        with pytest.raises(ValueError, match="observations but treat has"):
            local_projection(np.zeros(50), np.zeros(40))

    def test_horizon_too_long_rejected(self):
        data = _load("data")
        endo, treat, ctrl = data[:, 0], data[:, 1], data[:, 2:]
        with pytest.raises(ValueError, match="shorten the horizon"):
            local_projection(endo, treat, ctrl, nlags=4, horizon=200)

    def test_bad_det_rejected(self):
        with pytest.raises(ValueError, match="det must be"):
            local_projection(np.zeros(50), np.zeros(50), det=3)


def test_bandwidth_cannot_exceed_the_sample():
    """Regression test: this used to surface as a cryptic matmul error from
    inside the lag loop instead of a stated precondition."""
    rng = np.random.default_rng(0)
    X = np.column_stack([np.ones(10), rng.standard_normal(10)])
    with pytest.raises(ValueError, match="needs more than"):
        newey_west_se(X, rng.standard_normal(10), 10)


class TestLPIV:
    """Instrumented local projections, validated against JT2025 section 3:
    unemployment on the federal funds rate, instrumented by the Romer-Romer
    RRCG shock with 6 instrument lags, 1985m1-2000m1."""

    @pytest.fixture
    def fit(self):
        from conftest import load_data

        data = load_data("jt2025iv_data")
        instr = load_data("jt2025iv_iv").ravel()
        return local_projection(
            endo=data[:, 0],
            treat=data[:, 1],
            ctrl=data[:, 2:],
            nlags=6,
            det=1,
            horizon=48,
            ci=0.95,
            unit_shock=True,
            long_diff=True,
            iv=instr,
            nlags_iv=6,
        )

    def _ref(self, name):
        return np.loadtxt(FIXTURES / f"jt2025iv_{name}.csv", delimiter=",")

    def test_impulse_responses(self, fit):
        np.testing.assert_allclose(fit.ir, self._ref("IR"), rtol=0, atol=1e-8)

    def test_standard_errors(self, fit):
        np.testing.assert_allclose(fit.se, self._ref("se"), rtol=0, atol=1e-8)

    def test_confidence_bands(self, fit):
        np.testing.assert_allclose(fit.lower, self._ref("INF"), rtol=0, atol=1e-8)
        np.testing.assert_allclose(fit.upper, self._ref("SUP"), rtol=0, atol=1e-8)

    def test_first_stage_f(self, fit):
        np.testing.assert_allclose(
            fit.first_stage_f, self._ref("Fstat"), rtol=1e-9, atol=0
        )

    def test_instrument_lags_cannot_exceed_control_lags(self):
        with pytest.raises(ValueError, match="cannot exceed nlags"):
            local_projection(
                np.zeros(50), np.zeros(50), nlags=2, iv=np.zeros(50), nlags_iv=5
            )

    def test_ols_path_reports_no_first_stage(self):
        data = _load("data")
        res = local_projection(data[:, 0], data[:, 1], nlags=4, horizon=3)
        assert res.first_stage_f is None
