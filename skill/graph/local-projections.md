---
type: method
handbook: "§7"
implemented_by: pyvartoolbox.lp.local_projection
---

# Local projections (Jordà)

A separate regression per horizon:

```
y_{t+h} = β_h s_t + controls + e_{t+h}
```

`β_h` *is* the [[impulse-response]] at horizon `h`.

Trade-off against a VAR: robust to misspecified dynamics and easy to extend to
non-linear or state-dependent settings, but less efficient, and the estimates
are not constrained to form a coherent system.

Overlapping windows make the horizon-`h` residual MA(`h`), so inference must be
HAC — see [[newey-west-inference]].

**Lags of the outcome are not added automatically.** Include the outcome in
`ctrl` if you want them; forgetting is a common under-specification.

With an instrument, each horizon is 2SLS with Frisch-Waugh partialling; check
[[weak-instruments]].

## Relations

- alternative estimator of → [[impulse-response]]
- requires → [[newey-west-inference]]
- IV variant shares assumptions with → [[proxy-svar]]
