"""Centralised styling: the config drives the figures, not hard-coded values."""

import numpy as np
import pytest

matplotlib = pytest.importorskip("matplotlib")
pytest.importorskip("yaml")
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from pyvartoolbox import VARmodel, plot_irf, use_style  # noqa: E402
from pyvartoolbox.style import (  # noqa: E402
    active_font,
    default_config,
    despine,
    palette,
    settings,
    to_rcparams,
)


@pytest.fixture(autouse=True)
def restore_style():
    yield
    plt.close("all")
    use_style()


class TestConfig:
    def test_ships_with_the_package(self):
        cfg = default_config()
        assert {"font", "axes", "line", "color", "figure", "legend", "savefig"} <= set(
            cfg
        )

    def test_top_and_right_spines_are_off_by_default(self):
        rc = to_rcparams(default_config())
        assert rc["axes.spines.top"] is False
        assert rc["axes.spines.right"] is False
        assert rc["axes.spines.left"] is True
        assert rc["axes.spines.bottom"] is True

    def test_serif_family_is_requested(self):
        rc = to_rcparams(default_config())
        assert rc["font.family"] == "serif"
        assert "Latin Modern Roman" in rc["font.serif"]

    def test_overrides_merge_without_restating_a_section(self):
        cfg = use_style(overrides={"font": {"size": 17.0}})
        assert cfg["font"]["size"] == 17.0
        # Untouched keys in the same section survive.
        assert cfg["font"]["mathtext"] == default_config()["font"]["mathtext"]
        assert matplotlib.rcParams["font.size"] == 17.0

    def test_overrides_do_not_mutate_the_shipped_defaults(self):
        use_style(overrides={"color": {"primary": "#000000"}})
        assert default_config()["color"]["primary"] != "#000000"

    def test_a_replacement_file_is_accepted(self, tmp_path):
        import yaml

        cfg = default_config()
        cfg["figure"]["dpi"] = 77
        path = tmp_path / "house.yaml"
        path.write_text(yaml.safe_dump(cfg))
        assert use_style(path)["figure"]["dpi"] == 77
        assert matplotlib.rcParams["figure.dpi"] == 77

    def test_usetex_without_latex_is_rejected(self, monkeypatch):
        monkeypatch.setattr("shutil.which", lambda _: None)
        with pytest.raises(RuntimeError, match="no `latex` executable"):
            use_style(overrides={"font": {"usetex": True}})


class TestFonts:
    def test_resolves_to_a_configured_family_or_warns(self):
        chosen = active_font()
        # On a machine with TeX installed this should be Latin Modern; the point
        # is that it is one of ours, never a silent DejaVu fallback.
        assert chosen is None or chosen in default_config()["font"]["family"]

    def test_cmr10_disables_unicode_minus(self):
        """cmr10 has no Unicode minus glyph; leaving it enabled emits a warning
        on every negative tick label."""
        cfg = default_config()
        cfg["font"]["family"] = ["cmr10"]
        assert to_rcparams(cfg)["axes.unicode_minus"] is False


class TestAppliedToFigures:
    @pytest.fixture
    def irf(self, y_small):
        return VARmodel(y_small, nlags=2).irf(horizon=8)

    def test_figures_have_no_top_or_right_spine(self, irf):
        use_style()
        fig = plot_irf(irf)
        for ax in fig.axes:
            assert not ax.spines["top"].get_visible()
            assert not ax.spines["right"].get_visible()
            assert ax.spines["left"].get_visible()

    def test_line_colour_comes_from_the_config(self, irf):
        cfg = use_style()
        fig = plot_irf(irf)
        drawn = fig.axes[0].lines[-1].get_color()
        assert matplotlib.colors.to_hex(drawn) == cfg["color"]["primary"].lower()

    def test_changing_the_config_changes_the_figure(self, irf):
        use_style(overrides={"color": {"primary": "#123456"}})
        fig = plot_irf(irf)
        assert matplotlib.colors.to_hex(fig.axes[0].lines[-1].get_color()) == "#123456"

    def test_horizon_ticks_are_integers(self, irf):
        use_style()
        fig = plot_irf(irf)
        ticks = fig.axes[0].get_xticks()
        assert np.allclose(ticks, np.round(ticks))

    def test_panel_size_follows_the_config(self, irf):
        cfg = use_style()
        fig = plot_irf(irf)
        nvar = irf.shape[1]
        expected_h = cfg["figure"]["panel_height"] * nvar
        assert fig.get_size_inches()[1] == pytest.approx(expected_h)

    def test_despine_helper_respects_keep(self):
        _, ax = plt.subplots()
        despine(ax, keep=("bottom",))
        assert not ax.spines["left"].get_visible()
        assert ax.spines["bottom"].get_visible()


def test_palette_is_exposed_and_non_empty():
    assert len(palette()) >= 4
    assert all(c.startswith("#") for c in palette())


def test_settings_applies_defaults_when_unset():
    assert settings()["figure"]["dpi"] > 0
