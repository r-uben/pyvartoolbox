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
| `sigma`, impact matrix `B`, residuals, IRFs (sw2001, bq1989) | 1e-10 to 1e-12 absolute |
| variance decompositions (sw2001, bq1989) | 1e-8 absolute (percent scale) |
| everything for gk2015 | 1e-7 absolute — see the note below |

## Tolerance note: GK2015

The Gertler-Karadi case is asserted at 1e-7, not 1e-10. This is not slack for a
suspected bug — `tests/test_conditioning.py` pins the cause.

The design has 12 lags of monthly data and 49 regressors, giving `cond(X)` about
4.7e4 and `cond(X'X)` about 2.2e9. Upstream solves via normal equations, which
forms `X'X` and so works with the squared conditioning; this package uses
`lstsq`. That costs roughly five digits and puts agreement between any two
implementations at order 1e-8 rather than 1e-12.

At that level the difference is BLAS-ordering noise. It is platform-dependent:
on macOS/Accelerate, reproducing upstream's normal-equations solver in numpy
lands closer to MATLAB than QR does; on Linux/OpenBLAS the ordering reverses.
The evidence that this is conditioning rather than a porting error is the
contrast with Stock-Watson, where 4 lags and benign conditioning let both
solvers match the reference to better than 1e-11.

The package keeps `lstsq`. Matching a less accurate reference bit-for-bit is not
worth losing accuracy on every other design.

## MATLAB toolbox dependencies

`LPmodel.m` calls `zscore` and `norminv`, both from the Statistics and Machine
Learning Toolbox. Without that licence local projections cannot run at all, so
`tools/shims/` supplies exact standard definitions (`norminv` via base MATLAB's
`erfinv`, `zscore` as `(x-mean)/std(x,0)`) that `make_fixtures.m` puts on the
path. With the toolbox licensed, drop the `addpath` line — the fixtures are
identical either way, which is why the shims use exact identities rather than
approximations.

Noted while porting: `LPmodel.m` passes t-statistics to `tdis_prb` without the
finite-value guard that `OLSmodel.m` has, so a specification that produces a
non-finite t-statistic fails inside `betainc` rather than returning NaN.

## Case: jt2025

Reproduces `GO_JT2025.m` section 2 — Jorda and Taylor (2025), CPI response to a
Romer-Romer shock, 1985q1-2007q4, 4 lags, constant, long-difference LHS, unit
shock, 18 horizons, 95% bands. Impulse responses, Newey-West standard errors,
and both bands agree to 1e-9.

## Cases: uhlig2005 and adrr2018

Both are rejection samplers, so they are validated differently from the rest —
see the README section "The two set-identified replications, validated
differently".

Generated with `VARopt.inference = 0`, so every rotation is taken around the
point estimate rather than a posterior draw; that is what makes the accepted
matrices reproducible targets. The fixtures store `SRout.Ball`, the impact
matrices MATLAB accepted (200 each), plus `IRall` for the first 10 Uhlig draws —
truncated because the full array is ~8 MB and the marginal validation value of
draws 11-200 is nil.

`adrr2018` uses `detc = 0`: the paper excludes the constant. A silently added
constant would shift every residual and invalidate the narrative checks, so
there is a test asserting the specification.
