---
type: inference
handbook: "§5.2"
implemented_by: pyvartoolbox.posterior.draw_posterior
---

# Posterior draws

Flat (Jeffreys) prior gives a Normal-inverse-Wishart posterior centred on OLS:

```
Σ⁻¹ ~ Wishart(Σ̂⁻¹/T, T)
vec(B) | Σ ~ N(vec(B̂), Σ ⊗ (X'X)⁻¹)
```

Used to add parameter uncertainty to set-identified inference. Without it,
sign-restriction bands describe only the [[identified-set]] at fixed
coefficients and understate uncertainty.

Sampled via Bartlett decomposition and the Kronecker structure, avoiding both an
`O(T n²)` construction and forming the full `(k·nvar)²` covariance.

## Relations

- combines with → [[identified-set]]
- Bayesian counterpart of → [[bootstrap-inference]]
