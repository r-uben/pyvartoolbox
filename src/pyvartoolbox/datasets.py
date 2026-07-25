"""The replication datasets shipped with the package.

These are the same series the MATLAB VAR Toolbox uses in its ``Replic/`` folder,
extracted to CSV. They exist so the replications in
:mod:`pyvartoolbox.replications` run from a clean install with no external
downloads, and so the test suite and the replications read identical data rather
than two copies that can drift apart.

Provenance and licence follow the upstream toolbox (GPL-3.0); each series is
public data assembled by the original authors.
"""

from __future__ import annotations

from importlib.resources import files

import numpy as np

#: Variable order in each dataset, as used by the replications.
COLUMNS = {
    "sw2001": ["inflation", "unemployment", "fed funds rate"],
    "bq1989": ["GDP growth", "unemployment"],
    "gk2015": ["1yr rate", "CPI", "IP", "EBP"],
    "jt2025": ["log CPI", "RR shock", "d log GDP", "d log CPI", "d short rate"],
    "jt2025iv": ["unemployment", "fed funds rate", "unemployment", "inflation", "ffr"],
    "uhlig2005": [
        "real GDP",
        "GDP deflator",
        "commodity price",
        "total reserves",
        "nonborrowed reserves",
        "fed funds rate",
    ],
    "adrr2018": [
        "real GDP",
        "GDP deflator",
        "commodity price",
        "total reserves",
        "nonborrowed reserves",
        "fed funds rate",
    ],
}


def load(name: str) -> np.ndarray:
    """Load a shipped dataset by name, e.g. ``load("sw2001")``."""
    path = files("pyvartoolbox.data") / f"{name}.csv"
    with path.open("r") as fh:
        return np.atleast_2d(np.loadtxt(fh, delimiter=",", ndmin=2))


def available() -> list[str]:
    """Names of every shipped CSV."""
    return sorted(
        p.name.removesuffix(".csv")
        for p in files("pyvartoolbox.data").iterdir()
        if p.name.endswith(".csv")
    )
