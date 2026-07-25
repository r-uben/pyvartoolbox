# Reference fixtures

`tests/fixtures/*.csv` are reference values produced by the **MATLAB VAR Toolbox
4.0**, not by this package. They are what `tests/test_reference.py` asserts
against, and they are the reason the port can claim to be correct rather than
merely self-consistent.

They are committed so that CI needs no MATLAB licence.

## Regenerating

```bash
git clone --depth 1 https://github.com/ambropo/VAR-Toolbox.git
# place tools/make_fixtures.m next to the clone, then:
/Applications/MATLAB_R2026a.app/bin/matlab -batch "run('make_fixtures.m')"
cp fixtures/*.csv <repo>/tests/fixtures/
```

Generated with MATLAB R2026a against upstream `main` at v4.0.

## Why these settings

- `VARopt.inference = 0` — point estimates only. Bootstrap bands depend on
  MATLAB's RNG stream, which cannot be reproduced in numpy, so committing them
  would produce a fixture nothing could ever match. Bootstrap correctness is
  tested by its own statistical properties in `test_bootstrap.py` instead.
- `VARopt.impact = 0` — one-standard-deviation shocks, the package default.
- `VARopt.recurs = 'wold'` — the Wold recursion rather than companion powers.
  `test_model.py` separately asserts the two agree, so this is not a loophole.
- Values are written at `%.17g`, i.e. full float64 round-trip precision. The
  default `writematrix` gives 5 significant digits, which would silently cap the
  achievable tolerance at ~1e-5 and make the comparison meaningless.

## Cases

| Fixture | Source | Spec | Identification |
| --- | --- | --- | --- |
| `sw2001` | Stock and Watson (2001) | 3 vars, 4 lags, constant, 24 horizons | Cholesky |
| `bq1989` | Blanchard and Quah (1989) | 2 vars, 8 lags, constant, 40 horizons | long-run zero |

## Convention differences, deliberate

Recorded here because each one looks like a bug the first time you hit it.

1. **Variance decomposition scale.** Upstream reports percent; this package
   reports shares in `[0, 1]`.
2. **Variance decomposition axis order.** Upstream indexes `IR(h, variable,
   shock)` but `VD(h, shock, variable)` — see the header of `compute_VD.m`.
   This package uses `(h, variable, shock)` for both.
3. **Horizon count.** Upstream's `nsteps` rows cover horizons `0 .. nsteps-1`;
   `irf(horizon=h)` returns `h + 1` rows covering `0 .. h`.
4. **Coefficient layout.** Upstream puts deterministic terms first; this package
   appends them after the lag block. This is why the tests compare `sigma`,
   `resid`, `B`, `IR` and `VD` — all layout-invariant — and never raw
   coefficient vectors.

## Achieved tolerances

| Quantity | Tolerance |
| --- | --- |
| `sigma`, impact matrix `B` | 1e-12 absolute |
| residuals, IRFs | 1e-10 absolute |
| variance decompositions | 1e-9 absolute (on the percent scale) |
