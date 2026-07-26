# API reference

Everything importable from `pyvartoolbox`. Shapes are stated because the layout
is the most common source of error — see `conventions.md`.

## Estimation

### `VARmodel(y, nlags, det=1, exog=None, dof_adjust=True)`

| Argument | Meaning |
| --- | --- |
| `y` | `(nobs, nvar)`; column order **is** the recursive ordering |
| `nlags` | lag order |
| `det` | `0` none, `1` constant, `2` +trend, `3` +trend² |
| `exog` | `(nobs, nexog)` contemporaneous regressors |
| `dof_adjust` | divide `sigma` by `neff - ncoef` rather than `neff` |

Attributes: `beta`, `resid`, `sigma`, `Y`, `X`, `det_names`, `nvar`, `neff`,
`ncoef`, `ar_coefs` `(nlags, nvar, nvar)`, `det_coefs` `(nvar, nextra)`.

Methods:

| Call | Returns |
| --- | --- |
| `companion()` | `(nvar*nlags, nvar*nlags)` |
| `max_eig()` / `is_stable()` | stability |
| `wold(horizon)` | `(horizon+1, nvar, nvar)` MA coefficients |
| `irf(horizon, ident, **kw)` | `(horizon+1, nvar, nshock)` |
| `vd(horizon, ident, **kw)` | shares in `[0,1]` |
| `hd(ident, **kw)` | `HistoricalDecomposition` |
| `simulate(resid, y0, X_extra=None)` | regenerate a path |

## Identification

**The rule: point-identified schemes are called by name, set-identified schemes
are sampled.** A point-identified scheme pins down a single impact matrix `B`,
so it is reachable through `ident=` and `impact_matrix`. A set-identified scheme
admits a whole family of admissible `B`, so there is nothing for a function to
return except a distribution, and it is reachable only through
`sign_restricted_irf`. The same rule places the code: `pyvartoolbox.ident` holds
the point-identified schemes and the dispatcher, `pyvartoolbox.sign` holds the
set-identified ones and the sampler.

| | Schemes | Call |
| --- | --- | --- |
| Point-identified | `"chol"`, `"longrun"`, `"iv"` | `ident=` / `impact_matrix` |
| Set-identified | sign, narrative sign, sign+instrument | `sign_restricted_irf` |

Passing a set-identified name to `ident=` raises and names
`sign_restricted_irf`. The scheme *is* implemented — the error means it has no
single `B` to hand back, not that it is missing.

```python
vt.impact_matrix(model, ident="chol", **kw)   # -> B, (nvar, nvar)
vt.proxy_iv(model, iv)                        # the IV scheme directly
vt.SCHEMES                                    # implemented names
vt.PARTIAL                                    # schemes identifying only shock 0
```

## Inference

### `bootstrap_irf(model, horizon=40, ident="chol", nboot=1000, method="resid", ci=0.90, seed=None, drop_unstable=True, backend="numpy")`

Returns `BootstrapIRF` with `irf`, `lower`, `upper`, `draws`, `median`, `ci`,
`ndiscarded`. `method` is `"resid"` or `"wild"`; `backend` is `"numpy"` or
`"jax"` (the latter supports `chol` and `longrun` only).

### `sign_restricted_irf(model, restrictions, horizon=40, ndraws=1000, sr_hor=1, max_rot=500, ci=0.90, seed=None, posterior=True, narrative=None, iv=None, max_reject=200)`

`restrictions` is `(nvar, nshock)` of `+1 / -1 / 0`. Returns
`SignRestrictedIRF` with `draws`, `lower`, `median`, `upper`, `naccepted`,
`nattempted`, `acceptance_rate`.

`narrative` is a list of:

```python
NarrativeSign(period, shock, sign)          # sign of a shock on a date
NarrativeDominance(period, shock, variable) # shock dominates a variable's move
```

`period` indexes the original sample.

### `draw_posterior(model, rng)` / `wishart(scale, df, rng)`

One draw from the flat-prior Normal-inverse-Wishart posterior; the drawn object
behaves like a `VARmodel`.

## Historical decomposition

```python
d = model.hd(ident="chol")
d.shock          # (nobs, nvar, nshock)
d.init, d.const, d.trend, d.total
d.deterministic  # const + trend
d.check(y)       # components reconstruct the data
```

First `nlags` rows are `NaN`; `init` has one fewer NaN row, since its `t=0`
state is the last presample period rather than a gap.

## Local projections

### `local_projection(endo, treat, ctrl=None, nlags=4, det=1, horizon=20, ci=0.95, unit_shock=False, long_diff=False, iv=None, nlags_iv=0)`

Returns `LocalProjection` with `ir`, `se`, `lower`, `upper`, `nobs`, `beta`,
`first_stage_f` (IV only). `newey_west_se(X, resid, nlags)` is exposed
separately.

## Plotting and style

```python
vt.plot_irf(irf, lower=None, upper=None, var_names=..., shocks=[0])
vt.plot_vd(vd); vt.plot_hd(decomp, variable=0); vt.plot_lp(lp)
vt.use_style(config=None, overrides=None)
vt.settings(); vt.palette(); vt.despine(ax)
```

All appearance lives in `config.yaml`. Each function returns the matplotlib
`Figure`.

## Datasets and replications

```python
from pyvartoolbox.datasets import load, available, COLUMNS
from pyvartoolbox import replications
replications.gertler_karadi_2015()   # and the other five
replications.run_all(outdir)
```

Command line: `pyvartoolbox-replicate all --outdir figures`.
