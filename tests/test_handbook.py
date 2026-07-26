"""The converted VAR Handbook: format guarantees and attribution.

The conversion exists so a model can read the handbook in fragments. These tests
assert the properties that serve that purpose — normalised maths, tagged code
fences, no dead cross-references — and that the attribution survives every
regeneration.
"""

import re
from pathlib import Path

import pytest

HANDBOOK = Path(__file__).parent.parent / "skill" / "handbook"


@pytest.fixture(scope="module")
def pages():
    files = sorted(p for p in HANDBOOK.glob("*.md") if p.name != "INDEX.md")
    if not files:
        pytest.skip("handbook not generated; run pyvartoolbox-convert-handbook")
    return {p.name: p.read_text(encoding="utf-8") for p in files}


class TestStructure:
    def test_sections_were_converted(self, pages):
        assert len(pages) >= 10

    def test_index_exists_and_links_every_page(self, pages):
        index = (HANDBOOK / "INDEX.md").read_text(encoding="utf-8")
        for name in pages:
            assert name in index, f"{name} missing from INDEX"

    def test_every_page_has_frontmatter(self, pages):
        for name, text in pages.items():
            assert text.startswith("---\n"), f"{name} has no frontmatter"
            block = text.split("---", 2)[1]
            assert "source: VAR Handbook" in block, name
            assert "licence: GPL-3.0" in block, name


class TestMachineReadableFormat:
    """The whole point of the conversion."""

    def test_no_github_specific_inline_maths(self, pages):
        """GFM writes inline maths as $`x`$, which only GitHub renders."""
        for name, text in pages.items():
            assert "$`" not in text, f"{name} still has GFM inline maths"

    def test_no_math_code_fences(self, pages):
        for name, text in pages.items():
            assert not re.search(r"^``` *math", text, re.M), f"{name} has a math fence"

    def test_display_maths_uses_dollars(self, pages):
        joined = "".join(pages.values())
        assert joined.count("$$") >= 20

    def test_no_raw_html_anchors(self, pages):
        for name, text in pages.items():
            assert "data-reference" not in text, f"{name} has raw HTML anchors"

    def test_no_unresolved_latex_references(self, pages):
        for name, text in pages.items():
            assert "\\ref{" not in text, f"{name} has a raw \\ref"
            assert "\\eqref{" not in text, f"{name} has a raw \\eqref"

    def test_code_blocks_are_tagged_with_a_language(self, pages):
        """An untagged fence tells a reader nothing about what it contains."""
        tagged = sum(len(re.findall(r"^``` \w+", t, re.M)) for t in pages.values())
        assert tagged >= 20

    def test_custom_environments_did_not_leak(self, pages):
        for name, text in pages.items():
            for env in ("matlabcode", "matlaboutput", "notebox"):
                assert f"\\begin{{{env}}}" not in text, f"{name} leaked {env}"


class TestAttribution:
    def test_every_page_credits_the_author(self, pages):
        for name, text in pages.items():
            assert "Cesa-Bianchi" in text, f"{name} lacks attribution"
            assert "GPL-3.0" in text, f"{name} lacks the licence"

    def test_every_page_warns_the_code_is_matlab(self, pages):
        """A reader following a listing into this package would be misled."""
        for name, text in pages.items():
            assert "MATLAB" in text, name
            assert "do not apply to" in text, name

    def test_index_points_at_our_own_docs(self):
        index = (HANDBOOK / "INDEX.md").read_text(encoding="utf-8")
        assert "graph/INDEX.md" in index
        assert "conventions.md" in index


class TestConverter:
    def test_balanced_brace_extraction(self):
        from pyvartoolbox._convert import _balanced

        text = r"\caption{Outer \scshape{Inner} tail}"
        content, _ = _balanced(text, text.index("{"))
        assert content == r"Outer \scshape{Inner} tail"

    def test_unbalanced_braces_are_reported(self):
        from pyvartoolbox._convert import _balanced

        with pytest.raises(ValueError, match="unbalanced"):
            _balanced("{no close", 0)

    def test_custom_environments_are_rewritten(self):
        from pyvartoolbox._convert import preprocess

        out = preprocess(r"\begin{matlabcode}x = 1;\end{matlabcode}")
        assert "lstlisting" in out and "language=matlab" in out

    def test_split_requires_sections(self):
        from pyvartoolbox._convert import split_tex

        with pytest.raises(ValueError, match="no .*section"):
            split_tex("no sections here")
