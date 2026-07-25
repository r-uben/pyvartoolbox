"""Matplotlib helpers for the standard VAR figures.

Optional: ``pip install pyvartoolbox[plot]``. Deliberately thin. The arrays this
package returns are plain numpy with an obvious layout, so anyone with a house
style should plot them directly rather than fight a wrapper; these exist to make
the common case one line.

Every function returns the matplotlib ``Figure`` so the caller can restyle it.
"""

from __future__ import annotations

import numpy as np


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


def plot_irf(
    irf: np.ndarray,
    lower: np.ndarray | None = None,
    upper: np.ndarray | None = None,
    var_names=None,
    shock_names=None,
    shocks=None,
    figsize=None,
):
    """Grid of impulse responses, variables down rows and shocks across columns.

    ``irf`` is ``(horizon+1, nvar, nshock)`` as returned by ``VARmodel.irf``.
    Pass ``lower``/``upper`` for shaded bands. ``shocks`` restricts the columns,
    which is what you want under partial identification such as ``ident="iv"``,
    where only shock 0 is meaningful.
    """
    plt = _require_matplotlib()

    nsteps, nvar, nshock = irf.shape
    cols = list(range(nshock)) if shocks is None else list(shocks)
    vnames = _labels(var_names, nvar, "variable")
    snames = _labels(shock_names, nshock, "shock")
    h = np.arange(nsteps)

    figsize = figsize or (3.2 * len(cols) + 1, 2.4 * nvar + 0.5)
    fig, axes = plt.subplots(
        nvar, len(cols), figsize=figsize, squeeze=False, sharex=True
    )

    for r in range(nvar):
        for c, s in enumerate(cols):
            ax = axes[r][c]
            if lower is not None and upper is not None:
                ax.fill_between(h, lower[:, r, s], upper[:, r, s], alpha=0.25)
            ax.plot(h, irf[:, r, s], linewidth=2)
            ax.axhline(0.0, linewidth=0.8, linestyle="--", color="0.4")
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

    nsteps, nvar, nshock = vd.shape
    vnames = _labels(var_names, nvar, "variable")
    snames = _labels(shock_names, nshock, "shock")
    h = np.arange(nsteps)

    figsize = figsize or (4.0 * nvar, 3.2)
    fig, axes = plt.subplots(1, nvar, figsize=figsize, squeeze=False, sharey=True)

    for i in range(nvar):
        ax = axes[0][i]
        ax.stackplot(h, *[vd[:, i, j] for j in range(nshock)], labels=snames)
        ax.set_title(vnames[i])
        ax.set_xlabel("horizon")
        ax.set_ylim(0, 1)
    axes[0][0].set_ylabel("share of forecast error variance")
    axes[0][-1].legend(loc="upper right", fontsize="small")

    fig.tight_layout()
    return fig


def plot_hd(decomp, variable: int = 0, var_names=None, shock_names=None, figsize=None):
    """Stacked-bar historical decomposition of one variable.

    ``decomp`` is a :class:`pyvartoolbox.hd.HistoricalDecomposition`. Positive
    and negative shock contributions stack separately, which is the only way a
    stacked bar reads correctly when contributions have mixed signs.
    """
    plt = _require_matplotlib()

    shock = decomp.shock[:, variable, :]
    mask = ~np.isnan(shock).any(axis=1)
    contrib = shock[mask]
    t = np.flatnonzero(mask)
    nshock = contrib.shape[1]
    snames = _labels(shock_names, nshock, "shock")
    vnames = _labels(var_names, decomp.shock.shape[1], "variable")

    fig, ax = plt.subplots(figsize=figsize or (10, 4))
    pos = np.zeros(len(t))
    neg = np.zeros(len(t))
    for j in range(nshock):
        c = contrib[:, j]
        up, down = np.clip(c, 0, None), np.clip(c, None, 0)
        ax.bar(t, up, bottom=pos, width=1.0, label=snames[j])
        ax.bar(t, down, bottom=neg, width=1.0, color=ax.patches[-1].get_facecolor())
        pos += up
        neg += down

    ax.plot(t, decomp.total[mask, variable], color="black", linewidth=1.5, label="data")
    ax.axhline(0.0, color="0.3", linewidth=0.8)
    ax.set_title(f"Historical decomposition: {vnames[variable]}")
    ax.set_xlabel("observation")
    ax.legend(loc="best", fontsize="small", ncol=2)

    fig.tight_layout()
    return fig
