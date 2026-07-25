---
type: pitfall
severity: high
---

# Weak instruments

[[proxy-svar]] and IV [[local-projections]] both assume the instrument is
relevant. When correlation with the target shock is weak:

- the impact scaling becomes large and unstable
- 2SLS is biased toward OLS, and conventional standard errors understate it
- the reported precision is misleading rather than merely wide

`local_projection` reports `first_stage_f` per horizon. For the VAR case,
inspect the first-stage fit directly. The conventional rule of thumb (F > 10) is
a rough screen, not a test.

## Relations

- threatens → [[proxy-svar]], [[local-projections]]
- diagnosed by → first-stage F
