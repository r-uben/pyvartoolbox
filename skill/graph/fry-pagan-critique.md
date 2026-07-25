---
type: pitfall
severity: medium
---

# The Fry-Pagan critique

In a set-identified model, the pointwise **median** response across accepted
draws need not correspond to *any single* admissible model. Each horizon's
median may come from a different rotation, so the median path can be one no
`B` in the [[identified-set]] actually generates.

Consequences:

- do not describe the median as "the estimate"
- do not compute quantities that require internal consistency — a
  [[historical-decomposition]], say — from the median path

The usual remedy is to report a specific admissible draw, such as the one
closest to the median in Frobenius distance (the "Fry-Pagan draw"), alongside
the set.

## Relations

- applies to → [[sign-restrictions]], [[narrative-sign-restrictions]]
- qualifies → [[identified-set]]
