# STATUS — pyvartoolbox

Last updated: 2026-07-25
Stage: beta (v0.4.0) — feature-complete against upstream; all six replications validated
Repo: https://github.com/r-uben/pyvartoolbox (public, GPL-3.0, CI green)

## Where things stand

161 tests pass on Python 3.11/3.12/3.13; ruff clean.

All nine roadmap tickets are closed, including ticket 02: every one of the six
upstream replications is now validated, though not all to the same strength.

### Exact, against MATLAB VAR Toolbox 4.0

| Case | What | Agreement |
| --- | --- | --- |
| Stock-Watson (2001) | Cholesky | 1e-10 to 1e-12 |
| Blanchard-Quah (1989) | long-run zero | 1e-10 to 1e-12 |
| Gertler-Karadi (2015) | proxy SVAR | 1e-7 (conditioning floor) |
| Jorda-Taylor (2025) | local projections, OLS | 1e-9 |
| Jorda-Taylor (2025) | local projections, IV | 1e-8 incl. first-stage F |

Historical decompositions are validated on the first three VAR cases at the same
tolerances.

### Weaker, and labelled as such

Uhlig (2005) and Antolín-Díaz–Rubio-Ramírez (2018) are rejection samplers, so
draw-for-draw agreement is impossible. The fixtures hold the impact matrices
MATLAB accepted (`inference = 0`, rotations around the point estimate) and the
tests check that our predicate accepts all of them, that our IRFs from those
matrices match to 1e-8, and that both ADRR narrative constraints bind. This
validates everything except the RNG. **Do not present it as equivalent to the
rows above.**

Bootstrap bands and posterior draws are tested through distributional properties
(Haar uniformity, Wishart moment formulas, the Kronecker covariance).

`tools/make_fixtures.m` regenerates everything under MATLAB R2026a;
`tools/shims/` supplies exact `zscore`/`norminv` so it runs without the
Statistics toolbox.

## Next action

Nothing is blocking. The highest-value remaining item is TODO 1 below —
implementing ADRR's importance weighting would make this *better* than upstream
rather than merely a faithful port.

## Outstanding TODOs

1. **Narrative restrictions follow upstream's rejection filter, not the
   importance weighting of the original paper.** Same posterior support,
   different shape, so results will not reproduce the paper's figures. Flagged
   in README and docstring. Implementing the weighting is a genuine improvement
   over upstream, not a port task.
2. Bootstrap bias correction (Kilian 1998) — upstream does not apply it either.
3. Decide the pandas question before the API hardens: currently pure-array,
   variable names are the caller's problem.
4. Consider publishing to PyPI (name is free).
5. `repos-admin` does not scan the `open-source/` category, so this repo shows
   as a sync warning in `~/repos/INDEX.md`. Pre-existing — `other/cancherism`
   warns identically. One-line fix in
   `admin/repos-admin/src/repos_admin/index.py:18`.

Explicitly **not** a TODO: a JAX backend for the rotation sampler. Tried,
measured, rejected — see ticket 07 in `docs/roadmap.md` for the numbers.

## Recent decisions

- **2026-07-25** — Standalone GPL-3.0 port rather than an upstream PR. Upstream
  history is two squashed release commits by a single author, and both
  substantive community PRs were closed unmerged.
- **2026-07-25** — numpy is the reference implementation and the default
  everywhere; JAX is optional and now scoped to the bootstrap alone.
- **2026-07-25** — Keep `lstsq` over upstream's normal equations. Matching a
  less accurate reference bit-for-bit is not worth losing accuracy elsewhere;
  the GK2015 tolerance is widened to 1e-7 instead.
- **2026-07-25** — Do not assert on which linear-algebra solver lands closer to
  MATLAB; that ordering flips between Accelerate and OpenBLAS. CI caught this
  after I had written the wrong explanation into the docs.
- **2026-07-25** — Backends share their resample draws, generated in numpy, so
  numpy/JAX parity is an exact draw-for-draw comparison.
- **2026-07-25** — Use `(time/horizon, variable, shock)` ordering everywhere.
  Upstream is inconsistent: `IR` is `(h, variable, shock)` but `VD` and
  `HD.shock` are `(h, shock, variable)`.
- **2026-07-25** — Sign-restriction bands include posterior parameter
  uncertainty by default, matching `SR.m`. `posterior=False` gives the
  identified set alone and is documented as not comparable to published figures.
- **2026-07-25** — JAX helps the bootstrap (8.2x) and hurts the rotation sampler
  (300x slower). The difference is what each replication costs: a full
  re-estimation amortises dispatch, a small QR does not. Both numbers are
  recorded rather than only the flattering one.
