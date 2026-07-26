"""Integrity of the concept graph in skill/graph/.

A knowledge graph fails silently: a wikilink is renamed, the note it pointed at
still exists under the old name, and a reader — human or model — follows a dead
edge. These tests make broken structure a CI failure.
"""

import re
from pathlib import Path

import pytest

GRAPH = Path(__file__).parent.parent / "skill" / "graph"
INDEX = GRAPH / "INDEX.md"

WIKILINK = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]")


#: Generated or hand-written scaffolding, not concept notes. They carry no
#: Relations section and would fail every structural check below.
NOT_NOTES = {"INDEX.md", "GRAPH.md", "README.md"}


def _notes():
    return sorted(p for p in GRAPH.glob("*.md") if p.name not in NOT_NOTES)


def _links(text):
    """Wikilink targets, dropping any display alias and external paths."""
    return {m.strip() for m in WIKILINK.findall(text) if not m.startswith("..")}


@pytest.fixture(scope="module")
def notes():
    return {p.stem: p.read_text(encoding="utf-8") for p in _notes()}


class TestStructure:
    def test_graph_is_not_empty(self, notes):
        assert len(notes) >= 20, "a graph this small is a list, not a graph"

    def test_index_exists(self):
        assert INDEX.exists()

    def test_every_note_has_frontmatter_with_a_type(self, notes):
        for name, text in notes.items():
            assert text.startswith("---\n"), f"{name} has no frontmatter"
            block = text.split("---", 2)[1]
            assert re.search(r"^type:\s*\S+", block, re.M), f"{name} has no type"

    def test_every_note_has_a_relations_section(self, notes):
        """A note with no stated edges is a document, not a graph node."""
        for name, text in notes.items():
            assert "## Relations" in text, f"{name} states no relations"


class TestEdges:
    def test_no_dangling_links(self, notes):
        dangling = {}
        for name, text in notes.items():
            missing = _links(text) - set(notes)
            if missing:
                dangling[name] = sorted(missing)
        assert not dangling, f"links to non-existent notes: {dangling}"

    def test_index_links_are_valid(self, notes):
        missing = sorted(_links(INDEX.read_text(encoding="utf-8")) - set(notes))
        assert not missing, f"INDEX links to non-existent notes: {missing}"

    def test_no_note_links_only_to_itself(self, notes):
        for name, text in notes.items():
            assert _links(text) - {name}, f"{name} has no outbound edges"

    def test_every_note_is_reachable_from_the_index(self, notes):
        """An unreachable note will never be read."""
        seen, frontier = set(), _links(INDEX.read_text(encoding="utf-8"))
        while frontier:
            current = frontier.pop()
            if current in seen or current not in notes:
                continue
            seen.add(current)
            frontier |= _links(notes[current])
        orphans = sorted(set(notes) - seen)
        assert not orphans, f"unreachable from INDEX: {orphans}"

    def test_every_note_is_linked_to_by_something(self, notes):
        """Reachability allows a long chain; being cited is a stronger check on
        the graph actually being connected rather than a linked list."""
        incoming = set()
        for text in [INDEX.read_text(encoding="utf-8"), *notes.values()]:
            incoming |= _links(text)
        uncited = sorted(set(notes) - incoming)
        assert not uncited, f"no note links to: {uncited}"


class TestContent:
    def test_core_concepts_are_present(self, notes):
        required = {
            "identification-problem",
            "rotation-indeterminacy",
            "point-vs-set-identification",
            "cholesky-identification",
            "proxy-svar",
            "sign-restrictions",
            "local-projections",
        }
        assert required <= set(notes), f"missing: {sorted(required - set(notes))}"

    def test_hub_concepts_are_well_connected(self, notes):
        """The identification problem should be referenced widely; if it is not,
        the graph has been written as isolated summaries."""
        citations = sum(
            "identification-problem" in _links(t) for t in notes.values()
        )
        assert citations >= 3

    def test_narrative_divergence_is_disclosed_in_the_graph(self, notes):
        text = notes["narrative-sign-restrictions"].lower()
        assert "rejection filter" in text
        assert "importance weight" in text

    def test_originality_of_the_text_is_stated(self):
        """The graph mirrors the handbook's structure but not its prose; that
        has to be said where a reader will see it."""
        text = INDEX.read_text(encoding="utf-8").lower()
        assert "original" in text
        assert "handbook" in text


class TestDiagram:
    """GRAPH.md is generated; these guard against it drifting from the notes."""

    def test_diagram_is_current(self, notes):
        """Regenerating must be a no-op. If this fails, run
        `pyvartoolbox-graph-diagram` and commit the result."""
        from pyvartoolbox._graph import build_page, parse_notes

        current = (GRAPH / "GRAPH.md").read_text(encoding="utf-8")
        assert build_page(parse_notes(GRAPH)) == current

    def test_every_note_appears_as_a_node(self, notes):
        text = (GRAPH / "GRAPH.md").read_text(encoding="utf-8")
        missing = sorted(slug for slug in notes if f"    {slug}[" not in text)
        assert not missing, f"absent from the diagram: {missing}"

    def test_edges_were_extracted(self, notes):
        from pyvartoolbox._graph import parse_notes

        parsed = parse_notes(GRAPH)
        total = sum(len(n["edges"]) for n in parsed.values())
        assert total >= 40, "relations are not being parsed"

    def test_no_edge_points_outside_the_graph(self):
        from pyvartoolbox._graph import parse_notes

        parsed = parse_notes(GRAPH)
        for slug, note in parsed.items():
            for _, target in note["edges"]:
                assert target in parsed, f"{slug} -> {target} is dangling"

    def test_foundations_are_grouped_by_layer_not_type(self):
        """Every foundational note is type 'concept', but so are cross-cutting
        ones — grouping on type alone silently over-collects."""
        from pyvartoolbox._graph import _group_of

        assert _group_of({"layer": "foundation", "type": "concept"}) == "foundation"
        assert _group_of({"layer": "", "type": "inference"}) == "inference"
        assert _group_of({"layer": "", "type": "concept"}) == "other"

    def test_mermaid_block_is_present_and_closed(self):
        text = (GRAPH / "GRAPH.md").read_text(encoding="utf-8")
        assert text.count("```") == 2
        assert "```mermaid" in text
        assert "graph LR" in text
