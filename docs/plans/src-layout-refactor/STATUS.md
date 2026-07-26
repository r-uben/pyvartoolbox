# STATUS — src/pyvartoolbox layout refactor

Last updated: 2026-07-26

## Stage

Plan authored and revised after an advisory panel. Nothing implemented —
`create` writes the plan, `next` dispatches it.

**The panel was one model, not three.** codex (session 142) delivered a
substantive critique. gemini (143) failed on expired OAuth; grok (144) returned
empty after 5s. Treat the review as a single strong opinion, not a consensus —
re-running `/plan review` once `gemini` is re-authenticated would be worth it
before dispatching wave 1.

## Base state (clean before tickets)

- Repo: `~/repos/open-source/pyvartoolbox`, branch `feat/10-src-layout-refactor`
  cut from `main` at `6e172ae`
- 249 tests passing, ruff clean, CI green on 3.11/3.12/3.13
- Working tree clean at branch point; `main` pushed and even with origin
- v0.5.0 tagged; package feature-complete against upstream

## Ticket board

| Ticket | Stream | Status | depends-on | Wave |
|--------|--------|--------|------------|------|
| A1 | package boundary | TODO | — | 1 |
| B1 | identification cohesion | TODO | — | 1 |
| A2 | package boundary | TODO | A1 | 2 |
| A3 | package boundary | TODO | A1 | 2 |
| B2 | identification cohesion | TODO | B1 (collision) | 2 |
| C1 | regression guard | TODO | A2 | 3 |

## Dispatch waves

- **Wave 1:** A1, B1 — file-disjoint. A1 touches the doc-tooling modules,
  `pyproject.toml` and two test modules; B1 touches `_linalg.py`, `ident.py`,
  `sign.py`.
- **Wave 2:** A2, A3, B2 — A2 is `pyproject.toml` only, A3 is `skill/**`, B2 is
  `ident.py`/`sign.py`/`api.md`/`test_model.py`. Disjoint.
- **Wave 3:** C1 — needs a wheel built without the scripts, so it follows A2.

## What the panel changed

1. **A1 contradicted its own constraint.** "All 249 tests must pass unchanged"
   versus a ticket that necessarily edits two test modules' imports. Resolved by
   stating the constraint precisely: test diffs must be import-path-only, and
   A1 now carries a `git diff` check proving it.
2. **A1 was too big** — module move plus new package plus workspace wiring plus
   `pyproject` surgery plus test updates plus wheel proof. Split into A1
   (relocate + imports), A2 (drop scripts, verify the built artifact), A3 (docs
   that reference the commands).
3. **C1 was checking the wrong thing.** Asserting on the source tree and
   `[project.scripts]` misses a hatch `artifacts` setting re-including files.
   Now asserts against wheel contents.
4. **B2's dependency is collision-based, not logical** — stated explicitly in
   the ticket so a future dispatcher does not treat it as a correctness gate.
5. **A stale global console script could fake a green Done-when.** A2 now
   requires recording the resolved path of `pyvartoolbox-graph-diagram`.
6. **A3 is new** — the panel spotted that `skill/**` docs instruct readers to run
   commands that will no longer exist for installed users.

## Risks being carried

- The uv workspace wiring in A1 is the genuinely uncertain part; the file move is
  routine. If workspace membership proves awkward, the fallback is a plain path
  dependency in the dev group.
- `tests/test_concept_graph.py::TestDiagram::test_diagram_is_current` imports
  `build_page` and regenerates `GRAPH.md` for byte comparison. It will fail loudly
  on a bad move, which is desirable, but it also means A1 cannot be verified by
  import checks alone.

## Next action

Optionally re-run `/plan review` with gemini re-authenticated (`gemini` needs an
OAuth login), then `/plan next` to dispatch wave 1 (A1 and B1 in parallel).
