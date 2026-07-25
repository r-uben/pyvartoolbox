---
type: object
handbook: "§6.3"
implemented_by: VARmodel.hd
---

# Historical decomposition

Back out structural shocks (`ε = B⁻¹ u`) and push each separately through the
[[companion-form]] recursion, so the observed path splits into each shock's
cumulated contribution plus the initial condition and deterministic terms.

Components sum to the data exactly — `decomp.check(y)`.

Requires an **invertible** `B`, which is why [[proxy-svar]] internally completes
its single identified column to full rank even though the other columns carry no
economic content.

## Relations

- requires → invertible `B`, [[companion-form]]
- answers → "which shocks drove this episode", unlike [[impulse-response]]
