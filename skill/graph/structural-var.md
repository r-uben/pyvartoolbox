---
type: concept
layer: foundation
handbook: "§2.2"
---

# Structural VAR

The structural shocks `ε_t` are mutually orthogonal with unit variance
(`Σ_ε = I`) and relate to the reduced form through the **impact matrix** `B`:

```
u_t = B ε_t
```

Everything structural — [[impulse-response]], [[variance-decomposition]],
[[historical-decomposition]] — is a function of `B` and the reduced-form
dynamics. Choosing `B` *is* identification.

## Relations

- requires → [[reduced-form-var]]
- determined by → [[identification-problem]]
- yields → [[impulse-response]]
