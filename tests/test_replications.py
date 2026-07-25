"""The six replications, run end to end.

Distinct from the fixture tests: those check our numbers against MATLAB's on
identical specifications, while these check that the whole pipeline runs from a
clean install and produces economically sensible results — which is the thing a
user actually does.

The sign assertions are deliberately about direction, not magnitude. They are
the qualitative findings of the papers, so they would catch a wiring error
(wrong column, flipped shock, mis-aligned instrument) that a numerical tolerance
on our own output would not.
"""

import numpy as np
import pytest

matplotlib = pytest.importorskip("matplotlib")
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from pyvartoolbox import replications  # noqa: E402


@pytest.fixture(autouse=True)
def close_figures():
    yield
    plt.close("all")


def test_every_upstream_exercise_is_covered():
    assert set(replications.REPLICATIONS) == {
        "sw2001",
        "bq1989",
        "gk2015",
        "uhlig2005",
        "adrr2018",
        "jt2025",
    }


class TestStockWatson:
    def test_table_1b_shares_are_valid(self):
        res = replications.stock_watson_2001(nboot=30, seed=0)
        for horizon, block in res["table_1b"].items():
            assert block.shape == (3, 3)
            np.testing.assert_allclose(block.sum(axis=1), 100.0, atol=1e-8)
            assert block.min() >= 0, f"negative share at horizon {horizon}"

    def test_own_shock_dominates_on_impact(self):
        """Under a recursive ordering the first variable's impact variance is
        entirely its own shock."""
        res = replications.stock_watson_2001(nboot=30, seed=0)
        assert res["table_1b"][1][0, 0] == pytest.approx(100.0)


class TestBlanchardQuah:
    def test_demand_shock_has_no_permanent_output_effect(self):
        """The identifying restriction. It binds asymptotically, not at the
        40-quarter horizon the paper plots, so check the limit on the model
        rather than on the figure's truncated sum."""
        res = replications.blanchard_quah_1989()
        limit = res["model"].irf(horizon=800, ident="longrun").sum(axis=0)
        assert limit[0, 1] == pytest.approx(0.0, abs=1e-6)
        # At the plotted horizon it is merely small, not zero.
        assert abs(res["cumulative"][-1, 0, 1]) < 1e-2

    def test_supply_shock_does_have_one(self):
        res = replications.blanchard_quah_1989()
        assert abs(res["cumulative"][-1, 0, 0]) > 1e-3


class TestGertlerKaradi:
    def test_monetary_tightening_has_the_expected_signs(self):
        """The paper's headline: a contractionary shock raises the policy rate,
        lowers prices and output, and widens the excess bond premium."""
        res = replications.gertler_karadi_2015()
        impact = res["irf_iv"][0, :, 0]
        assert impact[0] > 0, "1yr rate should rise"
        assert impact[3] > 0, "excess bond premium should widen"
        # Output and prices fall over the first two years.
        assert res["irf_iv"][:24, 1, 0].min() < 0, "CPI should fall"
        assert res["irf_iv"][:24, 2, 0].min() < 0, "industrial production should fall"

    def test_proxy_and_cholesky_differ(self):
        """If these coincided the instrument would be doing nothing."""
        res = replications.gertler_karadi_2015()
        assert not np.allclose(res["irf_iv"][:, :, 0], res["irf_chol"][:, :, 0])


class TestSignRestricted:
    def test_uhlig_draws_satisfy_the_monetary_pattern(self):
        res = replications.uhlig_2005(ndraws=15, seed=0)["result"]
        impact = res.draws[:, 0, :, 0]
        assert (impact[:, 5] >= -1e-9).all(), "funds rate must rise"
        assert (impact[:, 1] <= 1e-9).all(), "deflator must fall"
        assert (impact[:, 4] <= 1e-9).all(), "nonborrowed reserves must fall"

    def test_narrative_restrictions_tighten_the_set(self):
        """ADRR's point: the narrative constraints are informative, so they must
        actually remove draws the sign pattern alone admits."""
        res = replications.antolin_diaz_rubio_ramirez_2018(ndraws=15, seed=0)
        assert res["narrative"].acceptance_rate < res["sign_only"].acceptance_rate


class TestJordaTaylor:
    def test_both_projections_produce_finite_bands(self):
        res = replications.jorda_taylor_2025()
        for key in ("ols", "iv"):
            lp = res[key]
            assert np.isfinite(lp.ir).all()
            assert np.all(lp.lower <= lp.ir)
            assert np.all(lp.ir <= lp.upper)

    def test_iv_reports_a_usable_first_stage(self):
        res = replications.jorda_taylor_2025()
        assert np.nanmedian(res["iv"].first_stage_f) > 1.0


def test_run_all_writes_a_figure_for_every_exercise(tmp_path):
    out = replications.run_all(tmp_path, quick=True)
    assert set(out) == set(replications.REPLICATIONS)
    for name, payload in out.items():
        assert payload["figures"], f"{name} wrote no figure"
        for path in payload["figures"]:
            assert path.exists() and path.stat().st_size > 0


def test_cli_runs_a_single_exercise(tmp_path, capsys):
    assert replications.main(["bq1989", "--outdir", str(tmp_path)]) == 0
    assert "wrote" in capsys.readouterr().out
