# STATUS — src/pyvartoolbox layout refactor

Last updated: 2026-07-26

## Stage

Wave 1 dispatched and reviewed on 2026-07-26. A1 and B1 both implemented, both
independently verified against their Done-when gates, both APPROVE from a
`code-reviewer` pass. A2 came along inside A1's diff (dispatch-prompt error, see
below) and was verified separately against the built wheel. **All three are
uncommitted** — the working tree holds wave 1 plus A2, awaiting a commit.

Remaining: A3 and B2 (wave 2), C1 (wave 3, now unblocked since A2 is done).

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
| A3 | package boundary | TODO | A1 | 2 |
| B2 | identification cohesion | TODO | B1 (collision) | 2 |
| C1 | regression guard | TODO | A2 | 3 |

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
- **Wave 2:** A3, B2 remaining (A2 ✅ — see footnote). A3 is `skill/**`, B2 is
  `ident.py`/`sign.py`/`api.md`/`test_model.py`. Disjoint, dispatchable in parallel.
- **Wave 3:** C1 — unblocked now that A2 is done.

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
3. **The B1 asymmetry invariant is stated too broadly in `TICKETS.md`.** "`sign` does
   not restore the column" is true of the *non-IV rotation path* only; `sign.py:157`
   (sign+IV) does restore, and always did. A later audit reading it literally will
   raise a false positive.

## Next action

**Commit wave 1 + A2** — the tree is verified but uncommitted; nothing should be
dispatched on top of an uncommitted base. Then dispatch A3 and B2 in parallel
(file-disjoint), with C1 following.

The plan's original suggestion to re-run `/plan review` with gemini re-authenticated
was skipped before wave 1. Wave 1 came back clean, so the codex-only critique held up
for stream A/B basics — but B2 and C1 have had exactly one model's eyes on them.
