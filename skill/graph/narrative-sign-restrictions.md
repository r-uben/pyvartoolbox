---
type: scheme
handbook: "§4.4"
identifies: a set
divergence: rejection filter, not importance weighting
---

# Narrative sign restrictions (Antolín-Díaz & Rubio-Ramírez)

[[sign-restrictions]] plus claims about specific dates: the October 1979
monetary shock was positive; it was the dominant driver of the funds rate that
month.

Two constraint types:

- **sign** — the structural shock has a given sign on a date
- **dominance** — one shock accounts for more of a variable's move on that date
  than all others combined

**Known divergence.** Upstream, and therefore this package, applies these as a
*rejection filter*. The paper instead reweights accepted draws by an importance
weight. Same posterior support, different shape — results will not exactly
reproduce the paper. Disclose this when reporting.

Expect low acceptance; the sampler draws until `ndraws` are accepted.

## Relations

- extends → [[sign-restrictions]]
- diverges from → the published method (importance weighting)
- is → [[point-vs-set-identification|set-identified]]
