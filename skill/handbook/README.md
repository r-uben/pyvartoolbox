# Provenance

These files are **generated**. Do not hand-edit — regenerate with:

```bash
git clone --depth 1 https://github.com/ambropo/VAR-Toolbox.git
pyvartoolbox-convert-handbook --tex VAR-Toolbox/VAR_Handbook.tex --outdir skill/handbook
```

Requires `pandoc`.

## What the conversion does, and why

The handbook is written for a human reading a PDF. A model reads in fragments,
cannot resolve `\ref{sec:wold}`, and cannot see a figure. The converter:

- splits into one file per section, each independently readable
- normalises maths to `$...$` and `$$...$$` (pandoc's GFM writer emits GitHub's
  ``$`x`$`` and ```` ```math ```` fences, which only GitHub renders)
- rewrites cross-references as links that resolve, and drops the ones that
  cannot rather than leaving dead anchors
- keeps MATLAB listings as fenced blocks tagged with their language
- replaces figure floats with their captions, since the images are not shipped
  and would be invisible regardless

**The split happens before pandoc runs, not after.** Pandoc's LaTeX reader is
effectively non-terminating on the whole 3,700-line document — minutes without
finishing — while one 375-line section converts in 0.06s. Sectioning first is
what makes the conversion possible at all.

## Licence and attribution

The content is Ambrogio Cesa-Bianchi's. Only the format has changed. This is a
derivative work redistributed under the GPL-3.0 that the original carries, and
every generated page states so.

Code listings are **MATLAB** and do not apply to `pyvartoolbox`. Where the two
disagree on an API detail, [`../references/conventions.md`](../references/conventions.md)
is authoritative for this package.
