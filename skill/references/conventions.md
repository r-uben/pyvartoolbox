# Conventions and gotchas

Read this when a result looks wrong. Most surprises here are deliberate choices,
several of them places where this package deliberately differs from the MATLAB
original.

## Array layout

**`(horizon, variable, shock)` everywhere.** `irf`, `vd` and `hd.shock` all use
it.

```python
irf[h, i, j]   # response of variable i at horizon h to shock j
```

Upstream is inconsistent on this: `compute_IR.m` returns `(h, variable, shock)`
but `compute_VD.m` and `HD.shock` return `(h, shock, variable)`. If you are
porting MATLAB code or comparing outputs, transpose the last two axes of VD and
HD.

## Horizon counting

`irf(horizon=h)` returns `h + 1` rows covering horizons `0 .. h`. Upstream's
`nsteps = H` returns `H` rows covering `0 .. H-1`. To match `nsteps=24`, ask for
`horizon=23`.

## Variance decomposition scale

This package returns **shares in `[0, 1]`**. Upstream returns **percent**.
Multiply by 100 to compare.

## Coefficient layout

Deterministic terms are appended **after** the lag block, so
`beta[:nvar*nlags]` is always the autoregressive part regardless of which
deterministic terms are present. Upstream puts them first.

Consequence: raw coefficient vectors are not comparable across the two
implementations. Compare `sigma`, `resid`, `B`, `irf`, `vd`, `hd` — all
layout-invariant — never `beta`.

## Partial identification returns zeros

Under `ident="iv"`, only shock 0 is identified. `irf[:, :, 1:]` and
`vd[:, :, 1:]` are returned as **zeros**, not as the arbitrary numerical
completion used internally. Variance shares therefore do not sum to one. This is
correct reporting, not missing data.

The internal completion exists only so `B` is invertible for the historical
decomposition. Note it restores the identified column exactly *after* the
orthonormal completion, which breaks `B @ B.T == sigma` by construction —
upstream makes the same trade, on the grounds that exact shock-1 responses
matter and the other columns are meaningless anyway.

## Instrument alignment

`iv` is aligned on the **full** sample of `y`, not the residual sample, with
missing periods as `NaN`. The first `nlags` observations are dropped internally.
Leading and trailing gaps are trimmed; an interior gap raises.

## Ordering still matters under IV

The instrument identifies the shock to the **first column of `y`**. Proxy
identification frees you from assuming an ordering *among the other variables*,
not from choosing which variable is instrumented.

## Local projections do not add lags of the outcome

Unlike the VAR, `local_projection` does **not** automatically include lags of
`endo`. Pass the outcome among `ctrl` if you want to control for its own lags,
which is the usual specification. This mirrors upstream and is a common source
of accidentally under-specified projections.

## `ndraws` counts accepted draws

`sign_restricted_irf(ndraws=1000)` samples until 1000 draws are **accepted**,
not until 1000 are attempted. With a narrative filter accepting a few percent
this matters enormously. `max_reject` caps total attempts per requested draw.

## Long-run restrictions bind asymptotically

The cumulated response is zero in the limit, not at the plotted horizon. At 40
quarters expect something small but non-zero. Check the restriction at horizon
500+ if you want to verify it holds.

## Numerical tolerances

Agreement with MATLAB is not uniform, and the reason is conditioning rather than
correctness:

- Well-conditioned designs (4 lags, quarterly): 1e-10 to 1e-12.
- Gertler-Karadi (12 lags of monthly data, 49 regressors): **1e-7**. `cond(X)` is
  ~4.7e4 but `cond(X'X)` is ~2.2e9. Upstream solves via normal equations, which
  works with the squared conditioning; this package uses `lstsq`. At that level
  the difference is BLAS-ordering noise and is platform-dependent.

This package keeps `lstsq`. Matching a less accurate reference bit-for-bit is
not worth losing accuracy everywhere else.

## Stability is not checked for you

`VARmodel` will happily estimate an explosive VAR. Call `is_stable()`. An
unstable VAR gives exploding IRFs, meaningless long-run identification, and
bootstrap bands dominated by discarded draws.

## Float64 in the JAX backend

`backend="jax"` forces `jax_enable_x64` at import. float32 silently corrupts
long-horizon impulse responses, because the companion recursion compounds the
error. If you write your own JAX code against this package, do the same.

The JAX backend accelerates the **bootstrap** (~8x at `nboot=2000`). It is
deliberately *not* used for rotation sampling, where it measured 300x slower —
small QR decompositions dominated by dispatch overhead.
