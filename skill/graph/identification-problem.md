---
type: concept
layer: foundation
handbook: "§2.5"
centrality: high
---

# The identification problem

Taking covariances of `u_t = B ε_t`:

```
Σ_u = B B'
```

`Σ_u` is symmetric, so this is `nvar(nvar+1)/2` equations in `nvar²` unknowns.
For two variables: 3 equations, 4 unknowns. **Underdetermined.**

Every identification scheme is a rule for choosing one `B` from the infinitely
many that satisfy it. The schemes differ only in what they assume in order to
choose — which is why the assumption, not the estimator, is what a referee
should attack.

## Relations

- caused by → non-diagonal `Σ_u` in [[reduced-form-var]]
- formalised by → [[rotation-indeterminacy]]
- resolved by → [[cholesky-identification]], [[long-run-restrictions]],
  [[proxy-svar]], [[sign-restrictions]]
- splits into → [[point-vs-set-identification]]
