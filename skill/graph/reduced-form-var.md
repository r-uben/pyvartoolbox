---
type: concept
layer: foundation
handbook: "§2.1"
implemented_by: pyvartoolbox.model.VARmodel
---

# Reduced-form VAR

`y_t = A_1 y_{t-1} + ... + A_p y_{t-p} + c + u_t`, with `E[u_t u_t'] = Σ_u`.

Every equation shares the same regressors, so equation-by-equation OLS is the
system's GLS estimator — one least-squares solve suffices.

The essential fact: **`Σ_u` is not diagonal**. The reduced-form innovations are
contemporaneously correlated, so they cannot be read as economic shocks. That
correlation is the entire reason [[identification-problem]] exists.

## Relations

- produces → [[wold-representation]], [[companion-form]]
- must satisfy → [[stability]]
- maps to → [[structural-var]] via [[identification-problem]]
