"""Centralised figure styling, driven by ``config.yaml``.

The YAML file is the single source of truth. Everything that maps onto
matplotlib ``rcParams`` is translated here; the rest — semantic colours, panel
sizing, font-discovery order — is exposed through :func:`settings`.

Why not a ``.mplstyle`` file, which is matplotlib's own mechanism: it can only
express rcParams. It has no way to say "this colour means *confidence band*" or
"an IRF panel is 3.1 by 2.15 inches", both of which the plotting code needs.
Rather than run two config systems, the YAML emits rcParams and holds the rest.

Usage::

    import pyvartoolbox as vt
    vt.use_style()                                  # defaults
    vt.use_style(overrides={"font": {"size": 12}})  # patch
    vt.use_style("house_style.yaml")                # full replacement
"""

from __future__ import annotations

import copy
import warnings
from importlib.resources import files
from pathlib import Path

# Common TeX distribution font directories. Latin Modern usually arrives with a
# TeX install rather than as a system font, so matplotlib will not have indexed
# it even when it is present.
_TEX_FONT_DIRS = (
    "/usr/local/texlive/*/texmf-dist/fonts/opentype/public/lm",
    "/usr/share/texlive/texmf-dist/fonts/opentype/public/lm",
    "/opt/texlive/*/texmf-dist/fonts/opentype/public/lm",
    "~/Library/TinyTeX/texmf-dist/fonts/opentype/public/lm",
    "~/.TinyTeX/texmf-dist/fonts/opentype/public/lm",
    "C:/texlive/*/texmf-dist/fonts/opentype/public/lm",
)

_CACHE: dict | None = None
_FONTS_REGISTERED = False


def _load_yaml(path) -> dict:
    try:
        import yaml
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "styling needs pyyaml; install with pyvartoolbox[plot]"
        ) from exc
    if hasattr(path, "open"):
        with path.open("r") as fh:
            return yaml.safe_load(fh)
    with open(path) as fh:
        return yaml.safe_load(fh)


def _deep_update(base: dict, patch: dict) -> dict:
    """Recursive dict merge, so an override can touch one key without
    restating its whole section."""
    out = copy.deepcopy(base)
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _deep_update(out[key], value)
        else:
            out[key] = value
    return out


def default_config() -> dict:
    """The shipped configuration, as a plain dict."""
    return _load_yaml(files("pyvartoolbox") / "config.yaml")


def register_tex_fonts() -> list[str]:
    """Make Latin Modern visible to matplotlib if a TeX install provides it.

    Returns the font family names that became available. Idempotent, and silent
    when nothing is found — the configured fallbacks then apply.
    """
    global _FONTS_REGISTERED
    if _FONTS_REGISTERED:
        return []
    from glob import glob

    from matplotlib import font_manager as fm

    added = []
    for pattern in _TEX_FONT_DIRS:
        for directory in glob(str(Path(pattern).expanduser())):
            for path in sorted(Path(directory).glob("*.otf")):
                try:
                    fm.fontManager.addfont(str(path))
                    added.append(fm.FontProperties(fname=str(path)).get_name())
                except (RuntimeError, OSError):
                    # A malformed font is not worth failing a plot over.
                    continue
    _FONTS_REGISTERED = True
    return sorted(set(added))


def _resolve_font(candidates: list[str]) -> str | None:
    from matplotlib import font_manager as fm

    available = {f.name for f in fm.fontManager.ttflist}
    for name in candidates:
        if name in available:
            return name
    return None


def to_rcparams(config: dict) -> dict:
    """Translate the configuration into matplotlib rcParams."""
    font, axes = config["font"], config["axes"]
    line, color = config["line"], config["color"]
    fig, legend, save = config["figure"], config["legend"], config["savefig"]

    chosen = _resolve_font(font["family"])
    spines = set(axes["spines"])

    rc = {
        "font.family": "serif",
        "font.serif": font["family"],
        "font.size": font["size"],
        "mathtext.fontset": font["mathtext"],
        "text.usetex": font["usetex"],
        # cmr10 has no proper Unicode minus; without this matplotlib emits a
        # warning on every negative tick label.
        "axes.unicode_minus": chosen not in ("cmr10",),
        "axes.spines.top": "top" in spines,
        "axes.spines.right": "right" in spines,
        "axes.spines.left": "left" in spines,
        "axes.spines.bottom": "bottom" in spines,
        "axes.linewidth": axes["linewidth"],
        "axes.grid": axes["grid"],
        "axes.titlesize": axes["title_size"],
        "axes.titleweight": axes["title_weight"],
        "axes.labelsize": axes["label_size"],
        "axes.prop_cycle": _cycle(color["palette"]),
        "grid.alpha": axes["grid_alpha"],
        "grid.linewidth": axes["grid_linewidth"],
        "xtick.labelsize": axes["tick_size"],
        "ytick.labelsize": axes["tick_size"],
        "xtick.direction": axes["tick_direction"],
        "ytick.direction": axes["tick_direction"],
        "xtick.major.size": axes["tick_length"],
        "ytick.major.size": axes["tick_length"],
        "xtick.major.width": axes["tick_width"],
        "ytick.major.width": axes["tick_width"],
        "lines.linewidth": line["width"],
        "figure.dpi": fig["dpi"],
        "figure.facecolor": fig["facecolor"],
        "legend.frameon": legend["frameon"],
        "legend.fontsize": legend["fontsize"],
        "savefig.dpi": save["dpi"],
        "savefig.bbox": save["bbox"],
        "savefig.pad_inches": save["pad"],
        "savefig.transparent": save["transparent"],
        "savefig.format": save["format"],
    }
    return rc


def _cycle(palette: list[str]):
    from cycler import cycler

    return cycler(color=palette)


def use_style(config=None, overrides: dict | None = None) -> dict:
    """Apply the styling and return the resolved configuration.

    ``config`` may be a path to a replacement YAML file or a dict; ``overrides``
    is a partial patch merged over whatever ``config`` resolves to.
    """
    global _CACHE
    import matplotlib as mpl

    if config is None:
        resolved = default_config()
    elif isinstance(config, dict):
        resolved = copy.deepcopy(config)
    else:
        resolved = _load_yaml(config)

    if overrides:
        resolved = _deep_update(resolved, overrides)

    register_tex_fonts()
    chosen = _resolve_font(resolved["font"]["family"])
    if chosen is None:
        warnings.warn(
            f"none of {resolved['font']['family']} is available; matplotlib will "
            "fall back to its default font",
            RuntimeWarning,
            stacklevel=2,
        )
    if resolved["font"]["usetex"]:
        from shutil import which

        if which("latex") is None:
            raise RuntimeError(
                "font.usetex is true but no `latex` executable is on PATH"
            )

    mpl.rcParams.update(to_rcparams(resolved))
    _CACHE = resolved
    return resolved


def settings() -> dict:
    """The configuration currently in effect, applying the default if unset."""
    if _CACHE is None:
        return use_style()
    return _CACHE


def active_font() -> str | None:
    """Which of the configured families matplotlib actually resolved to.

    Useful in reports and bug reports: a figure that silently fell back to
    DejaVu looks wrong in a way that is hard to attribute.
    """
    register_tex_fonts()
    return _resolve_font(settings()["font"]["family"])


def despine(ax, keep: tuple[str, ...] | None = None) -> None:
    """Hide all spines except ``keep`` (default: left and bottom)."""
    keep = tuple(settings()["axes"]["spines"]) if keep is None else keep
    for name, spine in ax.spines.items():
        spine.set_visible(name in keep)


def palette() -> list[str]:
    """The categorical colour cycle."""
    return list(settings()["color"]["palette"])
