---
type: index
---

# VAR/SVAR concept graph

**[See the rendered diagram](GRAPH.md)** — 25 concepts and their relations, drawn
from these notes.

Atomic, wikilinked notes on the econometrics behind this package. Each note is
one concept, states relations explicitly, and cites the section of the upstream
VAR Handbook where a fuller derivation lives.

Written for machine reading as much as human: short notes, explicit typed
relations, no narrative that must be held in working memory across sections.
The text is original — the handbook supplied the structure, coverage and
notation, not the prose. See [[../references/validation|validation]] for what
this package verifies.

## Foundations

- [[reduced-form-var]] — what OLS gives you, and why it is not structural
- [[structural-var]] — orthogonal shocks and the impact matrix `B`
- [[identification-problem]] — more unknowns than equations
- [[rotation-indeterminacy]] — `B` and `BQ` are observationally equivalent
- [[wold-representation]] — the MA form responses are read from
- [[companion-form]] — VAR(p) as VAR(1)
- [[stability]] — check it before anything else

## What gets reported

- [[impulse-response]]
- [[variance-decomposition]]
- [[historical-decomposition]]

## Identification schemes

Point-identified:

- [[cholesky-identification]] — a recursive ordering
- [[long-run-restrictions]] — neutrality in the limit
- [[proxy-svar]] — an external instrument

Set-identified:

- [[sign-restrictions]] — signs only
- [[narrative-sign-restrictions]] — signs plus dated episodes
- [[sign-plus-iv]] — an instrument plus signs for the rest

## Inference

- [[point-vs-set-identification]] — the distinction that governs everything
- [[bootstrap-inference]]
- [[posterior-draws]]
- [[identified-set]]
- [[newey-west-inference]]

## Alternative estimator

- [[local-projections]]

## Pitfalls

- [[price-puzzle]] — the classic misidentification symptom
- [[fry-pagan-critique]] — why the median is not an estimate
- [[weak-instruments]]

## Suggested reading order

New to SVARs: [[reduced-form-var]] → [[identification-problem]] →
[[rotation-indeterminacy]] → [[point-vs-set-identification]] → the scheme you
intend to use.

Choosing a strategy: [[point-vs-set-identification]] then
[[../references/identification|the identification guide]].

## Viewing this as a graph

**Obsidian** is the best way — these notes are already wikilinked, so no
conversion is involved. Open this folder as a vault and press `⌘G` for Graph
View, or `⌘⇧G` for the local graph of whichever note is focused.

A `.obsidian/graph.json` ships with the folder, so nodes are coloured by the
`type` and `layer` frontmatter on first open: foundations blue, identification
schemes red, reported objects green, inference amber, pitfalls purple. Only that
file is tracked; the rest of Obsidian's workspace state is gitignored.

Foam, Logseq and Dendron read this layout directly too.

For a static picture that needs no tooling, [GRAPH.md](GRAPH.md) renders on
GitHub.
