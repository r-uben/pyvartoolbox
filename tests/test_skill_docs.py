"""Keep the skill documentation honest.

Reference docs rot silently: an API is renamed, the markdown still describes the
old name, and an agent reading it confidently writes code that cannot run. These
tests make that a CI failure rather than a user's problem.
"""

import re
from pathlib import Path

import pytest

import pyvartoolbox as vt

SKILL = Path(__file__).parent.parent / "skill"
REFERENCES = SKILL / "references"


def _read(path):
    return path.read_text(encoding="utf-8")


def _importable(name: str) -> bool:
    """True if `from pyvartoolbox import <name>` would succeed."""
    if hasattr(vt, name):
        return True
    import importlib

    try:
        importlib.import_module(f"pyvartoolbox.{name}")
    except ImportError:
        return False
    return True


@pytest.fixture(scope="module")
def all_docs():
    return {p.name: _read(p) for p in [SKILL / "SKILL.md", *REFERENCES.glob("*.md")]}


class TestStructure:
    def test_skill_file_exists_with_frontmatter(self):
        text = _read(SKILL / "SKILL.md")
        assert text.startswith("---\n")
        block = text.split("---", 2)[1]
        assert re.search(r"^name:\s*\S+", block, re.M)
        assert re.search(r"^description:\s*\S+", block, re.M)

    def test_description_states_when_to_use(self):
        """A skill without trigger clauses never fires."""
        block = _read(SKILL / "SKILL.md").split("---", 2)[1]
        description = block.split("description:", 1)[1]
        assert "Use when" in description or "use when" in description

    def test_every_reference_linked_from_skill_exists(self):
        text = _read(SKILL / "SKILL.md")
        linked = set(re.findall(r"references/([a-z_]+\.md)", text))
        assert linked, "SKILL.md links to no reference files"
        for name in linked:
            assert (REFERENCES / name).exists(), f"missing {name}"

    def test_every_reference_file_is_linked(self):
        """An orphan reference will never be read."""
        text = _read(SKILL / "SKILL.md")
        for path in REFERENCES.glob("*.md"):
            assert path.name in text, f"{path.name} is not linked from SKILL.md"


class TestApiClaims:
    """The important one: names the docs promise must actually exist."""

    def test_documented_public_names_exist(self, all_docs):
        referenced = set()
        for text in all_docs.values():
            referenced |= set(re.findall(r"\bvt\.([A-Za-z_][A-Za-z0-9_]*)", text))
            referenced |= set(
                re.findall(r"\bpyvartoolbox\.([A-Za-z_][A-Za-z0-9_]*)", text)
            )
        # Submodules are legitimate references but are not package attributes
        # until imported.
        submodules = {"datasets", "replications", "style", "sign", "ident", "hd", "lp"}
        missing = sorted(
            n for n in referenced - submodules if not hasattr(vt, n)
        )
        assert not missing, f"documented but absent from the package: {missing}"

    def test_documented_import_names_exist(self, all_docs):
        names = set()
        for text in all_docs.values():
            for match in re.findall(
                r"from pyvartoolbox import ([A-Za-z_, ]+)", text
            ):
                names |= {n.strip() for n in match.split(",") if n.strip()}
        assert names
        # A submodule is a valid import target even though hasattr() is False
        # until something imports it.
        missing = sorted(n for n in names if not _importable(n))
        assert not missing, f"documented import targets missing: {missing}"

    def test_documented_datasets_exist(self, all_docs):
        from pyvartoolbox.datasets import available

        shipped = set(available())
        referenced = set()
        for text in all_docs.values():
            referenced |= set(re.findall(r'load\("([a-z0-9_]+)"\)', text))
        missing = sorted(referenced - shipped)
        assert not missing, f"documented datasets not shipped: {missing}"

    def test_documented_identification_names_are_real(self, all_docs):
        from pyvartoolbox.ident import SCHEMES

        referenced = set()
        for text in all_docs.values():
            referenced |= set(re.findall(r'ident="([a-z+]+)"', text))
        unknown = sorted(referenced - set(SCHEMES))
        assert not unknown, f"docs mention unimplemented schemes: {unknown}"


class TestConsistencyWithBehaviour:
    """Claims that would quietly become false if the code changed."""

    def test_partial_scheme_list_matches_the_docs(self):
        from pyvartoolbox.ident import PARTIAL

        text = _read(REFERENCES / "conventions.md")
        assert "iv" in PARTIAL
        assert "zeros" in text.lower()

    def test_axis_order_claim_holds(self, y_small):
        """conventions.md promises (horizon, variable, shock) everywhere."""
        m = vt.VARmodel(y_small, nlags=2)
        h, nvar = 6, m.nvar
        assert m.irf(horizon=h).shape == (h + 1, nvar, nvar)
        assert m.vd(horizon=h).shape == (h + 1, nvar, nvar)
        assert m.hd().shock.shape == (m.y.shape[0], nvar, nvar)

    def test_horizon_counting_claim_holds(self, y_small):
        m = vt.VARmodel(y_small, nlags=2)
        assert m.irf(horizon=23).shape[0] == 24

    def test_vd_is_shares_not_percent(self, y_small):
        m = vt.VARmodel(y_small, nlags=2)
        assert m.vd(horizon=5).max() <= 1.0

    def test_attribution_is_present_and_unambiguous(self):
        text = _read(SKILL / "SKILL.md").lower()
        assert "cesa-bianchi" in text
        assert "unofficial" in text
        assert "gpl-3.0" in text

    def test_narrative_divergence_is_disclosed(self):
        """The one methodological difference a user could publish without
        noticing. It must appear in the identification reference."""
        text = _read(REFERENCES / "identification.md").lower()
        assert "importance weight" in text
        assert "rejection filter" in text
