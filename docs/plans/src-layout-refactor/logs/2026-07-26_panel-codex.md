# Panel critique — codex (session 142), 2026-07-26

Advisory review of the draft ticket graph. gemini (143) failed on expired OAuth
and grok (144) returned empty, so this was the only verdict received.

**Main Critique**

A1 violates the stated hard constraint as written. The context says “tests must pass unchanged,” but A1 explicitly edits `tests/test_concept_graph.py` and `tests/test_handbook.py`. That is not just bookkeeping: both tests directly import `pyvartoolbox._graph` / `pyvartoolbox._convert`. If tests are truly untouchable, A1 cannot move those modules out of `pyvartoolbox` without keeping compatibility shims, which would undercut “wheel contains neither module.” Pick one.

**1. Missing / Duplicate Tickets**

A1 fixes the “doc tooling ships in wheel + scripts exposed” defect only if you accept changing internal test imports. It does not fix references in docs/handbook/graph text that still tell maintainers to run `pyvartoolbox-convert-handbook` / `pyvartoolbox-graph-diagram`; maybe fine if the dev workspace preserves them, but A1 should explicitly include generated-doc references or declare them intentionally unchanged.

B1 fixes the duplicated QR completion and the back-import of `_cholesky`. Good ticket.

B2 fixes a real fourth defect implied by the description: `impact_matrix(..., "sign")` lies by saying “not implemented” when the implementation exists elsewhere. That is not just documentation polish; it is API behavior.

Missing ticket: packaging verification should inspect the built wheel metadata, not only `src/pyvartoolbox` and root `[project.scripts]`. A hatch config change can still accidentally include files through artifacts/package settings. C1 should assert wheel contents or there should be a separate packaging-smoke ticket.

**2. Wrong Depends-On**

B2 is not meaningfully gated on B1. The point-vs-set rule and `impact_matrix("sign")` error can be changed before extracting `_linalg.py`. The only shared files are `ident.py` and `sign.py`, so the dependency is about avoiding merge collisions, not correctness. If this is a multi-agent graph, make B2 wave 2 because of file collision risk, not because it depends on B1.

C1 is gated on A1 if it must pass immediately. But as a TDD guard, C1 could be written first and fail before A1. Current dependency is acceptable for green-only sequencing, not logically necessary.

**3. Same-Wave Collisions**

A1 and B1 do not directly overlap. A1 touches `pyproject.toml`, doc-tool modules, and doc tests. B1 touches `ident.py`, `sign.py`, new `_linalg.py`.

Indirect coupling is low. B1 adding `src/pyvartoolbox/_linalg.py` slightly weakens a naive C1 rule like “no private modules,” but C1 is wave 2 and should target doc-tooling names/patterns, not all underscore modules.

**4. Tickets Too Big**

A1 is too big for one clean ticket. It combines:

- moving modules
- creating a second package
- adding uv workspace wiring
- changing root scripts
- preserving local CLI behavior
- updating tests
- proving wheel contents

Split it unless one person owns it end to end. Better decomposition:

A1a: remove installed user scripts from root package and prove wheel metadata is clean.

A1b: relocate doc tooling into `tools/pyvartoolbox_docs`.

A1c: wire uv workspace/local entry points and update maintenance tests/imports.

A1d or C1: add permanent packaging guard.

The risky bit is not the file move; it is uv workspace behavior and console-script resolution from the root.

**5. Hidden Ordering / Risk**

Yes, moving `_graph.py` breaks `test_diagram_is_current` and the other graph tests immediately:

```python
from pyvartoolbox._graph import build_page, parse_notes
```

Same for handbook converter tests:

```python
from pyvartoolbox._convert import _balanced, preprocess, split_tex
```

So A1’s done-when “full suite exits 0” catches it, but the ticket description underplays that this is a test import migration. If tests must be unchanged, A1 is impossible as drafted.

Other gaps:

- `uv run pyvartoolbox-graph-diagram --help` may still resolve an old installed script unless the workspace/package wiring is precise. The done condition should run from a clean environment or verify the command target.
- `uv build` at repo root may not build the tools package. If the new package has its own `pyproject.toml`, explicitly test the root library wheel and the tools entry points.
- C1 reading only `pyproject.toml` misses stale built artifacts in `dist/`. CI should clean `dist/` before wheel inspection.
- B1 done-when grep is weak: `grep -c "_complete_basis"` can pass while duplicated QR logic remains under another name. Add a behavioral or structural assertion, or review requirement.
- B1 should run sign+iv tests specifically. The dangerous behavior is preserving IV column restoration inside sign+iv rotations, not plain Cholesky/sign tests alone.

**6. Is A1’s Approach Right?**

I would not jump straight to a separate package.

Best pragmatic option: hatch wheel-exclusion plus removing public console scripts from `[project.scripts]`, if local dev commands can still be exposed through a dev-only mechanism. This keeps tests importing `pyvartoolbox._graph` / `_convert` unchanged while preventing wheel dead weight. It is the smallest change and respects the “tests unchanged” constraint.

Separate package is cleaner architecturally, but it is heavier than the defect demands. It creates workspace complexity, a second package to maintain, import-path churn in tests, and possible confusion around which project owns the commands.

Leaving the tooling in the package is defensible only if the project values simplicity over distribution hygiene. But the scripts are exposed to every pip installer and operate on repo-local assets, so this is not harmless dead weight; it is misleading public surface.

My recommendation: replace A1 with a narrower “exclude dev tooling from wheel + remove installed scripts or make them dev-only” ticket first. Only split into `tools/pyvartoolbox_docs` if hatch exclusion cannot preserve local entry points cleanly under the project’s uv rules.
