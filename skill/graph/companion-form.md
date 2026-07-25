---
type: concept
layer: foundation
handbook: "§2.4"
implemented_by: VARmodel.companion
---

# Companion form

Stack a VAR(p) into a VAR(1):

```
F = [A_1 ... A_p]
    [ I  ...  0 ]
```

Used for [[stability]] (eigenvalues of `F`) and for the recursions behind
[[historical-decomposition]].

## Relations

- rewrites → [[reduced-form-var]]
- determines → [[stability]]
- drives → [[historical-decomposition]]
