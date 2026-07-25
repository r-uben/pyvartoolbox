"""Historical decomposition: adding-up, and agreement with the MATLAB reference."""

import numpy as np
import pytest

from pyvartoolbox import VARmodel
from test_reference import CASES, _load, _load3d


@pytest.fixture(params=sorted(CASES))
def case(request):
    name = request.param
    spec = CASES[name]
    y = _load(name, "data")
    model = VARmodel(y, nlags=spec["nlags"], det=1)
    kwargs = {"iv": _load(name, "iv")} if spec["ident"] == "iv" else {}
    return name, spec, model, kwargs


class TestAddingUp:
    """The defining property: the components must reconstruct the data."""

    def test_components_sum_to_the_data(self, case):
        name, spec, m, kw = case
        decomp = m.hd(spec["ident"], **kw)
        assert decomp.check(m.y, atol=spec["atol"])

    def test_presample_is_masked(self, case):
        _, spec, m, kw = case
        decomp = m.hd(spec["ident"], **kw)
        assert np.isnan(decomp.shock[: m.nlags]).all()
        assert np.isnan(decomp.total[: m.nlags]).all()
        # init carries one fewer NaN row: its t=0 state is the last presample
        # period, which is a real value rather than a gap.
        assert np.isnan(decomp.init[: m.nlags - 1]).all()
        assert np.isfinite(decomp.init[m.nlags - 1]).all()

    def test_shapes(self, case):
        _, spec, m, kw = case
        decomp = m.hd(spec["ident"], **kw)
        nobs = m.y.shape[0]
        assert decomp.shock.shape == (nobs, m.nvar, m.nvar)
        assert decomp.init.shape == decomp.const.shape == (nobs, m.nvar)


class TestAgainstMatlab:
    def test_shock_contributions(self, case):
        name, spec, m, kw = case
        # Upstream stores HD.shock as (time, shock, variable); ours is
        # (time, variable, shock), matching our own IRF convention.
        ref = _load3d(name, "HDshock").transpose(0, 2, 1)
        got = m.hd(spec["ident"], **kw).shock
        np.testing.assert_allclose(got, ref, rtol=0, atol=spec["atol"])

    def test_initial_condition(self, case):
        name, spec, m, kw = case
        got = m.hd(spec["ident"], **kw).init
        np.testing.assert_allclose(
            got, _load(name, "HDinit"), rtol=0, atol=spec["atol"]
        )

    def test_constant_contribution(self, case):
        name, spec, m, kw = case
        got = m.hd(spec["ident"], **kw).const
        np.testing.assert_allclose(
            got, _load(name, "HDconst"), rtol=0, atol=spec["atol"]
        )

    def test_total(self, case):
        name, spec, m, kw = case
        got = m.hd(spec["ident"], **kw).total
        np.testing.assert_allclose(
            got, _load(name, "HDendo"), rtol=0, atol=spec["atol"]
        )


def test_deterministic_helper_adds_const_and_trend(y_small):
    m = VARmodel(y_small, nlags=2)
    decomp = m.hd()
    np.testing.assert_allclose(
        decomp.deterministic[m.nlags :],
        (decomp.const + decomp.trend)[m.nlags :],
    )
