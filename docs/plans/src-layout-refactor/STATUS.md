# STATUS — src/pyvartoolbox layout refactor

Last updated: 2026-07-26

## Stage

**All originally-planned tickets are done and committed** as of 2026-07-26: A1, A2,
B1 (`d3e11a9`), B2 (`4a8597c`), A3 (`33536af`), C2 (`9e27d3b`), C1 (`fc953f5`). Every
ticket was verified against its Done-when by the dispatcher rather than on the
implementer's self-report. Working tree clean; 258 tests pass, ruff clean.

One ticket remains, and it is not optional: **C3** — C1's packaging guard never runs
in CI, so the regression it exists to prevent is still unguarded on every pull request.
Nothing pushed since wave 1.

**The panel was one model, not three.** codex (session 142) delivered a
substantive critique. gemini (143) failed on expired OAuth; grok (144) returned
empty after 5s. Treat the review as a single strong opinion, not a consensus —
re-running `/plan review` once `gemini` is re-authenticated would be worth it
before dispatching wave 1.

## Base state (clean before tickets)

- Repo: `~/repos/open-source/pyvartoolbox`, branch `feat/10-src-layout-refactor`
  cut from `main` at `6e172ae`
- 252 tests passing, ruff clean, CI green on 3.11/3.12/3.13
  *(the plan originally recorded 249; verified against `a5710ec` on 2026-07-26 —
  the baseline is 252, so 249 was stale when written, not a regression)*
- Working tree clean at branch point; `main` pushed and even with origin
- v0.5.0 tagged; package feature-complete against upstream

## Ticket board

| Ticket | Stream | Status | depends-on | Wave |
|--------|--------|--------|------------|------|
| A1 | package boundary | DONE | — | 1 |
| B1 | identification cohesion | DONE | — | 1 |
| A2 | package boundary | DONE¹ | A1 | 2 |
| A3 | package boundary | DONE | A1 | 2 |
| B2 | identification cohesion | DONE | B1 (collision) | 2 |
| C1 | regression guard | DONE² | A2 | 3 |
| C2 | regression guard | DONE | — | 3 |
| C3 | regression guard | TODO | C1 | 4 |

² C1 also lacks a reviewer pass — `rev-C1` went idle without reporting. Verified
independently by the dispatcher, including the teeth proof and a `configparser`
case-folding defect found and fixed. See `logs/2026-07-26_C1.md`.

¹ A2 did **not** get its own implementer+reviewer pass. Its edit landed inside A1's
diff because the A1 dispatch prompt paraphrased the ticket and absorbed A2's scope.
Its Done-when gates were then run independently against the built wheel and pass —
see `logs/2026-07-26_A2.md`. Recorded DONE on that evidence, not on assertion.

## Dispatch waves

- **Wave 1:** A1, B1 — ✅ done 2026-07-26. File-disjoint as planned; the parallel
  dispatch worked, with the caveat that both agents shared one working tree, so the
  full-suite gate each ticket listed saw the other's in-flight edits. The reliable
  signals were the per-ticket static gates plus a single full-suite run by the
  dispatcher after both landed.
- **Wave 2:** A2, A3, B2 — ✅ done. Run serially, not in parallel: B2 edits
  `skill/references/api.md` and A3 edits `skill/*/README.md`, both inputs to
  `tests/test_skill_docs.py`, which appears in both tickets' Done-when. Files were
  disjoint but *gates* were not — the distinction that matters for parallel dispatch.
- **Wave 3:** C1, C2 — ✅ done, genuinely parallel-safe (`tests/test_packaging.py`
  versus `tests/test_handbook.py`, no shared gate).
- **Wave 4:** C3 — the CI build step. Cannot be verified locally by construction.

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

## Lessons for the remaining waves

1. **Build implementer prompts from the ticket text verbatim.** Paraphrasing A1's
   ticket leaked A2's scope into it. The plan skill says the ticket fields *are* the
   prompt body; treat that literally.
2. **Parallel same-tree dispatch makes a full-suite Done-when unreliable.** Each
   agent sees the other's half-finished edits. Either keep per-ticket gates scoped to
   files that ticket owns, or run parallel tickets in separate worktrees.
3. **The B1 asymmetry invariant was stated too broadly in `TICKETS.md`** — now fixed
   there. "`sign` does not restore the column" holds for the *non-IV rotation path*
   only; `sign.py`'s sign+IV path does restore, and always did. Separately, the break
   is conditional on the instrument's sample, not automatic. Both precisions are now
   in B1's ticket text and in the `ident.py`/`sign.py` docstrings.
4. **Prose about a numerical invariant needs a measurement, not an adjective.** B2
   shipped "iv deliberately does not satisfy `sigma == B B.T`" — an absolute claim
   that is false when the instrument spans the full VAR sample. Caught only by
   running it. If a docstring asserts a numerical property, verify it numerically
   before believing it, whoever wrote it.

## Two unpassable gates found — a pattern, not two accidents

Two of six tickets shipped with a **Done-when that could never pass**:

1. **A1** asserted "249 tests collected". The real baseline at `a5710ec` is 252,
   per-file identical — stale when written.
2. **A3** used `grep -rl ... | xargs grep -Lc "..."` expecting empty output. `-c`
   overrides `-L`, so it prints counts unconditionally.

Both were authored without being executed. Neither was caught by the advisory panel.
The rule going forward: **run every Done-when command against the pre-ticket tree
while writing it** — a gate that has never been executed is a guess. Note it should
fail before the ticket and pass after; A1's would have failed in both directions.

## Three defects that only surfaced by running things

Each passed every gate it was subject to, and each was found by executing rather than
reading. This is the plan's most transferable output:

1. **B2** shipped an absolute claim — "iv deliberately does not satisfy
   `sigma == B B.T`" — that is false when the instrument spans the full VAR sample
   (`5.551e-16` versus `9.537e-02`). A docstring, so no test could ever fail.
2. **C1**'s `configparser` lower-cased console-script names, which would fail the
   entry-point comparison for a reason unrelated to packaging. Invisible because every
   current script is lower-case.
3. **C1** never runs in CI at all (→ C3). All four tests skip on every pull request
   while the suite reports green.

The pattern: a green suite is evidence about what was executed, not about what was
claimed. Prose claims and skipped tests are both invisible to it.

## Next action

Dispatch **C3** — add `uv build` to `.github/workflows/ci.yml` before the pytest step.
Until it lands, C1 is a guard that never fires where it matters, and the branch should
not be presented as having packaging protection.

Then push the branch and open the PR. Still outstanding: the plan's panel was
effectively one model (codex) — gemini failed on expired OAuth, grok returned empty.
C1/C2/C3 were never panel-reviewed at all.
