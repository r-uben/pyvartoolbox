"""pyvartoolbox — VAR and local-projection analysis in Python.

An unofficial Python replication of the MATLAB VAR Toolbox (v4.0) by Ambrogio
Cesa-Bianchi, https://github.com/ambropo/VAR-Toolbox. The econometrics and the
design are his; this is a reimplementation in Python, distributed under the
GPL-3.0 as a derivative work.

Not affiliated with, reviewed by, or endorsed by the original author. Cite the
original toolbox in research.
"""

from ._lag import DET_CONST, DET_NONE, DET_TREND, DET_TREND2, make_lags, make_xy
from .bootstrap import BootstrapIRF, bootstrap_irf
from .ident import SCHEMES, impact_matrix
from .model import VARmodel

__version__ = "0.1.0"

__all__ = [
    "VARmodel",
    "bootstrap_irf",
    "BootstrapIRF",
    "impact_matrix",
    "SCHEMES",
    "make_lags",
    "make_xy",
    "DET_NONE",
    "DET_CONST",
    "DET_TREND",
    "DET_TREND2",
    "__version__",
]
