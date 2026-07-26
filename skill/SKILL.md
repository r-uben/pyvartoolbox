---
name: pyvartoolbox
description: Estimate structural VARs and local projections in Python — Cholesky, long-run, sign, narrative sign, proxy SVAR (external instruments), and sign+IV identification, with impulse responses, variance decompositions, historical decompositions, bootstrap and posterior inference. Use when the user wants to identify a structural shock, estimate a VAR or SVAR, compute IRFs/FEVD/HD, run local projections (OLS or IV), choose an identification strategy, or replicate a monetary-policy-shock paper. Also use when the user names Uhlig, Blanchard-Quah, Gertler-Karadi, Antolin-Diaz & Rubio-Ramirez, Stock-Watson, or Jorda-Taylor in an empirical-macro context.
---

# pyvartoolbox

Structural VAR and local-projection analysis. Python port of Ambrogio
Cesa-Bianchi's MATLAB VAR Toolbox, validated against it — see
`references/validation.md` for what "validated" means and where it stops.

## Orientation

Read this file for the decision, then the one reference file you need. Do not
read them all.

| You need to | Read |
| --- | --- |
| Choose an identification strategy | `references/identification.md` |
| Understand the econometrics | `references/theory.md` |
| Traverse the theory as a linked graph | `graph/INDEX.md` |
| Read the original handbook derivations | `handbook/INDEX.md` |
| Know what a band means before quoting it | `references/inference.md` |
| Call the API correctly | `references/api.md` |
| Debug a result that looks wrong | `references/conventions.md` |
| Copy a working end-to-end script | `references/workflows.md` |

## Install

```bash
uv add "pyvartoolbox[plot]"
```

## The 30-second version

```python
import pyvartoolbox as vt

m = vt.VARmodel(y, nlags=4)              # y is (nobs, nvar), OLS with a constant
assert m.is_stable()                     # always check
irf = m.irf(horizon=40, ident="chol")    # (41, nvar, nshock)
bands = vt.bootstrap_irf(m, horizon=40, nboot=1000, seed=0)
vt.plot_irf(bands.irf, bands.lower, bands.upper)
```

`irf[h, i, j]` is the response of **variable i** at **horizon h** to **shock j**.
That ordering is consistent across `irf`, `vd` and `hd`.

## Choosing an identification scheme

This is the only decision that matters; everything else is mechanics. Ask what
the user is willing to assume, not what is convenient.

| Assumption they can defend | Scheme | Call |
| --- | --- | --- |
| A recursive ordering of contemporaneous effects | Cholesky | `ident="chol"` |
| Some shock has no permanent effect on some variable | Long-run | `ident="longrun"` |
| They have an instrument correlated with one shock only | Proxy SVAR | `ident="iv", iv=z` |
| Only the *signs* of some responses | Sign restrictions | `sign_restricted_irf(...)` |
| Signs, plus what happened on a specific date | Narrative | `narrative=[...]` |
| An instrument *and* signs for the other shocks | sign+IV | `sign_restricted_irf(..., iv=z)` |

**Default to being sceptical of Cholesky.** It is the easy choice and is
frequently indefensible: it asserts that variable 1 is unaffected within the
period by every other shock. For monetary policy in monthly or quarterly data
that is a strong claim, and it is what produces the "price puzzle" that proxy
SVARs were introduced to fix. If the user reaches for Cholesky, ask what ordering
they are asserting and why.

**Point- versus set-identification is not a detail.** Cholesky, long-run, proxy
and exogenous identification return one answer. Sign and narrative restrictions
return a *set*, and the bands mean something different. Read
`references/inference.md` before describing any interval to a user.

## Three things that cause wrong answers

1. **Ordering matters even for proxy SVARs.** The instrument identifies the
   shock to the **first column of `y`**. Put the instrumented variable first.
2. **Sign-restriction bands are not confidence intervals.** They mix parameter
   and identification uncertainty and are not comparable to bootstrap bands.
3. **`ident="iv"` returns zeros for shocks 1 onward.** Only the first shock is
   identified. That is correct, not a bug.

Full list in `references/conventions.md`.

## Validation status

Four of the six upstream replications match MATLAB numerically (1e-7 to 1e-12).
The two rejection-sampler exercises are validated more weakly, by construction.
Bootstrap, posterior and rotation sampling cannot be matched across RNG streams
and are tested through distributional properties instead. Do not describe this
package as "verified" without that nuance — `references/validation.md` has the
exact claims.

## Attribution

The econometrics and design are Cesa-Bianchi's
(<https://github.com/ambropo/VAR-Toolbox>); this is an unofficial Python
reimplementation under GPL-3.0, not affiliated with or endorsed by him. Cite the
original toolbox and its VAR Handbook in research, not this package.
