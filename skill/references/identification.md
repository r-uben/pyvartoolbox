# Identification schemes

Each scheme: what it assumes, when it is defensible, how to call it, how it
fails. Read `theory.md` first if the identification problem itself is unclear.

---

## Cholesky — zero contemporaneous restrictions

**Assumption.** A recursive ordering: variable 1 is unaffected within the period
by every other shock, variable 2 only by shock 1, and so on. `B` is the lower
triangular Cholesky factor of `Σ_u`.

**When defensible.** When there is a genuine timing story — slow-moving real
variables that cannot react within the period to a financial shock, or a policy
rate that observes everything else contemporaneously and so goes last.

**When not.** Whenever the ordering is chosen for convenience. It is exactly
identifying, so it never fails visibly — a bad ordering produces a clean,
confident, wrong answer. In monetary VARs it typically generates the *price
puzzle*: prices rising after a contractionary shock. That is a symptom of
misidentification, not an economic finding.

```python
irf = m.irf(horizon=40, ident="chol")
```

Ordering is the column order of `y`. Reordering `y` is reordering the
identification.

**Diagnostic.** `irf[0]` must be lower triangular; the impact response of
variable 0 to shock 1 is exactly zero by construction.

---

## Long-run zero restrictions (Blanchard-Quah)

**Assumption.** Some shock has no permanent effect on some variable. The
classic case: demand shocks do not move output in the long run, supply shocks do.

The long-run multiplier is `C(1) = (I - Σ_j A_j)⁻¹`, and requiring the cumulated
structural response to be lower triangular gives
`C(1) B = chol(C(1) Σ_u C(1)')`.

```python
irf = m.irf(horizon=40, ident="longrun")
cum = irf.cumsum(axis=0)     # cum[-1, 0, 1] → 0
```

**Enter the data in the form the restriction applies to** — usually first
differences — so that "long run" means the cumulated response.

**Fails when** `I - Σ_j A_j` is singular, i.e. the VAR has a unit root. The
package raises with that diagnosis rather than returning nonsense. Difference
the data first.

**Caveat.** The restriction binds *asymptotically*. At 40 quarters the cumulated
response is small but not zero; do not treat a small non-zero value at the
plotted horizon as a bug.

---

## Proxy SVAR / external instruments (Gertler-Karadi)

**Assumption.** An observed instrument `z_t` is correlated with the shock of
interest (relevance) and with no other structural shock (exogeneity). Typical
instruments: high-frequency policy surprises around FOMC announcements,
narrative measures.

**Identifies one shock only.** Two-stage: project the first reduced-form
residual on the instrument, regress the remaining residuals on the fitted values
to get impact ratios, then scale by the shock size implied by the Gertler-Karadi
footnote-4 correction.

```python
# The instrumented variable must be FIRST in y.
irf = m.irf(horizon=48, ident="iv", iv=z)
irf[:, :, 0]      # the identified shock
irf[:, :, 1:]     # zeros — not identified, correctly reported as such
```

`z` is aligned on the **full** sample of `y`, with missing periods as `NaN`.
Leading and trailing gaps are trimmed; an interior gap raises, because the
two-stage regression needs a contiguous overlap.

**Why prefer it to Cholesky.** It does not require any ordering assumption among
the other variables, and it typically removes the price puzzle. That is the
empirical case for the whole approach.

**Check the instrument is strong.** A weak instrument gives a large, unstable
impact scaling. For local projections the package reports `first_stage_f`; for
the VAR case, inspect the first-stage fit before trusting the magnitudes.

---

## Sign restrictions (Uhlig)

**Assumption.** Only the *signs* of some responses, over some horizons. A
contractionary monetary shock raises the policy rate and lowers prices — but you
refuse to say by how much, or to order the variables.

**Set-identified.** There is no single answer. The sampler draws Haar-uniform
rotations `Q`, keeps those whose implied responses satisfy the pattern, and
reports the distribution over accepted draws.

```python
import numpy as np
R = np.array([[ 0.0],   # output: unrestricted
              [-1.0],   # prices: must not rise
              [ 1.0]])  # policy rate: must not fall
res = vt.sign_restricted_irf(m, R, horizon=40, ndraws=1000, sr_hor=6, seed=0)
res.median, res.lower, res.upper
```

- `+1` response must be non-negative, `-1` non-positive, `0` unrestricted.
- `sr_hor=6` imposes the pattern over the first six horizons, not just impact.
- Columns of `R` are shocks; you may restrict fewer shocks than there are
  variables, and usually should.

**The point of the method is that it is honest about what it cannot pin down.**
Uhlig's own result is that the output response to a monetary shock straddles
zero once you stop assuming a recursive ordering. A sign-restricted band that
includes zero is a finding, not a failure.

**Fails when** the pattern is infeasible for the data, or `max_rot` is too small.
The error distinguishes those cases. Note that leaving fewer free columns than
restrictions — for example `nvar=2` with an instrument already pinning one column
— can leave no rotational freedom at all.

---

## Narrative sign restrictions (Antolín-Díaz & Rubio-Ramírez)

**Assumption.** Sign restrictions *plus* statements about specific historical
dates: "the October 1979 monetary shock was positive", or "it was the dominant
driver of the funds rate that month".

```python
from pyvartoolbox import NarrativeSign, NarrativeDominance

res = vt.sign_restricted_irf(m, R, horizon=40, ndraws=1000, narrative=[
    NarrativeSign(period=t, shock=0, sign=1),
    NarrativeDominance(period=t, shock=0, variable=5),
])
```

`period` indexes the original sample; the lag trim is applied internally.

**Important divergence from the paper.** Upstream — and therefore this port —
applies narrative restrictions as a **rejection filter**: a draw violating any
constraint is discarded. The original paper instead *reweights* accepted draws
by an importance weight. The two agree on the support of the posterior but not
its shape, so results here will not exactly reproduce the paper's figures. Say
so when reporting.

**Expect low acceptance.** Narrative constraints can accept a few percent of
otherwise-valid draws. The sampler keeps going until `ndraws` are accepted, up
to `max_reject` attempts each, and warns if it falls short.

---

## Sign restrictions combined with an instrument

**Assumption.** An instrument identifies one shock; sign restrictions identify
others within the remaining space.

```python
res = vt.sign_restricted_irf(m, R_for_other_shocks, iv=z, horizon=40)
```

Shock 0 comes from the instrument and is held fixed across rotations; only its
orthogonal complement is rotated, so `R` has at most `nvar - 1` columns.

With `nvar = 2` the complement is one-dimensional — there is no rotational
freedom left and the remaining column is determined up to sign. That looks like
a bug and is not.

---

## Choosing, in practice

Ask in this order:

1. **Is there an instrument?** If a credible one exists, use it. It buys
   identification without an ordering assumption, and it is point-identified so
   inference is straightforward.
2. **Is there a defensible timing story?** Then Cholesky, and state the ordering
   explicitly as an assumption in the write-up.
3. **Is there a long-run neutrality claim?** Then long-run restrictions, on
   differenced data.
4. **Otherwise, sign restrictions** — and accept that some responses will be
   inconclusive. That is the honest answer, not a weaker one.
5. **Add narrative constraints** when there is a specific episode everyone
   agrees about. They tighten the set at the cost of an extra assumption.

Reporting more than one scheme on the same data is usually the strongest move:
agreement is evidence, disagreement locates the assumption that is doing the
work. The Gertler-Karadi replication in this package does exactly that.
