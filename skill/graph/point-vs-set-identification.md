---
type: distinction
centrality: high
---

# Point versus set identification

The distinction that governs how results may be described.

**Point-identified** — [[cholesky-identification]], [[long-run-restrictions]],
[[proxy-svar]]. The assumptions pin `B`. The only uncertainty is that
coefficients are estimated, so [[bootstrap-inference]] gives a genuine
confidence band.

**Set-identified** — [[sign-restrictions]], [[narrative-sign-restrictions]].
The assumptions admit a *range* of `B`. There is no point estimate. Intervals
describe an [[identified-set]] and are **not** confidence intervals.

Conflating the two is the most common way to misreport a VAR result.

## Relations

- governs → [[bootstrap-inference]] vs [[identified-set]]
- source → [[identification-problem]]
