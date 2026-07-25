# Inference: what each band actually means

Three different objects in this package are drawn as a shaded region around a
line. They are not interchangeable, and conflating them is the most common way
to misreport a VAR result.

| Object | Produced by | Uncertainty represented |
| --- | --- | --- |
| Bootstrap band | `bootstrap_irf` | Parameter (sampling) uncertainty |
| Identified-set band | `sign_restricted_irf(..., posterior=False)` | Identification only |
| Posterior band | `sign_restricted_irf(...)` (default) | Both |
| Newey-West band | `local_projection` | Parameter uncertainty, HAC |

---

## Bootstrap bands (point-identified schemes)

For Cholesky, long-run and proxy identification, `B` is pinned by the
assumptions. The only uncertainty is that the VAR coefficients are estimated.

```python
b = vt.bootstrap_irf(m, horizon=40, nboot=1000, ci=0.90, method="resid", seed=0)
```

Two resampling schemes, both regenerating the series recursively from the
estimated VAR and re-estimating on each artificial sample:

- `"resid"` — iid resampling of residual **rows**, preserving contemporaneous
  correlation across equations.
- `"wild"` — Rademacher signs. Robust to conditional heteroskedasticity, which
  is the usual reason to prefer it on financial or monthly data.

These are **percentile** bands. No bias correction is applied — upstream does not
apply one either. Kilian (1998) is the standard reference if the user needs it;
it is not implemented here.

**`ndiscarded` matters.** Draws whose re-estimated VAR is explosive are dropped,
because they dominate the percentiles at long horizons. A large count means the
point estimate sits near the stability boundary and the bands should not be
trusted. Check it before quoting anything.

---

## Set-identified inference

Sign and narrative restrictions do not pin `B`. There is a *set* of admissible
impact matrices, and reporting requires care.

By default the VAR coefficients are also redrawn from their flat-prior
Normal-inverse-Wishart posterior before each rotation, matching upstream's
`SR.m`, so the bands reflect **both** parameter and identification uncertainty:

```python
res = vt.sign_restricted_irf(m, R, horizon=40, ndraws=1000, ci=0.68, seed=0)
```

Setting `posterior=False` holds the coefficients at their OLS estimates and
varies only the rotation. Those bands describe the identified set alone. They
are **not** comparable to published sign-restriction figures, but the gap
between the two is informative: it tells you how much of the width is
identification rather than estimation.

### How to describe these to a user

- Not a confidence interval. Do not say "we are 68% confident the response lies
  in this range".
- The **median** across draws is not an estimator of anything — it is a summary
  of the set, and the draw achieving it may differ at each horizon. The
  Fry-Pagan critique applies: no single admissible model need generate the
  median path at every horizon.
- A band containing zero means the restrictions are consistent with no effect.
  That is a result. Uhlig's paper exists to make exactly that point.

### Acceptance rate

`res.acceptance_rate` is diagnostic. Very low acceptance means the restrictions
are close to infeasible and the retained set may be a strange corner of the
parameter space. Very high acceptance means the restrictions are barely binding
and are not doing identification work.

---

## Local projections

`local_projection` returns Newey-West standard errors with bandwidth equal to
the horizon, because the horizon-`h` projection residual is MA(`h`) by
construction — the projection windows overlap.

```python
lp = vt.local_projection(y, shock, ctrl=X, nlags=4, horizon=20, ci=0.95)
lp.ir, lp.se, lp.lower, lp.upper
```

Bands are **pointwise** and use the normal quantile, as upstream does. They are
not joint bands over horizons; do not read "the response is significant
somewhere in the first 20 quarters" off them without a joint test.

Under LP-IV, check `first_stage_f` before interpreting magnitudes. Weak
instruments inflate 2SLS estimates in ways the standard errors do not capture.

---

## What cannot be reproduced

Bootstrap draws, posterior draws and rotation sampling all consume a random
number stream. Results are reproducible **within** this package under a fixed
`seed`, but cannot be matched draw-for-draw against MATLAB, which has a
different generator. This is a property of the methods, not a defect.

Where exactness matters, use the point estimates: those are validated against
MATLAB to 1e-7 or better. See `validation.md`.
