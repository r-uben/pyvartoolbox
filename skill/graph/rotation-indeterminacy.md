---
type: concept
layer: foundation
handbook: "§2.5"
---

# Rotation indeterminacy

If `B` satisfies `Σ_u = B B'`, then so does `BQ` for **any** orthonormal `Q`:

```
(BQ)(BQ)' = B Q Q' B' = B B' = Σ_u
```

The data cannot distinguish `B` from `BQ`. This is the precise statement of
[[identification-problem]], and it is what [[sign-restrictions]] exploits: rather
than pinning `Q`, sample it and keep the draws whose implications are
economically acceptable.

Sampling `Q` must be Haar-uniform on the orthogonal group, or the resulting set
is biased. QR of a Gaussian matrix with the sign of each column fixed so `R` has
a non-negative diagonal — LAPACK's sign convention is otherwise arbitrary.

## Relations

- restates → [[identification-problem]]
- exploited by → [[sign-restrictions]], [[narrative-sign-restrictions]]
- constrained by → [[sign-plus-iv]] (rotates only a subspace)
