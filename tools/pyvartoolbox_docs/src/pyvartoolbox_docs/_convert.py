"""Convert the upstream VAR Handbook from LaTeX into AI-readable markdown.

The handbook is written for a human reading a PDF: continuous prose, LaTeX
cross-references, figures placed by the typesetter. That is a poor format for a
model, which reads in fragments, cannot resolve ``\\ref{sec:wold}``, and cannot
see a figure. This produces the same content restructured to be read piecewise —
one file per section, frontmatter carrying the metadata, equations preserved as
LaTeX (which models parse well), and cross-references rewritten as links that
resolve.

The output is a derivative work of Ambrogio Cesa-Bianchi's handbook,
redistributed under the GPL-3.0 it already carries. Every generated file says so.

**The document is split before pandoc is invoked, not after.** Pandoc's LaTeX
reader is effectively non-terminating on the whole 3,700-line handbook — it runs
for minutes without finishing — while a single 375-line section converts in
0.06s. The cost is superlinear in document size, so sectioning first is what
makes this work at all, not merely a convenience for the output layout.

Maintainer tooling: the console script belongs to the ``pyvartoolbox-docs`` dev
workspace package, so it resolves inside a repo checkout only — installing
``pyvartoolbox`` does not put it on the PATH. Run::

    uv run pyvartoolbox-convert-handbook \\
        --tex path/to/VAR_Handbook.tex --outdir skill/handbook
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

SOURCE_URL = "https://github.com/ambropo/VAR-Toolbox"
PANDOC_TIMEOUT = 120

NOTICE = (
    "> **Source.** This page is a reformatted extract of the *VAR Handbook* by\n"
    "> Ambrogio Cesa-Bianchi, from the MATLAB VAR Toolbox ({url}). The content is\n"
    "> his; only the format has changed, so that it can be read in fragments by a\n"
    "> machine. Redistributed under the GPL-3.0 the original carries. Code\n"
    "> listings are **MATLAB** and do not apply to `pyvartoolbox` — see\n"
    "> [conventions](../references/conventions.md) for where the APIs differ."
)

# Custom environments pandoc has no reader for. Rewritten into standard ones
# rather than taught to pandoc via a Lua filter, which would add a moving part
# for no extra fidelity.
_CODE_ENVIRONMENTS = (
    ("matlabcode", "matlab"),
    ("matlaboutput", "text"),
    ("matlabtableoutput", "text"),
    ("matlabsymbolicoutput", "text"),
)

SECTION = re.compile(r"^\\section\{(.+?)\}(?:\\label\{([^}]+)\})?", re.M)


def preprocess(tex: str) -> str:
    """Rewrite custom LaTeX environments into ones pandoc understands."""
    for name, lang in _CODE_ENVIRONMENTS:
        tex = re.sub(
            rf"\\begin\{{{name}\}}(.*?)\\end\{{{name}\}}",
            lambda m, lang=lang: (
                f"\n\\begin{{lstlisting}}[language={lang}]{m.group(1)}"
                f"\\end{{lstlisting}}\n"
            ),
            tex,
            flags=re.S,
        )
    # A notebox is an aside; a blockquote reads as one in markdown too.
    tex = re.sub(
        r"\\begin\{notebox\}(.*?)\\end\{notebox\}",
        r"\n\\begin{quote}\1\\end{quote}\n",
        tex,
        flags=re.S,
    )
    # The final section runs to \end{document}, which pandoc rejects when fed a
    # fragment rather than a whole file.
    tex = tex.replace(r"\end{document}", "")
    return _strip_figures(tex)


def _balanced(text: str, open_at: int) -> tuple[str, int]:
    """Return the contents of the brace group starting at ``open_at``.

    A regex cannot do this: captions contain nested commands such as
    ``\\scshape{...}``, and a non-greedy ``\\{(.*?)\\}`` stops at the first inner
    closing brace, producing LaTeX that no longer parses.
    """
    depth, index = 0, open_at
    while index < len(text):
        char = text[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[open_at + 1 : index], index + 1
        index += 1
    raise ValueError("unbalanced braces")


def _strip_figures(tex: str) -> str:
    """Drop figure floats, keeping the caption as an aside.

    The images are not shipped and a model cannot see them regardless, but the
    caption often carries the only statement of what is being shown.
    """
    out, cursor = [], 0
    while True:
        start = tex.find(r"\begin{figure}", cursor)
        if start == -1:
            out.append(tex[cursor:])
            return "".join(out)
        end = tex.find(r"\end{figure}", start)
        if end == -1:
            out.append(tex[cursor:])
            return "".join(out)
        end += len(r"\end{figure}")
        block = tex[start:end]

        caption = ""
        marker = block.find(r"\caption{")
        if marker != -1:
            try:
                caption, _ = _balanced(block, marker + len(r"\caption") )
            except ValueError:
                caption = ""
        caption = re.sub(r"\\[a-zA-Z]+\s*", " ", caption)
        caption = re.sub(r"[{}]", "", caption).strip()

        out.append(tex[cursor:start])
        if caption:
            out.append(f"\n\\begin{{quote}}\\textbf{{Figure.}} {caption}\\end{{quote}}\n")
        cursor = end


def split_tex(tex: str) -> list[tuple[str, str, str]]:
    """Split on ``\\section`` into ``(title, label, body)``, dropping the preamble."""
    matches = list(SECTION.finditer(tex))
    if not matches:
        raise ValueError("no \\section found; is this the handbook?")
    out = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(tex)
        title = re.sub(r"\\[a-zA-Z]+|[{}\\]", "", match.group(1)).strip()
        out.append((title, match.group(2) or "", tex[match.end() : end]))
    return out


def run_pandoc(tex: str) -> str:
    """LaTeX to GitHub-flavoured markdown, keeping maths as ``$...$``."""
    result = subprocess.run(
        [
            "pandoc",
            "--from=latex",
            # GFM for fenced code blocks with a language tag and pipe tables,
            # both of which read far better than markdown_strict's indented
            # code and raw HTML tables. Its two maths quirks are normalised in
            # rewrite_links.
            "--to=gfm+tex_math_dollars",
            "--wrap=none",
            "--markdown-headings=atx",
        ],
        input=tex,
        capture_output=True,
        text=True,
        timeout=PANDOC_TIMEOUT,
    )
    if result.returncode != 0:
        detail = result.stderr.strip().splitlines()
        raise RuntimeError(detail[-1] if detail else "pandoc failed")
    return result.stdout


def slugify(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-") or "section"


def rewrite_links(body: str, anchors: dict[str, str]) -> str:
    """Turn LaTeX cross-references into links that resolve.

    Unresolvable references are stripped to plain text rather than left as dead
    targets — a reader following one learns nothing, and a model may hallucinate
    what was behind it.
    """

    def replace(match):
        target = anchors.get(match.group(1))
        return f"[{match.group(1)}]({target})" if target else "that section"

    # GFM writes display maths as a ```math fence and inline maths as $`x`$.
    # Both are GitHub-specific; normalise to the $$ / $ conventions that models
    # and every other renderer expect.
    body = re.sub(
        r"``` ?math\n(.*?)\n```",
        lambda m: f"$$\n{m.group(1)}\n$$",
        body,
        flags=re.S,
    )
    body = re.sub(r"\$`([^`]+)`\$", r"$\1$", body)

    # Cross-references arrive as raw HTML anchors: noise to read, and dead once
    # the document is split into files.
    body = re.sub(
        r'<a href="#[^"]*"[^>]*data-reference="([^"]+)"[^>]*>.*?</a>',
        replace,
        body,
        flags=re.S,
    )
    body = re.sub(r"\[\\\[([^\]]+?)\\\]\]\(#[^)]+\)", replace, body)
    body = re.sub(r"\\ref\{([^}]+)\}", replace, body)
    body = re.sub(r"\\eqref\{([^}]+)\}", r"equation (\1)", body)
    # A $$ block is already display maths; the inner equation environment and
    # its label are redundant and break some renderers.
    body = re.sub(r"\$\$\s*\\begin\{equation\*?\}", "$$", body)
    body = re.sub(r"\\end\{equation\*?\}\s*\$\$", "$$", body)
    body = re.sub(r"\\label\{[^}]+\}", "", body)
    return body


def convert(tex_path: Path, outdir: Path) -> list[Path]:
    tex = preprocess(tex_path.read_text(encoding="utf-8", errors="replace"))
    sections = split_tex(tex)

    anchors = {
        label: f"{index:02d}-{slugify(title)}.md"
        for index, (title, label, _) in enumerate(sections, start=1)
        if label
    }

    outdir.mkdir(parents=True, exist_ok=True)
    written, failures = [], []
    for index, (title, label, body) in enumerate(sections, start=1):
        name = f"{index:02d}-{slugify(title)}.md"
        try:
            markdown = rewrite_links(run_pandoc(body), anchors).strip()
        except (RuntimeError, subprocess.TimeoutExpired) as exc:
            failures.append((title, str(exc)))
            continue
        frontmatter = [
            "---",
            f'title: "{title}"',
            f'label: "{label}"' if label else 'label: ""',
            "source: VAR Handbook (Cesa-Bianchi)",
            "type: reformatted-extract",
            "licence: GPL-3.0",
            "---",
        ]
        path = outdir / name
        path.write_text(
            "\n".join(
                [
                    *frontmatter,
                    "",
                    f"# {title}",
                    "",
                    NOTICE.format(url=SOURCE_URL),
                    "",
                    markdown,
                    "",
                ]
            ),
            encoding="utf-8",
        )
        written.append(path)

    index_path = outdir / "INDEX.md"
    index_path.write_text(_index(written), encoding="utf-8")
    written.append(index_path)
    if failures:
        for title, error in failures:
            print(f"  skipped {title!r}: {error}", file=sys.stderr)
    return written


def _index(written: list[Path]) -> str:
    lines = [
        "---",
        'title: "VAR Handbook — reformatted"',
        "type: index",
        "source: VAR Handbook (Cesa-Bianchi)",
        "---",
        "",
        "# VAR Handbook, reformatted for machine reading",
        "",
        NOTICE.format(url=SOURCE_URL),
        "",
        "Generated by `pyvartoolbox-convert-handbook`. **Do not hand-edit** —",
        "regenerate instead. One file per section, equations kept as LaTeX,",
        "cross-references rewritten as links that resolve.",
        "",
        "Regenerating is maintainer tooling and needs a repo checkout: the",
        "command ships with the `pyvartoolbox-docs` dev workspace package, not",
        "with the installed library.",
        "",
        "For the same theory as short linked notes written against *this*",
        "package's API and conventions, see [the concept graph](../graph/INDEX.md).",
        "The handbook documents the MATLAB interface; where the two disagree on",
        "an API detail, this package's [conventions](../references/conventions.md)",
        "are authoritative for `pyvartoolbox`.",
        "",
        "## Sections",
        "",
    ]
    for path in written:
        title = re.sub(r"^\d+-", "", path.stem).replace("-", " ")
        lines.append(f"- [{title}]({path.name})")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="pyvartoolbox-convert-handbook",
        description="Reformat the upstream VAR Handbook LaTeX into markdown.",
    )
    parser.add_argument("--tex", type=Path, required=True, help="VAR_Handbook.tex")
    parser.add_argument("--outdir", type=Path, default=Path("skill/handbook"))
    args = parser.parse_args(argv)

    if not args.tex.exists():
        print(f"not found: {args.tex}", file=sys.stderr)
        return 1
    written = convert(args.tex, args.outdir)
    print(f"wrote {len(written)} files to {args.outdir}")
    return 0
