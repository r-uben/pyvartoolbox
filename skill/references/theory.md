# VAR and SVAR foundations

Enough theory to choose and defend an identification strategy. Notation follows
Cesa-Bianchi's VAR Handbook so the two can be read together; his sections are
cited as `[Handbook §x]` where a derivation is wanted.

## The reduced form

A VAR(p) in `nvar` variables `y_t`:

```
y_t = A_1 y_{t-1} + ... + A_p y_{t-p} + c + u_t,      E[u_t u_t'] = Σ_u
```

Every equation has the same regressors, so equation-by-equation OLS is the
system's GLS estimator — a single least-squares solve suffices. `Σ_u` is
generally **non-diagonal**: the reduced-form innovations are correlated, which is
precisely why they cannot be read as economic shocks. [Handbook §2.1]

In this package: `VARmodel(y, nlags=p, det=1)`, giving `.beta`, `.ar_coefs`
(shape `(p, nvar, nvar)`), `.sigma`, `.resid`.

## The structural form

The structural shocks `ε_t` are mutually orthogonal with unit variance
(`Σ_ε = I`), and map to the reduced form through the **impact matrix** `B`:

```
u_t = B ε_t
```

Everything structural follows from `B`. [Handbook §2.2]

## The identification problem

Taking the covariance of both sides:

```
Σ_u = E[u_t u_t'] = B E[ε_t ε_t'] B' = B B'
```

Identification means choosing a `B` satisfying `Σ_u = B B'`. The problem is that
this is `nvar(nvar+1)/2` equations — `Σ_u` is symmetric — in `nvar²` unknowns.
For `nvar = 2` that is 3 equations in 4 unknowns; the system is underdetermined
and has infinitely many solutions. [Handbook §2.5]

Concretely: if `B` solves it, so does `BQ` for **any** orthonormal `Q`, since

```
(BQ)(BQ)' = B Q Q' B' = B B' = Σ_u
```

Every identification scheme is a rule for picking one `B` out of that family.
That is the whole subject. The schemes differ only in what they assume in order
to choose:

- **Cholesky** — impose `nvar(nvar-1)/2` zeros above the diagonal of `B`, i.e. a
  recursive contemporaneous ordering. Exactly enough restrictions to pin `B`.
- **Long-run** — impose the zeros on the *cumulative* effect instead.
- **Proxy/IV** — use an outside variable correlated with one shock and nothing
  else. Identifies one column, leaves the rest unidentified.
- **Sign restrictions** — do not pin `B` at all. Keep every `Q` whose implied
  responses have the right signs, and report the resulting *set*.

## The Wold (moving-average) representation

A stable VAR inverts to an infinite MA:

```
y_t = Ψ_0 u_t + Ψ_1 u_{t-1} + ...,      Ψ_0 = I
Ψ_h = Σ_{j=1}^{min(h,p)} A_j Ψ_{h-j}
```

Structural impulse responses are then `Θ_h = Ψ_h B`, so `Θ_h[i, j]` is the
response of variable `i` at horizon `h` to shock `j`. [Handbook §2.3]

This package computes `Ψ` by the recursion above rather than by powering the
companion matrix — cheaper and better conditioned at long horizons. The two are
asserted equal in the test suite.

## Stability

Write the VAR(p) as a VAR(1) in companion form:

```
F = [A_1 A_2 ... A_p ]
    [ I   0  ...  0  ]
    [ 0   I  ...  0  ]
```

The VAR is stable iff every eigenvalue of `F` has modulus < 1. Unstable VARs
produce impulse responses that explode rather than decay, and long-run
identification is not even defined when `I - ΣA_j` is singular. [Handbook §2.4]

```python
m.max_eig()    # < 1 means stable
m.is_stable()
```

**Always check this.** A near-unit root also invalidates bootstrap bands: the
resampled draws go explosive and dominate the percentiles at long horizons.
`bootstrap_irf` reports how many draws it discarded for that reason.

## Variance decomposition

The share of the `h`-step forecast error variance of variable `i` attributable
to shock `j`:

```
VD[h, i, j] = Σ_{l=0}^{h} Θ_l[i, j]²  /  Σ_j Σ_{l=0}^{h} Θ_l[i, j]²
```

Shares lie in `[0, 1]` and sum to one across shocks — under a *fully*
identifying scheme. Under proxy identification only one column is meaningful and
the rest are returned as zero, so they do not sum to one. [Handbook §6.2]

## Historical decomposition

Back out the structural shocks (`ε = B⁻¹ u`) and push each one separately
through the companion recursion, so the observed path decomposes into the
cumulated contribution of each shock plus the initial condition and the
deterministic terms. The components sum to the data exactly — `decomp.check(y)`
asserts it. [Handbook §6.3]

This needs an invertible `B`, which is why partially identifying schemes
internally complete `B` to full rank even though only one column has economic
content.

## Local projections

Instead of iterating one model forward, estimate a separate regression per
horizon:

```
y_{t+h} = β_h s_t + controls + e_{t+h}
```

`β_h` *is* the impulse response at horizon `h`. Advantages: robust to
misspecification of the dynamics, easy to make non-linear or state-dependent.
Cost: less efficient, and the estimates are not constrained to be a coherent
system.

The horizon-`h` residual is MA(`h`) by construction — overlapping windows — so
inference must be HAC. This package uses Newey-West with bandwidth equal to the
horizon. [Handbook §7]

## Further reading

The upstream VAR Handbook (`VAR_Handbook.pdf` in the MATLAB repository) is the
authoritative treatment and includes derivations omitted here. It is written
against the MATLAB API, so its code examples do not apply to this package —
see `api.md` and `conventions.md` for the differences.
