---
type: scheme
handbook: "§4.6"
call: 'sign_restricted_irf(..., iv=z)'
---

# Sign restrictions combined with an instrument

[[proxy-svar]] identifies shock 0; [[sign-restrictions]] identify others within
its orthogonal complement. Shock 0 is held fixed across rotations, so `R` has at
most `nvar - 1` columns.

With `nvar = 2` the complement is one-dimensional: no rotational freedom remains
and the second column is determined up to sign. Surprising, not a bug.

## Relations

- composes → [[proxy-svar]] + [[sign-restrictions]]
- constrains → [[rotation-indeterminacy]] to a subspace
