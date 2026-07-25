# Worked end-to-end recipes

Copy-paste starting points. Every one runs against the shipped datasets, so they
can be executed before substituting the user's data.

## 1. Recursive VAR with bootstrap bands

```python
import pyvartoolbox as vt
from pyvartoolbox.datasets import load

y = load("sw2001_data")               # inflation, unemployment, fed funds
m = vt.VARmodel(y, nlags=4, det=1)
assert m.is_stable(), m.max_eig()

b = vt.bootstrap_irf(m, horizon=23, nboot=1000, ci=0.90, seed=0)
print("discarded draws:", b.ndiscarded)          # sanity-check before plotting

fig = vt.plot_irf(b.irf, b.lower, b.upper,
                  var_names=["inflation", "unemployment", "fed funds"])
fig.savefig("irf.png")
```

## 2. Proxy SVAR, compared against Cholesky

The comparison is the point: if they disagree, the ordering assumption is doing
the work.

```python
y, z = load("gk2015_data"), load("gk2015_iv")
m = vt.VARmodel(y, nlags=12, det=1)

chol = m.irf(horizon=47, ident="chol")
iv   = m.irf(horizon=47, ident="iv", iv=z)

# Only shock 0 is identified under IV; columns 1+ are zeros by design.
vt.plot_irf(iv, shocks=[0], var_names=["1yr rate", "CPI", "IP", "EBP"])
```

## 3. Sign restrictions

```python
import numpy as np

y = load("uhlig2005_data")
m = vt.VARmodel(y, nlags=12, det=1)

# One restricted shock: contractionary monetary policy.
R = np.array([[0.0], [-1.0], [-1.0], [0.0], [-1.0], [1.0]])

res = vt.sign_restricted_irf(m, R, horizon=59, ndraws=500,
                             sr_hor=6, ci=0.68, seed=0)
print(f"acceptance {res.acceptance_rate:.1%}")
vt.plot_irf(res.median, res.lower, res.upper, shocks=[0])
```

Report the band as the identified set, not a confidence interval — see
`inference.md`.

## 4. Narrative restrictions

```python
from pyvartoolbox import NarrativeDominance, NarrativeSign

y = load("adrr2018_data")
t = int(load("adrr2018_narrperiod")[0, 0]) - 1     # October 1979
m = vt.VARmodel(y, nlags=12, det=0)                # the paper drops the constant

res = vt.sign_restricted_irf(
    m, R, horizon=59, ndraws=500, sr_hor=6, ci=0.68, seed=0,
    narrative=[NarrativeSign(t, 0, 1), NarrativeDominance(t, 0, 5)],
)
```

Expect low acceptance and say that results follow upstream's rejection filter
rather than the paper's importance weighting.

## 5. Historical decomposition

```python
d = m.hd(ident="chol")
assert d.check(m.y)                    # components reconstruct the data
vt.plot_hd(d, variable=0)
```

## 6. Local projections, OLS and IV

```python
data = load("jt2025_data")
lp = vt.local_projection(
    endo=data[:, 0], treat=data[:, 1], ctrl=data[:, 2:],
    nlags=4, horizon=17, unit_shock=True, long_diff=True,
)

ivd = load("jt2025iv_data")
lpiv = vt.local_projection(
    endo=ivd[:, 0], treat=ivd[:, 1], ctrl=ivd[:, 2:],
    nlags=6, horizon=48, unit_shock=True, long_diff=True,
    iv=load("jt2025iv_iv").ravel(), nlags_iv=6,
)
print("median first-stage F:", float(np.nanmedian(lpiv.first_stage_f)))
vt.plot_lp(lpiv, title="Unemployment response to a policy shock")
```

Remember: lags of the outcome are not added automatically. `ctrl` here already
contains the outcome.

## 7. Restyling every figure

```python
vt.use_style(overrides={"color": {"primary": "#8c1d40"},
                        "font": {"size": 11}})
```

Or point at a replacement YAML: `vt.use_style("house_style.yaml")`.

## 8. Large bootstraps

```python
b = vt.bootstrap_irf(m, horizon=40, nboot=5000, seed=0, backend="jax")
```

Requires `pyvartoolbox[jax]`. Supports `chol` and `longrun`. Agrees with the
numpy path draw-for-draw to 1e-10, because both consume the same resample
indices.

## Standard checklist before reporting anything

1. `m.is_stable()`
2. Lag order justified — this package does not select it for you; `statsmodels`
   has the information criteria if needed
3. `b.ndiscarded` small relative to `nboot`
4. For set-identified work, `res.acceptance_rate` neither near 0 nor near 1
5. For IV, first-stage strength checked
6. The identification assumption stated explicitly in the write-up
