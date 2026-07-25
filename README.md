# pyvartoolbox

VAR and local-projection analysis in Python.

> ## Attribution
>
> **This is an unofficial Python replication of someone else's work.** The
> original is the MATLAB [VAR Toolbox](https://github.com/ambropo/VAR-Toolbox)
> (v4.0) by **Ambrogio Cesa-Bianchi**, who wrote the algorithms, the
> identification schemes, and the accompanying VAR Handbook. This repository
> reimplements that toolbox in Python; the econometrics and the design are his,
> the Python is mine.
>
> It is a derivative work under the GPL-3.0, which is the licence the original
> carries. It is **not affiliated with, maintained by, reviewed by, or endorsed
> by** Ambrogio Cesa-Bianchi. Any bug here is mine, not his.
>
> For the authoritative implementation, the handbook, and the replication
> exercises, use the upstream MATLAB toolbox. If you use this package in
> research, cite the original (see [Citing](#citing)).

## Why this exists

`statsmodels` covers reduced-form VARs and recursive SVARs well. It does not
cover the identification schemes that most applied macro work now relies on:
proxy SVARs (external instruments), narrative sign restrictions, or historical
decompositions with bootstrap inference. The MATLAB VAR Toolbox does — and is
the de-facto reference for several of them — but only in MATLAB.

This package ports that functionality to numpy, with an optional JAX backend for
the parts that are genuinely expensive.

## Status: alpha

Working today:

| Feature | Status |
| --- | --- |
| Reduced-form VAR(p) by OLS, deterministic terms, exogenous regressors | ✅ |
| Companion form, stability check, Wold/MA representation | ✅ |
| Cholesky (zero contemporaneous) identification | ✅ |
| Long-run zero restrictions (Blanchard–Quah) | ✅ |
| Impulse responses and forecast error variance decomposition | ✅ |
| Residual and wild bootstrap percentile bands | ✅ |
| Sign restrictions / narrative sign restrictions | ⬜ planned |
| External instruments (proxy SVAR), IV + sign | ⬜ planned |
| Historical decompositions | ⬜ planned |
| Local projections (OLS and IV, Newey–West) | ⬜ planned |
| JAX backend for resampling | ⬜ planned |
| Validation against the six upstream replications | ⬜ planned |

See [`docs/roadmap.md`](docs/roadmap.md). **The numerical results have not yet
been validated against the MATLAB toolbox** — until the replication suite lands,
treat output as unverified against the reference.

## Install

```bash
uv add pyvartoolbox
# or, from a clone:
uv sync
```

## Quickstart

```python
import numpy as np
import pyvartoolbox as vt

y = ...  # (nobs, nvar) array, columns ordered for the recursive identification

m = vt.VARmodel(y, nlags=4)          # OLS, constant included by default
print(m.max_eig())                    # < 1 means stable

irf = m.irf(horizon=40)               # (41, nvar, nshock), Cholesky
vd = m.vd(horizon=40)                 # variance shares, sum to 1 across shocks

bands = vt.bootstrap_irf(m, horizon=40, nboot=1000, ci=0.90, seed=0)
bands.lower, bands.irf, bands.upper   # 5th pct, point estimate, 95th pct
```

`irf[h, i, j]` is the response of variable `i` at horizon `h` to a
one-standard-deviation structural shock `j`.

Long-run restrictions, on data entered in first differences:

```python
irf = m.irf(horizon=40, ident="longrun")
cum = irf.cumsum(axis=0)   # cum[-1, 0, 1] == 0 by construction
```

## Design notes

- **numpy is the reference implementation.** The optional JAX backend targets
  only the embarrassingly parallel layers — bootstrap replications and
  sign-restriction rejection sampling — where it buys one to two orders of
  magnitude. Estimation itself is a single small least-squares solve and gains
  nothing.
- **Float64 throughout.** VAR companion matrices and long-run restrictions are
  ill-conditioned; the JAX backend will require `jax_enable_x64`.
- Estimation uses `lstsq` rather than normal equations, because VAR regressors
  are collinear by construction and squaring the condition number is avoidable.

## Licence

GPL-3.0-or-later, inherited from the upstream VAR Toolbox. If you need a
permissively licensed VAR implementation, use `statsmodels` instead.

## Citing

Cite the original toolbox and handbook:

> Cesa-Bianchi, A. *VAR Toolbox*. https://github.com/ambropo/VAR-Toolbox
