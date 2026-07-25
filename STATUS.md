# STATUS — pyvartoolbox

Last updated: 2026-07-25
Stage: beta (v0.2.0) — every roadmap ticket implemented
Repo: https://github.com/r-uben/pyvartoolbox (public, GPL-3.0, CI green)

## Where things stand

146 tests pass on Python 3.11/3.12/3.13; ruff clean.

Tickets 01 and 03-09 are complete. Ticket 02 (replication validation) covers
four of the six upstream exercises; the two outstanding ones are blocked by
randomness, not by missing features.

Validated against MATLAB VAR Toolbox 4.0 via committed fixtures:

| Case | What | Agreement |
| --- | --- | --- |
| Stock-Watson (2001) | Cholesky | 1e-10 to 1e-12 |
| Blanchard-Quah (1989) | long-run zero | 1e-10 to 1e-12 |
| Gertler-Karadi (2015) | proxy SVAR | 1e-7 (conditioning floor) |
| Jorda-Taylor (2025) | local projections | 1e-9 |

Historical decompositions are validated on the first three at the same
tolerances. `tools/make_fixtures.m` regenerates everything under MATLAB R2026a;
`tools/shims/` supplies exact `zscore`/`norminv` definitions so it runs without
the Statistics toolbox.

Not fixture-validated, by necessity: bootstrap bands, sign restrictions,
narrative restrictions, and posterior draws all consume RNG streams numpy cannot
reproduce. Each is tested through its distributional properties instead — Haar
uniformity, the Wishart mean and variance formulas, restriction satisfaction,
and the Kronecker covariance of the coefficient draw.

## Next action

Uhlig (2005) and Antolín-Díaz–Rubio-Ramírez (2018). Neither can be matched
element-by-element, so decide what "validated" means for them first: the honest
options are (a) compare median IRFs within Monte Carlo error at large `ndraws`,
or (b) drive both implementations from an identical externally supplied sequence
of rotation matrices, which upstream's code would need a hook to accept.
Option (b) is a genuine comparison; option (a) is weak. Do not claim either as
equivalent to the 1e-10 results above.

## Outstanding TODOs

1. Uhlig (2005) and ADRR (2018) validation — see above.
2. **Narrative restrictions follow upstream's rejection filter, not the
   importance weighting of the original paper.** The two agree on the support of
   the posterior but not its shape, so results will not reproduce the paper's
   figures. Flagged in README and docstring. Implementing the weighting is a
   real improvement over upstream, not just a port.
3. LP-IV (instrumented local projections) — only the OLS branch of `LPmodel.m`
   is ported.
4. JAX backend for the rotation sampler; only the bootstrap is accelerated
   (8.2x at nboot=2000). The sampler was written as batched draws with an
   acceptance mask specifically so this is a swap, not a rewrite.
5. Bootstrap bias correction (Kilian 1998) — upstream does not apply it either.
6. Decide the pandas question before the API hardens: currently pure-array,
   variable names are the caller's problem.
7. Add `open-source/pyvartoolbox` to `~/repos/.repos.yaml`, regenerate INDEX.md.
8. Email Cesa-Bianchi. Four of his replications now match. Ask whether he
   objects to the `pyvartoolbox` name, which reads as semi-official.
9. Consider publishing to PyPI (name is free).

## Recent decisions

- **2026-07-25** — Standalone GPL-3.0 port rather than an upstream PR. Upstream
  history is two squashed release commits by a single author, and both
  substantive community PRs were closed unmerged.
- **2026-07-25** — numpy is the reference implementation and the default
  everywhere; JAX is optional and scoped to resampling.
- **2026-07-25** — Keep `lstsq` over upstream's normal equations. Matching a
  less accurate reference bit-for-bit is not worth losing accuracy elsewhere.
- **2026-07-25** — Do not assert on which linear-algebra solver lands closer to
  MATLAB; that ordering flips between Accelerate and OpenBLAS. CI caught this
  after I had written the wrong explanation into the docs.
- **2026-07-25** — Backends share their resample draws, generated in numpy, so
  numpy/JAX parity is an exact draw-for-draw comparison rather than a
  distributional one.
- **2026-07-25** — Use `(time/horizon, variable, shock)` ordering everywhere.
  Upstream is inconsistent: `IR` is `(h, variable, shock)` but `VD` and
  `HD.shock` are `(h, shock, variable)`.
- **2026-07-25** — Sign-restriction bands include posterior parameter
  uncertainty by default, matching `SR.m`. `posterior=False` gives the
  identified set alone and is documented as not comparable to published figures.
- **2026-07-25** — Measured JAX speedup is 8.2x, not the order of magnitude
  originally speculated in the README; the README now states the measurement.
