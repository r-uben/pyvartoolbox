---
type: scheme
handbook: "§4.3"
identifies: a set
call: sign_restricted_irf
---

# Sign restrictions (Uhlig)

Assume only the *signs* of some responses, over some horizons. Draw Haar-uniform
rotations (see [[rotation-indeterminacy]]), keep those satisfying the pattern,
report the resulting [[identified-set]].

`+1` non-negative, `-1` non-positive, `0` unrestricted. `sr_hor` extends the
pattern beyond impact.

**The method's virtue is that it admits what it cannot pin down.** Uhlig's own
result is that the output response to a monetary shock straddles zero once you
stop assuming a recursive ordering. A band containing zero is a finding.

Acceptance rate is diagnostic: near zero means near-infeasible restrictions;
near one means they are not binding and are doing no identifying work.

## Relations

- exploits → [[rotation-indeterminacy]]
- is → [[point-vs-set-identification|set-identified]]
- summarised by → [[identified-set]], subject to [[fry-pagan-critique]]
- tightened by → [[narrative-sign-restrictions]]
- rebuts → [[cholesky-identification]]
