"""Matplotlib helpers for the standard VAR figures.

Optional: ``uv add "pyvartoolbox[plot]"``. All appearance is centralised in
``config.yaml`` and applied through :mod:`pyvartoolbox.style` — nothing here
hard-codes a colour, size or font. To restyle every figure, edit that file or
call :func:`pyvartoolbox.use_style` with an override; do not patch this module.

Every function returns the matplotlib ``Figure``, so anything not covered by the
configuration remains adjustable by the caller.
"""

from __future__ import annotations

import numpy as np

from .style import despine, settings


def _require_matplotlib():
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:  # pragma: no cover - exercised by the error path
        raise ImportError(
            "plotting needs matplotlib; install with pyvartoolbox[plot]"
        ) from exc
    return plt


def _labels(names, n, prefix):
    if names is None:
        return [f"{prefix} {i + 1}" for i in range(n)]
    if len(names) != n:
        raise ValueError(f"expected {n} {prefix} names, got {len(names)}")
    return list(names)


def _zero_line(ax, cfg):
    ax.axhline(
        0.0,
        color=cfg["line"]["zero_color"],
        linewidth=cfg["line"]["zero_width"],
        linestyle=cfg["line"]["zero_style"],
        zorder=1,
    )


def _integer_axis(ax):
    """Horizons are integers; the default locator invents 2.5-period ticks."""
    from matplotlib.ticker import MaxNLocator

    ax.xaxis.set_major_locator(MaxNLocator(integer=True, nbins="auto"))


def _grid_size(cfg, ncols, nrows):
    return (
        cfg["figure"]["panel_width"] * ncols + cfg["figure"]["label_pad"],
        cfg["figure"]["panel_height"] * nrows,
    )


def plot_irf(
    irf: np.ndarray,
    lower: np.ndarray | None = None,
    upper: np.ndarray | None = None,
    var_names=None,
    shock_names=None,
    shocks=None,
    figsize=None,
    color=None,
):
    """Grid of impulse responses, variables down rows and shocks across columns.

    ``irf`` is ``(horizon+1, nvar, nshock)`` as returned by ``VARmodel.irf``.
    Pass ``lower``/``upper`` for shaded bands. ``shocks`` restricts the columns,
    which is what you want under partial identification such as ``ident="iv"``,
    where only shock 0 is meaningful.
    """
    plt = _require_matplotlib()
    cfg = settings()
    color = color or cfg["color"]["primary"]

    nsteps, nvar, nshock = irf.shape
    cols = list(range(nshock)) if shocks is None else list(shocks)
    vnames = _labels(var_names, nvar, "variable")
    snames = _labels(shock_names, nshock, "shock")
    h = np.arange(nsteps)

    fig, axes = plt.subplots(
        nvar,
        len(cols),
        figsize=figsize or _grid_size(cfg, len(cols), nvar),
        squeeze=False,
        sharex=True,
    )

    for r in range(nvar):
        for c, s in enumerate(cols):
            ax = axes[r][c]
            _zero_line(ax, cfg)
            if lower is not None and upper is not None:
                ax.fill_between(
                    h,
                    lower[:, r, s],
                    upper[:, r, s],
                    color=color,
                    alpha=cfg["color"]["band_alpha"],
                    linewidth=0,
                    zorder=2,
                )
            ax.plot(h, irf[:, r, s], color=color, zorder=3)
            ax.margins(x=0)
            _integer_axis(ax)
            despine(ax)
            if r == 0:
                ax.set_title(snames[s])
            if c == 0:
                ax.set_ylabel(vnames[r])
            if r == nvar - 1:
                ax.set_xlabel("horizon")

    fig.tight_layout()
    return fig


def plot_vd(vd: np.ndarray, var_names=None, shock_names=None, figsize=None):
    """Stacked-area forecast error variance decomposition, one panel per variable.

    ``vd`` is ``(horizon+1, nvar, nshock)`` in shares, as returned by
    ``VARmodel.vd``.
    """
    plt = _require_matplotlib()
    cfg = settings()
    colors = cfg["color"]["palette"]

    nsteps, nvar, nshock = vd.shape
    vnames = _labels(var_names, nvar, "variable")
    snames = _labels(shock_names, nshock, "shock")
    h = np.arange(nsteps)

    fig, axes = plt.subplots(
        1,
        nvar,
        figsize=figsize or _grid_size(cfg, nvar, 1.4),
        squeeze=False,
        sharey=True,
    )

    for i in range(nvar):
        ax = axes[0][i]
        ax.stackplot(
            h,
            *[vd[:, i, j] for j in range(nshock)],
            labels=snames,
            colors=[colors[j % len(colors)] for j in range(nshock)],
            edgecolor="none",
        )
        ax.set_title(vnames[i])
        ax.set_xlabel("horizon")
        ax.set_ylim(0, 1)
        ax.margins(x=0)
        _integer_axis(ax)
        despine(ax)
    axes[0][0].set_ylabel("share of forecast error variance")
    axes[0][-1].legend(loc="upper right")

    fig.tight_layout()
    return fig


def plot_hd(decomp, variable: int = 0, var_names=None, shock_names=None, figsize=None):
    """Stacked-bar historical decomposition of one variable.

    ``decomp`` is a :class:`pyvartoolbox.hd.HistoricalDecomposition`. Positive
    and negative shock contributions stack separately, which is the only way a
    stacked bar reads correctly when contributions have mixed signs.
    """
    plt = _require_matplotlib()
    cfg = settings()
    colors = cfg["color"]["palette"]

    shock = decomp.shock[:, variable, :]
    mask = ~np.isnan(shock).any(axis=1)
    contrib = shock[mask]
    t = np.flatnonzero(mask)
    nshock = contrib.shape[1]
    snames = _labels(shock_names, nshock, "shock")
    vnames = _labels(var_names, decomp.shock.shape[1], "variable")

    fig, ax = plt.subplots(
        figsize=figsize
        or (cfg["figure"]["panel_width"] * 3, cfg["figure"]["panel_height"] * 1.6)
    )
    pos = np.zeros(len(t))
    neg = np.zeros(len(t))
    for j in range(nshock):
        c = contrib[:, j]
        up, down = np.clip(c, 0, None), np.clip(c, None, 0)
        col = colors[j % len(colors)]
        ax.bar(t, up, bottom=pos, width=1.0, color=col, label=snames[j], linewidth=0)
        ax.bar(t, down, bottom=neg, width=1.0, color=col, linewidth=0)
        pos += up
        neg += down

    ax.plot(
        t,
        decomp.total[mask, variable],
        color="black",
        linewidth=cfg["line"]["width"] * 0.8,
        label="data",
    )
    _zero_line(ax, cfg)
    ax.set_title(f"Historical decomposition: {vnames[variable]}")
    ax.set_xlabel("observation")
    ax.margins(x=0)
    despine(ax)
    ax.legend(loc="best", ncol=2)

    fig.tight_layout()
    return fig


def plot_lp(lp, title: str | None = None, figsize=None, color=None):
    """Single local-projection response with its Newey-West band."""
    plt = _require_matplotlib()
    cfg = settings()
    color = color or cfg["color"]["primary"]

    h = np.arange(len(lp.ir))
    fig, ax = plt.subplots(
        figsize=figsize
        or (cfg["figure"]["panel_width"] * 1.6, cfg["figure"]["panel_height"] * 1.3)
    )
    _zero_line(ax, cfg)
    ax.fill_between(
        h,
        lp.lower,
        lp.upper,
        color=color,
        alpha=cfg["color"]["band_alpha"],
        linewidth=0,
    )
    ax.plot(h, lp.ir, color=color)
    ax.margins(x=0)
    _integer_axis(ax)
    despine(ax)
    ax.set_xlabel("horizon")
    if title:
        ax.set_title(title)
    fig.tight_layout()
    return fig
