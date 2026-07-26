# TICKETS — src/pyvartoolbox layout refactor

Status keys: `TODO` · `WIP` · `DONE` · `BLOCKED`. `depends-on` gates dispatch.
Parallelizable = no shared files / no dep. Each ticket = one implementer agent,
then one reviewer pass before commit.

## Scope discipline

The flat 16-module layout is **not** the problem and is not being reorganised.
At 3,054 lines it is a reasonable shape for this library, and moving files for
tidiness would churn 249 tests and the skill docs for nothing. Only the
evidenced defects below are in scope.

## Hard constraints (all tickets)

- **Public API frozen.** `src/pyvartoolbox/__init__.py` must export exactly what
  it exports today. `tests/test_skill_docs.py` fails CI if a documented symbol
  disappears, so an accidental API change surfaces as a *docs* failure rather
  than an obvious ImportError — do not be confused by that when it happens.
- **No test expectation may be weakened.** Import paths in test files *may*
  change where a ticket relocates a module; nothing else may. Concretely: any
  diff to a file under `tests/` must be import-path-only. No changed assertion,
  tolerance, skip, or xfail. If a test fails, the refactor is wrong, not the test.
  *(Panel caught the original wording — "all 249 tests pass unchanged" — as
  contradicting A1, which necessarily edits two test modules' imports.)*
- **`tests/fixtures/` and every numerical tolerance are untouchable.** They are
  the MATLAB validation contract.
- **Branch:** `feat/10-src-layout-refactor`. Never `main`.

---

## Stream A — package boundary

### TICKET-A1 — Relocate doc tooling out of the library package · TODO · depends-on: none · wave 1
**Problem:** `_convert.py` (322 lines) and `_graph.py` (182) live in
`src/pyvartoolbox/` but are documentation tooling: they shell out to `pandoc` and
operate on repo-relative paths (`skill/graph`, `VAR_Handbook.tex`) that no
installed user has. They are 16% of the package serving nobody who installs it.

**Do:** Move both to a repo-level `tools/pyvartoolbox_docs/` package with its own
`pyproject.toml`, declaring the two console scripts there. Wire it as a uv
workspace member / path dependency in the dev group so the commands still resolve
inside the repo — the global CLAUDE.md forbids `uv run python <file>.py`, so
these must remain real entry points, not loose scripts. Update the imports in
`tests/test_concept_graph.py` and `tests/test_handbook.py` (import path only).

**Files:** `src/pyvartoolbox/_convert.py`, `src/pyvartoolbox/_graph.py`,
`tools/pyvartoolbox_docs/**` (new), `pyproject.toml`,
`tests/test_concept_graph.py`, `tests/test_handbook.py`

**Done when:**
- `ls src/pyvartoolbox/_convert.py src/pyvartoolbox/_graph.py` exits non-zero
- `uv run pytest -q` exits 0 with 252 tests collected — in particular
  `tests/test_concept_graph.py::TestDiagram::test_diagram_is_current`, which
  imports `build_page`/`parse_notes` and regenerates `GRAPH.md` to compare
- `git diff -- tests/ | grep -E '^[+-]' | grep -v '^[+-][+-]' | grep -vcE '^[+-].*(import|from)'` prints `0`
  (proves the only test changes are imports)

### TICKET-A2 — Drop the doc-tooling scripts from the library distribution · TODO · depends-on: A1 · wave 2
**Problem:** `[project.scripts]` puts `pyvartoolbox-convert-handbook` and
`pyvartoolbox-graph-diagram` on the PATH of everyone who installs the library.
The panel's point: the file move is the easy half; the risk lives in entry-point
resolution and whether the built wheel is actually clean.

**Do:** Remove both entries from the library's `[project.scripts]`, leaving only
`pyvartoolbox-replicate`, which is genuinely user-facing. Verify against the
**built artifact**, not the source tree — a hatch `artifacts`/`packages` setting
can re-include files silently.

**Files:** `pyproject.toml`

**Done when:**
- `uv build` succeeds
- `unzip -l dist/*.whl | grep -cE "_convert|_graph"` prints `0`
- `unzip -p dist/*.whl '*/entry_points.txt' | grep -cE "convert-handbook|graph-diagram"` prints `0`
- `uv run pyvartoolbox-graph-diagram --help` exits 0 **and**
  `command -v pyvartoolbox-graph-diagram` resolves inside the project venv, not a
  stale global install — record the resolved path in the ticket log
- `uv run pytest -q` exits 0

### TICKET-A3 — Reconcile documentation that references the moved commands · TODO · depends-on: A1 · wave 2
**Problem:** `skill/graph/README.md`, `skill/handbook/README.md` and
`skill/graph/GRAPH.md` instruct the reader to run
`pyvartoolbox-convert-handbook` / `pyvartoolbox-graph-diagram`. After A1/A2 those
are dev-workspace commands, not user commands. Left alone, the docs quietly
promise something a `pip install` cannot deliver.

**Do:** Update those references to state that the commands are maintainer tooling
available in a repo checkout, not part of the installed package. Do not delete
the instructions — they are still correct for the audience that regenerates docs.

**Files:** `skill/graph/README.md`, `skill/handbook/README.md`,
`src/pyvartoolbox/_graph.py` docstring text as relocated by A1

**Done when:**
- `grep -rl "pyvartoolbox-convert-handbook\|pyvartoolbox-graph-diagram" --include="*.md" skill/ tools/ | xargs grep -L "repo checkout\|maintainer"` prints nothing
  *(corrected 2026-07-26: the original used `grep -Lc`, where `-c` overrides `-L`,
  so it printed counts unconditionally and could never pass. Verified with the
  fixed form.)*
- `uv run pytest tests/test_skill_docs.py tests/test_concept_graph.py tests/test_handbook.py -q` exits 0

---

## Stream B — identification cohesion

### TICKET-B1 — Extract the shared orthonormal-completion helper · TODO · depends-on: none · wave 1
**Problem:** `ident._complete` and `sign._complete_basis` implement nearly the
same operation — complete a unit vector to an orthonormal basis by QR, fixing the
sign of the first column — on opposite sides of the module split. `sign.py`
additionally reaches back into `ident.py` for `_cholesky`. Two copies of a
load-bearing numerical routine drift; this one underpins proxy-SVAR and sign+IV.

**Do:** Create `src/pyvartoolbox/_linalg.py` holding the guarded Cholesky
(currently `ident._cholesky`, keeping its positive-definite error message
verbatim) and a single `orthonormal_completion(q1, nvar)`. Rewrite both call
sites. **Preserve the behavioural difference:** `ident._complete` restores the
identified column *after* completion, so `B @ B.T == sigma` need not hold; the
**plain non-IV rotation path** in `sign.py` does not restore, and satisfies the
identity exactly. That asymmetry is intentional and tested.

*Two precisions added 2026-07-26, both found during implementation — the original
wording would mislead a later audit:*
- *The rule is scoped to the non-IV path. `sign.py`'s **sign+IV** path also restores
  column 0 (pre-existing, untouched by B1), so "`sign` does not restore" is false read
  literally of the module.*
- *"Deliberately breaking" overstates it. The break depends on `||q1|| != 1`, which
  happens only when the instrument is observed on a shorter sample than `sigma`.
  Measured: `5.551e-16` when the instrument spans the full VAR sample versus
  `9.537e-02` when it does not.*

**Files:** `src/pyvartoolbox/_linalg.py` (new), `src/pyvartoolbox/ident.py`,
`src/pyvartoolbox/sign.py`

**Done when:**
- `grep -c "_complete_basis" src/pyvartoolbox/sign.py` prints `0`
- `grep -c "def _cholesky" src/pyvartoolbox/ident.py` prints `0`
- `uv run pytest tests/test_model.py tests/test_sign.py tests/test_reference.py tests/test_sign_reference.py -q` exits 0
- `uv run pytest -q` exits 0

### TICKET-B2 — State the point-versus-set rule and stop `impact_matrix` lying · TODO · depends-on: B1 (file collision, not logic) · wave 2
**Problem:** No stated rule says which scheme lives in which module, so the split
reads as arbitrary. It is not: `ident.py` holds point-identified schemes and the
dispatcher, `sign.py` holds set-identified schemes and the sampler — exactly the
distinction the docs already call the most important thing a user must grasp.
Separately, `impact_matrix(m, "sign")` raises "not implemented", which is false:
it *is* implemented, just not reachable through a function that returns one `B`.

**Do:** Document the rule at the top of both modules. Change `impact_matrix` so a
set-identified scheme name raises an error naming `sign_restricted_irf` and
explaining that a set-identified scheme has no single `B` to return. Record the
rule in `skill/references/api.md`.

**Note on the dependency:** the panel is right that this is not logically gated on
B1 — it could ship first. It is sequenced second only because both tickets edit
`ident.py` and `sign.py`, and same-wave collisions are a merge conflict waiting to
happen. If B1 is dropped, B2 becomes wave 1.

**Files:** `src/pyvartoolbox/ident.py`, `src/pyvartoolbox/sign.py`,
`skill/references/api.md`, `tests/test_model.py`

**Done when:**
- `impact_matrix(model, "sign")` raises with a message containing
  `sign_restricted_irf`, asserted by a new test in `tests/test_model.py`
- `uv run pytest -q` exits 0
- `uv run pytest tests/test_skill_docs.py -q` exits 0

---

## Stream C — regression guard

### TICKET-C3 — Make the packaging guard actually run in CI · TODO · depends-on: C1 · wave 4
**Problem:** C1's `tests/test_packaging.py` skips when no matching wheel is in
`dist/`. `.github/workflows/ci.yml:20-22` runs `uv sync`, `ruff`, `pytest` and
**never `uv build`**, so `dist/` does not exist in CI and all four packaging tests
skip on every run, on every Python version. The suite reports green while the guard
asserts nothing. C1's Problem statement — "nothing stops the next dev-only module
re-entering the wheel, because nobody inspects a built artifact" — is therefore still
true after C1 ships, in the one place that checks every PR.

The skip-when-unbuilt behaviour is correct and specified; the gap is that nothing in
CI ever builds. Found by the dispatcher while reviewing C1, not by C1's own gates —
every one of which passes locally.

**Do:** Add a `uv build` step to `.github/workflows/ci.yml` before the pytest step so
the packaging tests execute rather than skip. Keep the skip path intact for local runs.

**Files:** `.github/workflows/ci.yml`

**Done when:**
- `.github/workflows/ci.yml` contains a `uv build` step ordered before the `uv run pytest` step
- a CI run on the branch shows `tests/test_packaging.py` with 4 passed and 0 skipped —
  paste the run URL in the ticket log. Local verification is not sufficient for this
  ticket, since the whole defect is CI-specific.

### TICKET-C2 — Guard the generated handbook index · TODO · depends-on: none · wave 3
**Problem:** `tests/test_handbook.py:19` excludes `INDEX.md` from the `pages`
fixture with the comment "INDEX and README are hand-written scaffolding, not
converted pages". That is false for `INDEX.md`: it is generator output from
`_index()` in `_convert.py`, proven during the A3 review by regenerating from a
fresh upstream clone and byte-diffing the result. The consequence is that nothing
regeneration-tests `INDEX.md` — it gets substring assertions at
`tests/test_handbook.py:35,96-97` and nothing more, so a hand-edit that drifts from
the generator would pass CI. `GRAPH.md` has exactly this protection
(`test_diagram_is_current`); `INDEX.md` does not.

**Do:** Correct the misleading comment, and add a regeneration check for `INDEX.md`
mirroring `test_concept_graph.py::TestDiagram::test_diagram_is_current` — call
`_index()` and byte-compare against the checked-in file. Skip cleanly when the
handbook has not been generated, as the existing `pages` fixture already does.

**Files:** `tests/test_handbook.py`

**Done when:**
- `grep -c "hand-written scaffolding" tests/test_handbook.py` prints `0`
- `uv run pytest tests/test_handbook.py -q` exits 0
- temporarily appending a line to `skill/handbook/INDEX.md` makes it fail; restore
  the file with `uv run pyvartoolbox-convert-handbook` and confirm it passes again

### TICKET-C1 — Assert the distribution stays clean · TODO · depends-on: A2 · wave 3
**Problem:** A1/A2 fix today's instance. Nothing stops the next dev-only module
re-entering the wheel, because nobody inspects a built artifact by hand.

**Do:** Add `tests/test_packaging.py` asserting the built wheel contains no
documentation-tooling modules and declares only user-facing console scripts.
Read `pyproject.toml` with stdlib `tomllib` rather than adding a dependency.
Follow the panel: assert against **wheel contents**, not just the source tree —
source-only checks miss a hatch `artifacts` setting re-including files. Skip
cleanly if no wheel has been built, so the suite stays runnable without `uv build`.

**Files:** `tests/test_packaging.py` (new)

**Done when:**
- `uv build && uv run pytest tests/test_packaging.py -q` exits 0
- Temporarily restoring `src/pyvartoolbox/_convert.py`, rebuilding, and rerunning
  makes it fail — verify, then delete the copy
- `uv run pytest tests/test_packaging.py -q` still exits 0 with no `dist/` present
