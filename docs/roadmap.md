# Roadmap

Ordered by what unblocks what. The numbering is stable; branches use
`feat/NN-slug`.

## 01 — Core reduced-form VAR ✅ (v0.1.0)

OLS estimation, deterministic and exogenous terms, companion form, stability,
Wold representation, Cholesky and long-run identification, IRF, VD, residual and
wild bootstrap bands.

## 02 — Replication validation (ongoing)

The upstream `Replic/` folder ships six replications. Matching them numerically
is the entire credibility claim of this port.

Machinery is in place: `tools/make_fixtures.m` drives the MATLAB toolbox and
writes full-precision CSVs, `tests/test_reference.py` asserts against them, and
the fixtures are committed so CI needs no licence. See `docs/fixtures.md`.

Done:

- Stock and Watson (2001) — Cholesky ✅
- Blanchard and Quah (1989) — long-run zero restrictions ✅

Each remaining replication is validated as part of the ticket that implements
its scheme, by adding a case to `make_fixtures.m`:

- Gertler and Karadi (2015) → ticket 04 ✅
- Uhlig (2005) → ticket 05
- Antolín-Díaz and Rubio-Ramírez (2018) → ticket 06
- Jordà and Taylor (2025) → ticket 08

Note that 05 and 06 are rejection samplers, so they cannot be matched
element-by-element across RNG streams. Validate the deterministic core (the
rotation-to-IRF map given a fixed `Q`, and that accepted draws satisfy the sign
pattern), plus a loose statistical comparison of median IRFs.

## 03 — Historical decompositions ✅

Port `compute_HD.m`. Needs the structural shock series and the initial-condition
handling, which the upstream code splits into deterministic, initial-condition,
and shock contributions.

## 04 — External instruments (proxy SVAR) ✅

Port `recover_B.m`'s IV branch. This plus 06 is the main gap versus
`statsmodels` and the strongest reason for the package to exist. Ordering it
before sign restrictions because it is deterministic and cheap — no sampling
layer, so it needs no JAX work to be usable.

## 05 — Sign restrictions ✅ (with posterior draws)

Port `SR.m` / `SignRestrictions.m`: draw an orthonormal `Q` by QR of a Gaussian
matrix, rotate the Cholesky factor, keep draws satisfying the sign pattern.

Design constraint to respect from the start: acceptance is data-dependent
control flow, which does not `jit`. Structure it as fixed-size batched draws
with a boolean acceptance mask, not an early-exit loop, so the JAX backend in 07
is a backend swap rather than a rewrite.

## 06 — Narrative sign restrictions ✅

Antolín-Díaz and Rubio-Ramírez (2018): adds importance weighting over accepted
draws. Depends on 05.

## 07 — JAX backend ✅ (bootstrap; rotation sampler outstanding)

Only for the resampling layers, behind the same public API:

- bootstrap replications — `vmap` + `jit` over the resample-and-re-estimate step
- sign-restriction rejection sampling — `vmap` over batched rotations

Non-goals: JITing the estimator itself (one small `lstsq`), or the IRF recursion
over horizons (sequential; `lax.scan` at best, and not the bottleneck).

**Must set `jax_enable_x64` at import.** float32 silently corrupts long-horizon
IRFs and long-run restrictions, both of which run through ill-conditioned
matrices.

Acceptance criterion: numpy and JAX backends agree to 1e-10 on the 02 fixtures
under a fixed seed, and the JAX path is measurably faster at `nboot >= 1000`.

## 08 — Local projections ✅ (OLS branch; LP-IV outstanding)

Port `LPmodel.m`: OLS and IV local projections with Newey–West standard errors.
Independent of 03–07; can be done in parallel.

## 09 — Plotting

Thin matplotlib helpers mirroring `VARirplot` / `VARhdplot` / `VARvdplot`.
Optional dependency. Deliberately last: it is the most code for the least
scientific value, and users can plot `(horizon, nvar, nshock)` arrays themselves.

## Deliberately out of scope

- `Stats/`, `Utils/`, `Figure/` — numpy, pandas and matplotlib already cover
  these; porting them would be re-implementing the standard library.
- Lag-order selection criteria — `statsmodels` has them and they compose fine.
- Bayesian VARs — different package.

## Open questions

- Bootstrap bias correction (Kilian 1998). Upstream does not apply it by
  default; should this?
- Whether to accept a pandas `DataFrame` and carry variable names through, or
  stay pure-array. Currently pure-array, names are the caller's problem.
