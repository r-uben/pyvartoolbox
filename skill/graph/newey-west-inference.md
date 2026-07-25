---
type: inference
implemented_by: pyvartoolbox.lp.newey_west_se
---

# Newey-West (HAC) inference

Bartlett-weighted autocovariance sandwich. In [[local-projections]] the
bandwidth is the horizon, because the horizon-`h` residual is MA(`h`) by
construction.

Bands are **pointwise**, using the normal quantile. They do not support "the
response is significant somewhere in the first 20 quarters" — that needs a joint
test.

Bandwidth zero reduces to the White heteroskedasticity-robust sandwich.

## Relations

- required by → [[local-projections]]
- pointwise, unlike a joint band
