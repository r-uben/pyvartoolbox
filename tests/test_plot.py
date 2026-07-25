"""Plotting helpers. Structural assertions only — these are not image tests."""

import numpy as np
import pytest

matplotlib = pytest.importorskip("matplotlib")
matplotlib.use("Agg")

from pyvartoolbox import VARmodel, bootstrap_irf  # noqa: E402
from pyvartoolbox.plot import plot_hd, plot_irf, plot_vd  # noqa: E402


@pytest.fixture
def model(y_small):
    return VARmodel(y_small, nlags=2)


@pytest.fixture(autouse=True)
def close_figures():
    yield
    matplotlib.pyplot.close("all")


class TestIRF:
    def test_grid_shape(self, model):
        fig = plot_irf(model.irf(horizon=10))
        assert len(fig.axes) == model.nvar * model.nvar

    def test_bands_add_a_filled_region(self, model):
        b = bootstrap_irf(model, horizon=6, nboot=30, seed=0)
        plain = plot_irf(b.irf)
        banded = plot_irf(b.irf, b.lower, b.upper)
        assert len(banded.axes[0].collections) > len(plain.axes[0].collections)

    def test_shock_subset_narrows_the_grid(self, model):
        fig = plot_irf(model.irf(horizon=6), shocks=[0])
        assert len(fig.axes) == model.nvar

    def test_names_are_applied(self, model):
        fig = plot_irf(
            model.irf(horizon=4),
            var_names=["output", "prices"],
            shock_names=["demand", "supply"],
        )
        assert fig.axes[0].get_title() == "demand"
        assert fig.axes[0].get_ylabel() == "output"

    def test_wrong_name_count_rejected(self, model):
        with pytest.raises(ValueError, match="expected 2 variable names"):
            plot_irf(model.irf(horizon=4), var_names=["only one"])


class TestVD:
    def test_one_panel_per_variable(self, model):
        fig = plot_vd(model.vd(horizon=10))
        # nvar panels plus the legend lives on an existing axis.
        assert len(fig.axes) == model.nvar

    def test_shares_axis_is_bounded(self, model):
        fig = plot_vd(model.vd(horizon=10))
        assert fig.axes[0].get_ylim() == (0.0, 1.0)


class TestHD:
    def test_returns_a_figure_with_a_data_line(self, model):
        fig = plot_hd(model.hd())
        labels = [line.get_label() for line in fig.axes[0].lines]
        assert "data" in labels

    def test_presample_is_dropped(self, model):
        """The first nlags rows are NaN and must not reach the renderer."""
        fig = plot_hd(model.hd())
        xdata = fig.axes[0].lines[0].get_xdata()
        assert xdata.min() >= model.nlags

    def test_variable_selection(self, model):
        fig = plot_hd(model.hd(), variable=1, var_names=["a", "b"])
        assert "b" in fig.axes[0].get_title()


def test_missing_matplotlib_raises_a_useful_error(monkeypatch):
    import builtins

    real = builtins.__import__

    def fake(name, *args, **kwargs):
        if name.startswith("matplotlib"):
            raise ImportError("no matplotlib")
        return real(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake)
    from pyvartoolbox.plot import _require_matplotlib

    with pytest.raises(ImportError, match=r"pyvartoolbox\[plot\]"):
        _require_matplotlib()


def test_hd_contributions_sum_to_the_plotted_data(model):
    """Guards the positive/negative stacking: the bar tops must reconstruct the
    series, which is the property that makes the chart honest."""
    d = model.hd()
    mask = ~np.isnan(d.total[:, 0])
    np.testing.assert_allclose(
        np.nansum(d.shock[mask, 0, :], axis=1)
        + d.init[mask, 0]
        + d.const[mask, 0]
        + d.trend[mask, 0],
        d.total[mask, 0],
        atol=1e-9,
    )
