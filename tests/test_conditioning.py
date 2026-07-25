"""Why the GK2015 fixture is compared at a looser tolerance than the others.

The Gertler and Karadi (2015) design has 12 lags of monthly macro series and 49
regressors. ``cond(X)`` is about 4.7e4, but any solver that forms ``X'X`` — which
is what upstream's ``(X'X) \\ (X'Y)`` does — works with about 2.2e9. That costs
roughly five digits and puts agreement between *any* two implementations at
order 1e-8 rather than 1e-12.

At that level the residual gap is BLAS-ordering noise, not a porting error. It
is genuinely platform-dependent: on macOS/Accelerate reproducing upstream's
normal-equations solver lands closer to MATLAB than QR does, and on
Linux/OpenBLAS the ordering reverses. So these tests deliberately assert only
what is invariant — the size of the gap and the contrast with a well-conditioned
design — and not which solver happens to win.
"""

from pathlib import Path

import numpy as np

from pyvartoolbox import VARmodel
from pyvartoolbox._lag import make_xy

FIXTURES = Path(__file__).parent / "fixtures"


def _load(case: str, name: str) -> np.ndarray:
    if name in ("data", "iv", "narrperiod"):
        from conftest import load_data

        return load_data(f"{case}_{name}")
    return np.atleast_2d(
        np.loadtxt(FIXTURES / f"{case}_{name}.csv", delimiter=",", ndmin=2)
    )


def _normal_equations(y: np.ndarray, nlags: int) -> np.ndarray:
    """Reproduce upstream's solver: residuals from beta = (X'X)^-1 X'Y."""
    Y, X, _ = make_xy(y, nlags, det=1)
    return Y - X @ np.linalg.solve(X.T @ X, X.T @ Y)


def test_squaring_the_design_costs_five_digits():
    """The mechanism, and the one fully deterministic fact here."""
    y = _load("gk2015", "data")
    _, X, _ = make_xy(y, 12, det=1)
    cond_x = np.linalg.cond(X)
    cond_xtx = np.linalg.cond(X.T @ X)
    assert cond_x > 1e4
    assert cond_xtx > 1e8
    assert cond_xtx > cond_x**1.8


def test_both_solvers_agree_with_matlab_to_the_conditioning_floor():
    """Neither solver is meaningfully closer than the other across platforms;
    both land at the level the conditioning permits and nowhere near 1e-12."""
    y = _load("gk2015", "data")
    ref = _load("gk2015", "resid")
    qr_gap = np.abs(VARmodel(y, nlags=12, det=1).resid - ref).max()
    ne_gap = np.abs(_normal_equations(y, 12) - ref).max()
    for gap in (qr_gap, ne_gap):
        assert 1e-12 < gap < 1e-7


def test_the_two_solvers_differ_from_each_other_by_the_same_order():
    """If the gap to MATLAB were a porting error rather than conditioning, two
    correct solvers applied to the same design would still agree closely with
    each other. They do not."""
    y = _load("gk2015", "data")
    qr = VARmodel(y, nlags=12, det=1).resid
    assert 1e-12 < np.abs(qr - _normal_equations(y, 12)).max() < 1e-6


def test_gap_is_negligible_relative_to_the_data():
    y = _load("gk2015", "data")
    ref = _load("gk2015", "resid")
    gap = np.abs(VARmodel(y, nlags=12, det=1).resid - ref).max()
    assert gap / np.abs(ref).max() < 1e-7


def test_well_conditioned_case_shows_no_such_gap():
    """Stock-Watson: 4 lags, benign conditioning. Both solvers agree with the
    reference several orders of magnitude more tightly than GK2015 does, which
    is what identifies conditioning as the cause."""
    y = _load("sw2001", "data")
    ref = _load("sw2001", "resid")
    qr_gap = np.abs(VARmodel(y, nlags=4, det=1).resid - ref).max()
    ne_gap = np.abs(_normal_equations(y, 4) - ref).max()
    assert qr_gap < 1e-11
    assert ne_gap < 1e-11
