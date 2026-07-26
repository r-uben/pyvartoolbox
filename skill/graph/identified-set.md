---
type: inference
implemented_by: sign_restricted_irf
---

# The identified set

The collection of `B` matrices consistent with both the data and the
restrictions. Reported as pointwise percentiles across accepted draws.

By default this package also redraws coefficients from their
[[posterior-draws|posterior]], so bands mix parameter and identification
uncertainty — matching upstream. `posterior=False` isolates identification
alone; the gap between the two shows how much width is estimation.

Do not say "we are 68% confident the response lies in this range". Do not treat
the median as an estimator — see [[fry-pagan-critique]].

## Relations

- produced by → [[sign-restrictions]]
- contrasts with → [[bootstrap-inference]]
- caveat → [[fry-pagan-critique]]
