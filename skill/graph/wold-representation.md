---
type: concept
layer: foundation
handbook: "§2.3"
implemented_by: VARmodel.wold
---

# Wold (moving-average) representation

A stable VAR inverts to an infinite MA:

```
Ψ_0 = I,   Ψ_h = Σ_{j=1..min(h,p)} A_j Ψ_{h-j}
```

Structural responses are `Θ_h = Ψ_h B`.

Computed by this recursion rather than by powering the [[companion-form]] —
cheaper and better conditioned at long horizons. The two are asserted equal in
the test suite.

## Relations

- requires → [[stability]]
- equivalent to → powers of [[companion-form]]
- combined with `B` gives → [[impulse-response]]
