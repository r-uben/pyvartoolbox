"""Validation against the MATLAB VAR Toolbox 4.0.

Fixtures in ``tests/fixtures/`` were produced by running the upstream toolbox on
its own replication datasets (MATLAB R2026a, ``VARopt.inference = 0`` so the
values are deterministic), and are committed so CI needs no MATLAB licence. The
generator lives in ``docs/fixtures.md``.

Cases:

``sw2001``
    Stock and Watson (2001), trivariate quarterly VAR, 4 lags, constant,
    Cholesky identification, 24 horizons.
``bq1989``
    Blanchard and Quah (1989), bivariate VAR, 8 lags, constant, long-run zero
    restrictions, 40 horizons.

Two known convention differences, both deliberate:

- Upstream reports variance decompositions in percent; this package reports
  shares in ``[0, 1]``.
- Upstream's ``IR`` has ``nsteps`` rows covering horizons ``0 .. nsteps-1``;
  ``VARmodel.irf(horizon=h)`` returns ``h + 1`` rows covering ``0 .. h``.
- Upstream indexes ``IR(h, variable, shock)`` but ``VD(h, shock, variable)``
  (see the header of ``compute_VD.m``). This package uses
  ``(h, variable, shock)`` for both, so the VD fixture is transposed on load.
"""

from pathlib import Path

import numpy as np
import pytest

from pyvartoolbox import VARmodel

FIXTURES = Path(__file__).parent / "fixtures"

CASES = {
    "sw2001": {"nlags": 4, "ident": "chol"},
    "bq1989": {"nlags": 8, "ident": "longrun"},
}


def _load(case: str, name: str) -> np.ndarray:
    return np.atleast_2d(
        np.loadtxt(FIXTURES / f"{case}_{name}.csv", delimiter=",", ndmin=2)
    )


def _load3d(case: str, name: str) -> np.ndarray:
    """Rebuild a 3-D array flattened by MATLAB's column-major ``reshape``."""
    flat = _load(case, name)
    ns, nv, nsh = _load(case, f"{name}shape")[0].astype(int)
    return flat.reshape(ns, nv, nsh, order="F")


@pytest.fixture(params=sorted(CASES))
def case(request):
    name = request.param
    spec = CASES[name]
    y = _load(name, "data")
    model = VARmodel(y, nlags=spec["nlags"], det=1)
    return name, spec, model


class TestAgainstMatlab:
    """Everything compared here is invariant to the coefficient layout, so a
    mismatch means a numerical disagreement rather than a reshaping artefact."""

    def test_residual_covariance(self, case):
        name, _, m = case
        np.testing.assert_allclose(m.sigma, _load(name, "sigma"), rtol=0, atol=1e-12)

    def test_residuals(self, case):
        name, _, m = case
        np.testing.assert_allclose(m.resid, _load(name, "resid"), rtol=0, atol=1e-10)

    def test_impact_matrix(self, case):
        name, spec, m = case
        from pyvartoolbox.ident import impact_matrix

        np.testing.assert_allclose(
            impact_matrix(m, spec["ident"]), _load(name, "B"), rtol=0, atol=1e-12
        )

    def test_impulse_responses(self, case):
        name, spec, m = case
        ref = _load3d(name, "IR")
        nsteps = ref.shape[0]
        got = m.irf(horizon=nsteps - 1, ident=spec["ident"])
        np.testing.assert_allclose(got, ref, rtol=0, atol=1e-10)

    def test_variance_decomposition(self, case):
        name, spec, m = case
        # Upstream is percent and (h, shock, variable); ours is share and
        # (h, variable, shock).
        ref = _load3d(name, "VD").transpose(0, 2, 1)
        nsteps = ref.shape[0]
        got = m.vd(horizon=nsteps - 1, ident=spec["ident"]) * 100.0
        np.testing.assert_allclose(got, ref, rtol=0, atol=1e-9)


def test_fixtures_cover_both_identification_schemes():
    """Guard against a fixture silently disappearing and the suite still passing."""
    assert {spec["ident"] for spec in CASES.values()} == {"chol", "longrun"}
    for name in CASES:
        assert (FIXTURES / f"{name}_IR.csv").exists()
