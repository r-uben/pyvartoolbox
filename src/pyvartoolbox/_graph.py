"""Render the concept graph as a Mermaid diagram.

The notes in ``skill/graph/`` already carry typed relations; this reads them and
emits a diagram GitHub renders inline, so the structure is visible without
installing anything or cloning the repo.

Generated rather than hand-drawn: a hand-maintained diagram drifts from the
notes within a week, and a wrong diagram is worse than none.

Run::

    pyvartoolbox-graph-diagram --graph skill/graph
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

WIKILINK = re.compile(r"\[\[([^\]|]+?)(?:\|[^\]]+)?\]\]")
RELATION = re.compile(r"^-\s+(.+?)\s*→\s*(.+)$", re.M)

# Ordered so related groups sit near each other in the rendered layout.
GROUPS = [
    ("foundation", "Foundations", None),  # matched on layer, not type
    ("objects", "What gets reported", "object"),
    ("schemes", "Identification schemes", "scheme"),
    ("inference", "Inference", "inference"),
    ("pitfalls", "Pitfalls", "pitfall"),
    ("other", "Cross-cutting", None),
]

STYLE = {
    "foundation": "fill:#eef2f7,stroke:#1f4e79,color:#12263a",
    "objects": "fill:#eef5f1,stroke:#4c8c72,color:#12263a",
    "schemes": "fill:#f7eeee,stroke:#a4342c,color:#12263a",
    "inference": "fill:#f6f1e8,stroke:#c98b2e,color:#12263a",
    "pitfalls": "fill:#f2eef7,stroke:#6b5b95,color:#12263a",
    "other": "fill:#f2f2f2,stroke:#7f8c8d,color:#12263a",
}


def parse_notes(graph_dir: Path) -> dict[str, dict]:
    """Read every note into ``{slug: {type, layer, title, edges}}``."""
    notes = {}
    for path in sorted(graph_dir.glob("*.md")):
        if path.name in ("INDEX.md", "GRAPH.md", "README.md"):
            continue
        text = path.read_text(encoding="utf-8")
        front = text.split("---", 2)[1] if text.startswith("---") else ""
        meta = dict(re.findall(r"^(\w+):\s*(.+)$", front, re.M))
        title = re.search(r"^#\s+(.+)$", text, re.M)

        edges = []
        relations = text.split("## Relations", 1)
        if len(relations) == 2:
            for verb, targets in RELATION.findall(relations[1]):
                for target in WIKILINK.findall(targets):
                    if not target.startswith(".."):
                        edges.append((verb.strip(), target.strip()))

        notes[path.stem] = {
            "type": meta.get("type", "").strip().strip('"'),
            "layer": meta.get("layer", "").strip().strip('"'),
            "title": title.group(1).strip() if title else path.stem,
            "edges": edges,
        }
    return notes


def _group_of(note: dict) -> str:
    # Layer wins over type: the foundational notes are all type "concept", but
    # so are some cross-cutting ones, so type alone would over-collect.
    if note["layer"] == "foundation":
        return "foundation"
    for key, _, type_name in GROUPS:
        if type_name and note["type"] == type_name:
            return key
    return "other"


def _short(verb: str) -> str:
    """Keep edge labels readable; the note carries the full phrasing."""
    verb = re.sub(r"\s+", " ", verb).strip()
    return verb if len(verb) <= 18 else verb[:17] + "…"


def build_mermaid(notes: dict[str, dict]) -> str:
    grouped: dict[str, list[str]] = {key: [] for key, _, _ in GROUPS}
    for slug, note in notes.items():
        grouped[_group_of(note)].append(slug)

    lines = ["graph LR"]
    for key, label, _ in GROUPS:
        members = sorted(grouped[key])
        if not members:
            continue
        lines.append(f'  subgraph {key}["{label}"]')
        for slug in members:
            lines.append(f'    {slug}["{notes[slug]["title"]}"]')
        lines.append("  end")

    seen = set()
    for slug in sorted(notes):
        for verb, target in notes[slug]["edges"]:
            if target not in notes or (slug, target) in seen:
                continue
            seen.add((slug, target))
            lines.append(f'  {slug} -- "{_short(verb)}" --> {target}')

    for key, _, _ in GROUPS:
        if grouped[key]:
            lines.append(f"  classDef {key} {STYLE[key]};")
            lines.append(f"  class {','.join(sorted(grouped[key]))} {key};")

    return "\n".join(lines)


def build_page(notes: dict[str, dict]) -> str:
    diagram = build_mermaid(notes)
    edge_count = sum(len(n["edges"]) for n in notes.values())
    return "\n".join(
        [
            "---",
            'title: "Concept graph — diagram"',
            "type: diagram",
            "---",
            "",
            "# Concept graph",
            "",
            f"{len(notes)} concepts, {edge_count} typed relations. Generated from the",
            "notes themselves by `pyvartoolbox-graph-diagram` — **do not hand-edit**,",
            "regenerate. A hand-maintained diagram drifts from the notes within a week,",
            "and a wrong map is worse than none.",
            "",
            "```mermaid",
            diagram,
            "```",
            "",
            "Node text links nowhere by design: Mermaid link support varies by",
            "renderer, and a diagram that half-works is worse than one that clearly",
            "does not. Use [INDEX.md](INDEX.md) to navigate.",
            "",
            "## Other ways to view this",
            "",
            "- **Obsidian** — point a vault at this folder. The notes are already",
            "  wikilinked, so the native graph view works with no conversion, and it is",
            "  interactive in a way a static diagram is not.",
            "- **Any wikilink-aware editor** — Foam, Dendron, Logseq all read this",
            "  layout directly.",
            "",
        ]
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="pyvartoolbox-graph-diagram",
        description="Render skill/graph as a Mermaid diagram GitHub can display.",
    )
    parser.add_argument("--graph", type=Path, default=Path("skill/graph"))
    args = parser.parse_args(argv)

    notes = parse_notes(args.graph)
    if not notes:
        print(f"no notes found in {args.graph}")
        return 1
    out = args.graph / "GRAPH.md"
    out.write_text(build_page(notes), encoding="utf-8")
    print(f"wrote {out} ({len(notes)} concepts)")
    return 0
