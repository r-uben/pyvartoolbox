---
type: concept
layer: foundation
handbook: "§2.4"
implemented_by: VARmodel.is_stable
severity: check-always
---

# Stability

Stable iff every eigenvalue of the [[companion-form]] has modulus < 1.

Consequences of ignoring it:

- impulse responses explode instead of decaying
- [[long-run-restrictions]] are undefined — `I - ΣA_j` is singular
- [[bootstrap-inference]] breaks down: explosive resampled draws dominate the
  percentiles at long horizons

`bootstrap_irf` reports `ndiscarded` for exactly this reason. A large count means
the point estimate sits near the boundary and the bands should not be trusted.

## Relations

- property of → [[companion-form]]
- precondition for → [[wold-representation]], [[long-run-restrictions]]
- diagnostic for → [[bootstrap-inference]]
