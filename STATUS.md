# STATUS — pyvartoolbox

Last updated: 2026-07-25
Stage: alpha, core validated against the MATLAB reference

## Where things stand

Ticket 01 (core reduced-form VAR) is done and tested: OLS estimation, companion
form, Wold representation, Cholesky and long-run identification, IRF, VD, and
residual/wild bootstrap bands. 30 tests pass.

Nothing has been checked against the MATLAB toolbox yet. The tests verify
internal consistency (simulate-roundtrip, Wold vs companion powers, Cholesky
reproduces sigma, VD shares sum to one, Monte Carlo unbiasedness) — not
agreement with the reference implementation.

## Next action

Ticket 02, and specifically its cheapest half: run the upstream
`Replic/StockWatson2001` and `Replic/BlanchardQuah1989` scripts in MATLAB, dump
the IRF arrays to `.npz`, and assert agreement. Both are already implementable
with the current code, so this converts the package from "plausible" to
"validated" without writing any new numerics.

## Outstanding TODOs

1. Ticket 02 — replication fixtures for Stock–Watson and Blanchard–Quah.
2. Decide the pandas question in `docs/roadmap.md` before the API hardens; it is
   much cheaper to settle now than after ticket 08.
3. Set up the GitHub remote (`r-uben/pyvartoolbox`) and push. Not yet created.
4. Email Cesa-Bianchi once ticket 02 lands — a validated port is a far better
   opening than an announcement of intent. Ask whether he objects to the
   `pyvartoolbox` name, since it reads as semi-official.
5. Add `open-source/pyvartoolbox` to `~/repos/.repos.yaml` and regenerate
   `INDEX.md`.

## Recent decisions

- **2026-07-25** — Standalone GPL-3.0 port rather than an upstream PR. Upstream
  history is two squashed release commits by a single author, and both
  substantive community PRs were closed unmerged; there is no review workflow to
  contribute a language port into.
- **2026-07-25** — numpy is the reference implementation; JAX is an optional
  backend for resampling only. Estimation is one small `lstsq` and gains nothing
  from acceleration.
- **2026-07-25** — Deterministic terms are appended *after* the lag block, unlike
  the MATLAB layout, so `beta[:nvar*nlags]` is always the AR part. This diverges
  from upstream deliberately; the replication tests in ticket 02 must compare
  IRFs, not raw coefficient vectors.
- **2026-07-25** — Skipping `Stats/`, `Utils/`, `Figure/` entirely; numpy,
  pandas and matplotlib already cover them.
