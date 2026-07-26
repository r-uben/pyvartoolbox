# Viewing the concept graph

## Obsidian (recommended)

Open this folder as a vault, then `⌘G` for Graph View or `⌘⇧G` for the local
graph of the focused note. Nothing needs converting — the notes are already
wikilinked with frontmatter.

`.obsidian/graph.json` ships with the folder so the view is configured on first
open: nodes coloured by `type`/`layer`, and `INDEX`/`GRAPH` filtered out. Those
two link to everything, so leaving them visible makes the index the largest hub
in the picture and visually displaces `identification-problem`, which is the
concept that actually is central.

**Obsidian rewrites `.obsidian/graph.json` from its own in-memory state while a
vault is open.** Editing that file with the app running silently loses the
change. Quit Obsidian first, or make the change through its UI.

Only `graph.json` is tracked; `workspace.json` and friends are per-machine churn
and gitignored.

## Static views

- [GRAPH.md](GRAPH.md) — the Obsidian render as a committed screenshot, plus a
  Mermaid diagram generated from the notes, which GitHub displays inline.
- Regenerate the Mermaid with `uv run pyvartoolbox-graph-diagram`. That command
  is maintainer tooling: it ships with the `pyvartoolbox-docs` dev workspace
  package and is only on the PATH inside a repo checkout, not after a
  `pip install pyvartoolbox`.

Foam, Logseq and Dendron read this layout directly as well.
