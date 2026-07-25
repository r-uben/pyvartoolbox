---
type: inference
handbook: "§5.1"
implemented_by: bootstrap_irf
---

# Bootstrap inference

For [[point-vs-set-identification|point-identified]] schemes. Regenerate the
series recursively from the estimated VAR, re-estimate, recompute responses,
take percentiles.

- `"resid"` — iid resampling of residual rows, preserving contemporaneous
  correlation
- `"wild"` — Rademacher signs; robust to conditional heteroskedasticity

No bias correction (Kilian 1998) is applied; upstream does not either.

Check `ndiscarded`: explosive draws are dropped, and a large count signals
[[stability]] problems that invalidate the bands.

## Relations

- valid for → [[point-vs-set-identification|point-identified]] schemes only
- diagnostic → [[stability]]
- distinct from → [[identified-set]], [[posterior-draws]]
