"""End-to-end replications of the six exercises in the MATLAB toolbox's ``Replic/``.

Each function reproduces one exercise from a clean install and returns its
results; ``run_all`` writes figures for every one. This is a different claim from
the fixture tests: those assert that our numbers equal MATLAB's on identical
specifications, while these demonstrate the whole pipeline — data in, estimated
model, identification, inference, figure out — actually works.

Where an exercise uses a sampler (Uhlig, ADRR) or a bootstrap, results are not
reproducible against MATLAB draw-for-draw; see the README. The point estimates
underneath them are.

Run from the command line:

    pyvartoolbox-replicate all --outdir figures
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from .datasets import load
from .lp import local_projection
from .model import VARmodel
from .sign import NarrativeDominance, NarrativeSign, sign_restricted_irf

# Column 0 is a contractionary monetary policy shock: it raises the funds rate
# and lowers the deflator, commodity prices and nonborrowed reserves. Shared by
# Uhlig (2005) and Antolin-Diaz and Rubio-Ramirez (2018).
MONETARY_SIGN = np.array(
    [
        [0.0], [-1.0], [-1.0], [0.0], [-1.0], [1.0],
    ]
)


def stock_watson_2001(nboot: int = 500, seed: int = 0) -> dict:
    """Cholesky identification in a trivariate quarterly VAR (Figure 1, Table 1.B)."""
    from .bootstrap import bootstrap_irf

    y = load("sw2001_data")
    m = VARmodel(y, nlags=4, det=1)
    bands = bootstrap_irf(m, horizon=23, nboot=nboot, ci=0.90, seed=seed)
    vd = m.vd(horizon=23)
    # Table 1.B reports the decomposition at horizons 1, 4, 8 and 12 quarters.
    table = {h: vd[h - 1] * 100 for h in (1, 4, 8, 12)}
    return {"model": m, "bands": bands, "vd": vd, "table_1b": table}


def blanchard_quah_1989() -> dict:
    """Long-run zero restrictions: supply and demand shocks (Figures 1 and 2)."""
    y = load("bq1989_data")
    m = VARmodel(y, nlags=8, det=1)
    irf = m.irf(horizon=39, ident="longrun")
    # The paper plots cumulated responses; by construction the cumulated
    # response of output to the demand shock vanishes.
    return {"model": m, "irf": irf, "cumulative": irf.cumsum(axis=0)}


def gertler_karadi_2015() -> dict:
    """Proxy SVAR versus Cholesky for a monetary policy shock."""
    y = load("gk2015_data")
    z = load("gk2015_iv")
    m = VARmodel(y, nlags=12, det=1)
    return {
        "model": m,
        "irf_chol": m.irf(horizon=47, ident="chol"),
        "irf_iv": m.irf(horizon=47, ident="iv", iv=z),
    }


def uhlig_2005(ndraws: int = 200, seed: int = 0) -> dict:
    """Sign restrictions on a monetary policy shock (Figure 6)."""
    y = load("uhlig2005_data")
    m = VARmodel(y, nlags=12, det=1)
    res = sign_restricted_irf(
        m,
        MONETARY_SIGN,
        horizon=59,
        ndraws=ndraws,
        sr_hor=6,
        ci=0.68,
        seed=seed,
    )
    return {"model": m, "result": res}


def antolin_diaz_rubio_ramirez_2018(ndraws: int = 200, seed: int = 0) -> dict:
    """Narrative sign restrictions, October 1979 (Figures 5 and 6)."""
    y = load("adrr2018_data")
    period = int(load("adrr2018_narrperiod")[0, 0]) - 1
    # The paper excludes the constant.
    m = VARmodel(y, nlags=12, det=0)
    narrative = [
        NarrativeSign(period=period, shock=0, sign=1),
        NarrativeDominance(period=period, shock=0, variable=5),
    ]
    plain = sign_restricted_irf(
        m, MONETARY_SIGN, horizon=59, ndraws=ndraws, sr_hor=6, ci=0.68, seed=seed
    )
    narr = sign_restricted_irf(
        m,
        MONETARY_SIGN,
        horizon=59,
        ndraws=ndraws,
        sr_hor=6,
        ci=0.68,
        seed=seed,
        narrative=narrative,
    )
    return {"model": m, "sign_only": plain, "narrative": narr}


def jorda_taylor_2025() -> dict:
    """Local projections, OLS and IV (Figures 5a and 6a)."""
    ols_data = load("jt2025_data")
    ols = local_projection(
        endo=ols_data[:, 0],
        treat=ols_data[:, 1],
        ctrl=ols_data[:, 2:],
        nlags=4,
        horizon=17,
        unit_shock=True,
        long_diff=True,
    )

    iv_data = load("jt2025iv_data")
    instr = load("jt2025iv_iv").ravel()
    iv = local_projection(
        endo=iv_data[:, 0],
        treat=iv_data[:, 1],
        ctrl=iv_data[:, 2:],
        nlags=6,
        horizon=48,
        unit_shock=True,
        long_diff=True,
        iv=instr,
        nlags_iv=6,
    )
    return {"ols": ols, "iv": iv}


REPLICATIONS = {
    "sw2001": stock_watson_2001,
    "bq1989": blanchard_quah_1989,
    "gk2015": gertler_karadi_2015,
    "uhlig2005": uhlig_2005,
    "adrr2018": antolin_diaz_rubio_ramirez_2018,
    "jt2025": jorda_taylor_2025,
}


def _save(fig, outdir: Path, name: str) -> Path:
    outdir.mkdir(parents=True, exist_ok=True)
    path = outdir / f"{name}.png"
    fig.savefig(path, dpi=130, bbox_inches="tight")
    return path


def plot(name: str, result: dict, outdir: Path) -> list[Path]:
    """Render an exercise's headline figure(s)."""
    import matplotlib.pyplot as plt

    from .plot import plot_irf

    written = []
    if name == "sw2001":
        b = result["bands"]
        written.append(
            _save(_lbl(plot_irf(b.irf, b.lower, b.upper), "sw2001"), outdir, "sw2001_irf")
        )
    elif name == "bq1989":
        written.append(
            _save(_lbl(plot_irf(result["cumulative"]), "bq1989"), outdir, "bq1989_cumirf")
        )
    elif name == "gk2015":
        written.append(
            _save(
                _lbl(plot_irf(result["irf_iv"], shocks=[0]), "gk2015"),
                outdir,
                "gk2015_proxy_irf",
            )
        )
    elif name in ("uhlig2005", "adrr2018"):
        res = result["result"] if name == "uhlig2005" else result["narrative"]
        written.append(
            _save(
                _lbl(plot_irf(res.median, res.lower, res.upper, shocks=[0]), name),
                outdir,
                f"{name}_irf",
            )
        )
    elif name == "jt2025":
        fig, axes = plt.subplots(1, 2, figsize=(11, 4))
        for ax, key, title in zip(
            axes, ("ols", "iv"), ("LP-OLS: CPI", "LP-IV: unemployment"), strict=True
        ):
            lp = result[key]
            h = np.arange(len(lp.ir))
            ax.fill_between(h, lp.lower, lp.upper, alpha=0.25)
            ax.plot(h, lp.ir, linewidth=2)
            ax.axhline(0, linestyle="--", linewidth=0.8, color="0.4")
            ax.set_title(title)
            ax.set_xlabel("horizon")
        fig.tight_layout()
        written.append(_save(fig, outdir, "jt2025_lp"))
    return written


def _lbl(fig, name: str):
    """Attach variable names to an IRF grid when we know them."""
    from .datasets import COLUMNS

    names = COLUMNS.get(name)
    if names:
        for ax, label in zip(fig.axes, names, strict=False):
            if ax.get_ylabel():
                ax.set_ylabel(label)
    return fig


def run_all(outdir: Path, quick: bool = False) -> dict:
    """Run every replication and write its figures. Returns the raw results."""
    out = {}
    for name, fn in REPLICATIONS.items():
        kwargs = {}
        if quick and name in ("uhlig2005", "adrr2018"):
            kwargs["ndraws"] = 20
        if quick and name == "sw2001":
            kwargs["nboot"] = 50
        result = fn(**kwargs)
        out[name] = {"result": result, "figures": plot(name, result, outdir)}
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="pyvartoolbox-replicate",
        description="Reproduce the six replication exercises of the MATLAB VAR Toolbox.",
    )
    parser.add_argument(
        "name",
        nargs="?",
        default="all",
        choices=["all", *REPLICATIONS],
        help="which exercise to run (default: all)",
    )
    parser.add_argument(
        "--outdir", type=Path, default=Path("figures"), help="where to write figures"
    )
    parser.add_argument(
        "--quick", action="store_true", help="fewer draws; for smoke-testing"
    )
    args = parser.parse_args(argv)

    names = list(REPLICATIONS) if args.name == "all" else [args.name]
    for name in names:
        kwargs = {}
        if args.quick and name in ("uhlig2005", "adrr2018"):
            kwargs["ndraws"] = 20
        if args.quick and name == "sw2001":
            kwargs["nboot"] = 50
        result = REPLICATIONS[name](**kwargs)
        for path in plot(name, result, args.outdir):
            print(f"{name}: wrote {path}")

        if name == "sw2001":
            print("\nStock and Watson (2001) Table 1.B — variance shares (%)")
            print(f"{'horizon':>8} {'inflation':>10} {'unemp':>10} {'ffr':>10}")
            for h, block in result["table_1b"].items():
                # Own-shock share of each variable's forecast error variance.
                print(
                    f"{h:>8} "
                    + " ".join(f"{block[i, i]:>10.1f}" for i in range(block.shape[0]))
                )
    return 0
