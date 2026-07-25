"""Why the GK2015 fixture is compared at a looser tolerance than the others.

Upstream solves the OLS system with normal equations, ``(X'X) \\ (X'Y)``. This
package uses ``lstsq`` (QR), which does not square the condition number.

On the Gertler and Karadi (2015) design — 12 lags of monthly macro series, 49
regressors, 384 usable observations — ``cond(X)`` is about 4.7e4 but
``cond(X'X)`` is about 2.2e9. Squaring costs roughly five digits, which puts the
attainable agreement between any two solvers at order 1e-8 rather than 1e-12.

The tests below establish that the residual gap is a property of the design's
conditioning and of upstream's choice of solver, not a porting error. That is
what licenses the looser tolerance for this case in ``test_reference.py``.

Deliberately *not* resolved by switching to normal equations: matching a less
accurate reference bit-for-bit is not worth losing accuracy everywhere else.
"""

from pathlib import Path

import numpy as np

from pyvartoolbox import VARmodel
from pyvartoolbox._lag import make_xy

FIXTURES = Path(__file__).parent / "fixtures"


def _load(case: str, name: str) -> np.ndarray:
    return np.atleast_2d(
        np.loadtxt(FIXTURES / f"{case}_{name}.csv", delimiter=",", ndmin=2)
    )


def _normal_equations(y: np.ndarray, nlags: int) -> np.ndarray:
    """Reproduce upstream's solver: residuals from beta = (X'X)^-1 X'Y."""
    Y, X, _ = make_xy(y, nlags, det=1)
    return Y - X @ np.linalg.solve(X.T @ X, X.T @ Y)


def test_squaring_the_design_costs_five_digits():
    y = _load("gk2015", "data")
    _, X, _ = make_xy(y, 12, det=1)
    cond_x = np.linalg.cond(X)
    cond_xtx = np.linalg.cond(X.T @ X)
    assert cond_x > 1e4
    assert cond_xtx > 1e8
    # The whole point: forming X'X roughly squares the conditioning.
    assert cond_xtx > cond_x**1.8


def test_normal_equations_land_closer_to_matlab_than_qr():
    """The evidence that the gap is solver-driven. Reproducing upstream's own
    solver moves materially toward its answer; if the port were wrong, changing
    the solver would not help."""
    y = _load("gk2015", "data")
    ref = _load("gk2015", "resid")
    qr_gap = np.abs(VARmodel(y, nlags=12, det=1).resid - ref).max()
    ne_gap = np.abs(_normal_equations(y, 12) - ref).max()
    assert ne_gap < qr_gap
    # Neither matches exactly: MATLAB's backslash on X'X uses its own
    # factorisation and BLAS ordering, so bit-identity is not attainable.
    assert 0 < ne_gap < 1e-8
    assert 0 < qr_gap < 1e-7


def test_gap_is_negligible_relative_to_the_data():
    y = _load("gk2015", "data")
    ref = _load("gk2015", "resid")
    gap = np.abs(VARmodel(y, nlags=12, det=1).resid - ref).max()
    assert gap / np.abs(ref).max() < 1e-7


def test_well_conditioned_case_shows_no_such_gap():
    """Stock-Watson: 4 lags, benign conditioning, so QR and normal equations
    agree to machine precision and both match the reference exactly."""
    y = _load("sw2001", "data")
    qr_resid = VARmodel(y, nlags=4, det=1).resid
    np.testing.assert_allclose(qr_resid, _normal_equations(y, 4), rtol=0, atol=1e-12)
    np.testing.assert_allclose(qr_resid, _load("sw2001", "resid"), rtol=0, atol=1e-12)
