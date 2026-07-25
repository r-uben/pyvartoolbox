---
type: scheme
handbook: "§4.2"
call: 'ident="longrun"'
---

# Long-run zero restrictions (Blanchard-Quah)

Assumes some shock has no permanent effect on some variable — classically,
demand shocks do not move output in the long run.

With `C(1) = (I - Σ_j A_j)⁻¹`, requiring the cumulated response to be lower
triangular gives `C(1) B = chol(C(1) Σ_u C(1)')`.

Two practical points:

- Enter data in the form the restriction applies to, usually first differences.
- The restriction binds **asymptotically**. At 40 quarters the cumulated
  response is small but non-zero; that is not a bug.

Undefined when the VAR has a unit root — see [[stability]].

## Relations

- requires → [[stability]]
- is → [[point-vs-set-identification|point-identified]]
- contrasts with → [[cholesky-identification]] (restricts the limit, not impact)
