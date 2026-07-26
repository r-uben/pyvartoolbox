"""Keep repository-only tooling out of the published distribution.

The handbook converter and the concept-graph renderer are maintainer tools: they
live in the `tools/pyvartoolbox_docs` workspace package and exist to regenerate
docs in this checkout. Nothing about them is useful to someone who runs
`pip install pyvartoolbox`, and their console scripts would squat on the user's
PATH.

Moving them out fixed one instance. These tests stop the next one, and they read
the *built wheel* rather than the source tree: a stray `packages` or `artifacts`
entry in the hatch config can re-include a file that `src/` layout alone would
have kept out. They skip when no matching wheel exists, so the suite stays
runnable without `uv build`.
"""

import configparser
import tomllib
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
DIST = ROOT / "dist"
DOCS_TOOL = ROOT / "tools" / "pyvartoolbox_docs"


def _pyproject(directory):
    with (directory / "pyproject.toml").open("rb") as fh:
        return tomllib.load(fh)


def _console_scripts(entry_points_text):
    parser = configparser.ConfigParser()
    # Script names are case-sensitive; configparser lower-cases option names by
    # default, which would mangle any name that is not already lower-case and
    # fail the comparison against pyproject.toml for a reason unrelated to
    # packaging. Invisible while every script happens to be lower-case.
    parser.optionxform = str
    parser.read_string(entry_points_text)
    if not parser.has_section("console_scripts"):
        return {}
    return dict(parser["console_scripts"])


@pytest.fixture(scope="module")
def library():
    return _pyproject(ROOT)["project"]


@pytest.fixture(scope="module")
def wheel(library):
    """The freshest wheel built from the version currently declared.

    A wheel for some other version is a stale artifact, not evidence about this
    source tree, so it counts as "not built" and the tests skip.
    """
    normalised = library["name"].replace("-", "_")
    candidates = sorted(
        DIST.glob(f"{normalised}-{library['version']}-*.whl"),
        key=lambda p: (p.stat().st_mtime, p.name),
    )
    if not candidates:
        pytest.skip(
            f"no {normalised}-{library['version']} wheel in dist/ — run `uv build`"
        )
    with zipfile.ZipFile(candidates[-1]) as archive:
        names = archive.namelist()
        entry_points = next(
            (n for n in names if n.endswith(".dist-info/entry_points.txt")), None
        )
        text = "" if entry_points is None else archive.read(entry_points).decode()
    return {"path": candidates[-1], "names": names, "scripts": _console_scripts(text)}


def test_no_documentation_tooling_module_ships(wheel):
    """Every module of the docs workspace package, by name, must be absent."""
    tooling = {
        p.name
        for p in (DOCS_TOOL / "src" / "pyvartoolbox_docs").glob("*.py")
        if p.name != "__init__.py"
    }
    assert tooling, "the docs tooling package is empty — this test proves nothing"
    shipped = sorted(n for n in wheel["names"] if Path(n).name in tooling)
    assert not shipped, f"documentation tooling in the wheel: {shipped}"


def test_wheel_ships_only_the_library_package(wheel, library):
    """Anything outside the package and its metadata got in by accident."""
    package = library["name"].replace("-", "_")
    strays = sorted(
        n
        for n in wheel["names"]
        if not n.startswith((f"{package}/", f"{package}-{library['version']}.dist-info/"))
    )
    assert not strays, f"unexpected members in the wheel: {strays}"


def test_declared_console_scripts_are_what_ships(wheel, library):
    """The wheel's entry points must match the declaration, exactly."""
    assert wheel["scripts"] == library.get("scripts", {})


def test_documentation_tooling_scripts_are_not_user_facing(wheel, library):
    """The maintainer scripts stay in the dev workspace, off the user's PATH."""
    tooling = set(_pyproject(DOCS_TOOL)["project"].get("scripts", {}))
    assert tooling, "the docs tooling declares no scripts — this test proves nothing"
    assert not tooling & set(wheel["scripts"])
    assert not tooling & set(library.get("scripts", {}))
