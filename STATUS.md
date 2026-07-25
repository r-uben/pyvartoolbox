# STATUS — pyvartoolbox

Last updated: 2026-07-25
Stage: alpha, validated against the MATLAB reference for every implemented scheme
Repo: https://github.com/r-uben/pyvartoolbox (public, GPL-3.0, CI green)

## Where things stand

95 tests pass; ruff clean; CI green on Python 3.11/3.12/3.13.

Done: tickets 01 (core VAR), 03 (historical decompositions), 04 (proxy SVAR),
05 (sign restrictions), and three of the six replications in ticket 02.

Validated against MATLAB VAR Toolbox 4.0 via committed fixtures:

| Case | Scheme | Agreement |
| --- | --- | --- |
| Stock-Watson (2001) | Cholesky | 1e-10 to 1e-12 |
| Blanchard-Quah (1989) | long-run zero | 1e-10 to 1e-12 |
| Gertler-Karadi (2015) | proxy SVAR | 1e-7 (conditioning floor) |

Historical decompositions are validated on all three at the same tolerances.

Not fixture-validated, by necessity rather than omission: bootstrap bands and
sign restrictions both consume RNG streams numpy cannot reproduce. Both are
tested through their statistical properties instead.

## Next action

Ticket 08 (local projections). It is independent of everything outstanding, and
Jordà-Taylor (2025) is deterministic, so it can be fixture-validated exactly the
way 01-04 were — add a case to `tools/make_fixtures.m` and run it under MATLAB
R2026a at `/Applications/MATLAB_R2026a.app/bin/matlab -batch`.

## Outstanding TODOs

1. Ticket 08 — local projections (OLS and IV, Newey-West). Validate against
   JT2025.
2. Ticket 06 — narrative sign restrictions (ADRR 2018). Depends on 05, which is
   done. Adds importance weighting over accepted draws.
3. Ticket 05b — posterior draws. Sign-restriction bands currently reflect
   identification uncertainty only. Upstream's `SR.m` combines rotations with
   coefficient draws from `VARdrawpost.m`; until that is ported the bands are
   not comparable to published sign-restriction figures. **This is the most
   likely thing for a user to misread**, and it is flagged in the README.
4. Ticket 07 — JAX backend for the bootstrap and rotation samplers.
5. Ticket 09 — plotting helpers.
6. Uhlig (2005) replication once 05b lands.
7. Add `open-source/pyvartoolbox` to `~/repos/.repos.yaml`, then regenerate
   `INDEX.md` with `uv run --project admin/repos-admin repos-index`.
8. Email Cesa-Bianchi. Now worth doing: three replications match his toolbox to
   1e-10. Ask whether he objects to the `pyvartoolbox` name, which reads as
   semi-official.

## Recent decisions

- **2026-07-25** — Standalone GPL-3.0 port rather than an upstream PR. Upstream
  history is two squashed release commits by a single author, and both
  substantive community PRs were closed unmerged; there is no review workflow to
  contribute a language port into.
- **2026-07-25** — numpy is the reference implementation; JAX stays optional and
  scoped to resampling. Estimation is one small `lstsq` and gains nothing.
- **2026-07-25** — Keep `lstsq` over normal equations even though upstream uses
  the latter. Matching a less accurate reference bit-for-bit is not worth losing
  accuracy elsewhere; the GK2015 tolerance is widened to 1e-7 instead.
- **2026-07-25** — Deterministic terms are appended *after* the lag block,
  unlike MATLAB. Reference tests therefore compare only layout-invariant
  quantities (`sigma`, `resid`, `B`, `IR`, `VD`, `HD`), never raw coefficients.
- **2026-07-25** — Use `(time/horizon, variable, shock)` ordering everywhere.
  Upstream is inconsistent: `IR` is `(h, variable, shock)` but `VD` and
  `HD.shock` are `(h, shock, variable)`.
- **2026-07-25** — Do not assert on which linear-algebra solver lands closer to
  MATLAB. That ordering flips between Accelerate and OpenBLAS; CI caught it.
  Tests assert magnitudes and contrasts, not tie-breaks.
- **2026-07-25** — Fixtures are committed as full-precision CSV, not `.npz`.
  Readable in review, and `writematrix`'s 5-significant-digit default would have
  silently capped every tolerance at ~1e-5.
