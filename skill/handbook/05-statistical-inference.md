---
title: "Statistical Inference"
label: "sec:inference"
source: VAR Handbook (Cesa-Bianchi)
type: reformatted-extract
licence: GPL-3.0
---

# Statistical Inference

> **Source.** This page is a reformatted extract of the *VAR Handbook* by
> Ambrogio Cesa-Bianchi, from the MATLAB VAR Toolbox (https://github.com/ambropo/VAR-Toolbox). The content is
> his; only the format has changed, so that it can be read in fragments by a
> machine. Redistributed under the GPL-3.0 the original carries. Code
> listings are **MATLAB** and do not apply to `pyvartoolbox` — see
> [conventions](../references/conventions.md) for where the APIs differ.

The figures produced in Section [sec:ident](04-identification-in-the-var-toolbox.md) display point estimates: impulse responses computed at the OLS parameter values $(\hat\Phi,\hat\Sigma_u)$, with no indication of sampling uncertainty. This section describes how the VAR Toolbox quantifies uncertainty around those point estimates.[^1]

How uncertainty is quantified depends on whether the identification scheme is *point-identified* or *set-identified*. Point-identified schemes — Cholesky, long-run, exogenous-variable, and external-instrument identification — uniquely determine the structural impact matrix $B$ from the reduced-form parameters $(\Phi,\Sigma_u)$. Uncertainty about structural objects therefore has a single source: *parameter uncertainty*, the finite-sample variability in the estimated $(\hat\Phi,\hat\Sigma_u)$ that carries through to impulse responses, variance decompositions, and historical decompositions. Set-identified schemes — sign restrictions, narrative sign restrictions, and their combination with external instruments — admit many rotation matrices $Q$ at any fixed $(\Phi,\Sigma_u)$: even in large samples, the data do not select a unique $B$. These schemes face an additional source: *identification uncertainty*, the irreducible non-uniqueness of the identified set that persists as $T\to\infty$ and cannot be reduced by collecting more data. The two sources are qualitatively different and call for qualitatively different inferential procedures.

By default, the toolbox accounts for parameter uncertainty; it can be switched off to return point estimates only. The field controls parameter uncertainty across all identification schemes. For point-identified models, parameter uncertainty is quantified via bootstrapping. For sign-restricted models, it is quantified via a Bayesian approach following ; frequentist alternatives exist but are not implemented. When , no parameter uncertainty is incorporated: point-identified models return point estimates only, and sign-restricted models draw rotations at the OLS estimates $(\hat\Phi,\hat\Sigma_u)$, so the distribution of accepted draws reflects identification uncertainty alone. When (the default), parameter uncertainty is included: point-identified models compute bootstrap confidence bands, and sign-restricted models draw $(\Phi,\Sigma_u)$ from their posterior before drawing rotations, so the resulting distribution reflects both sources of uncertainty jointly.

## Bootstrap Inference (Point-Identified Models)

For short-run, long-run, exogenous-variable, and external-instrument identification, the structural impact matrix $B$ is uniquely determined by the reduced-form parameters. Setting activates bootstrapping; all computations are performed internally by . Two variants are available, controlled by :

- <u>*Residual bootstrap*</u> (): at each draw, a new artificial sample is constructed by resampling the estimated residuals *with replacement* and feeding them through the estimated VAR, starting from the actual initial observations $x_1, \ldots, x_p$. This preserves the autocorrelation structure of the data but assumes the residuals are identically distributed over time.

- <u>*Wild bootstrap*</u> (): each residual is multiplied by an independent Rademacher variable ($+1$ or $-1$ with equal probability). This relaxes the homoskedasticity assumption and is the preferred choice when residuals display time-varying variance.

For external instruments (), the wild bootstrap is the recommended default. Reduced-form VAR residuals in macroeconomic and financial data typically display conditional heteroskedasticity — the residual variance varies over time, rising in volatile periods and falling in calm ones. The residual bootstrap assumes the residuals are identically distributed and therefore misrepresents this time variation; the wild bootstrap preserves the conditional variance at each date, delivering asymptotically valid inference under heteroskedasticity of unknown form. A further advantage in the proxy-SVAR setting is that reflecting each observation by $\pm 1$ preserves the time-series structure of the instrument — including the zeros in subsamples where surprises are unavailable — which resampling with replacement would scramble. The field controls the number of bootstrap replications (default: 1000) and sets the confidence level (default: 95).

No standalone example is introduced here.[^2] Setting before calling is all that is required; the call and all other options remain unchanged.

## Bayesian Inference (Sign-Restricted Models)

Sign-restricted VARs face both parameter uncertainty and identification uncertainty. The VAR Toolbox addresses them jointly via the Bayesian approach of . The prior over $(\Phi, \Sigma_u)$ is the conjugate Normal-Inverse-Wishart distribution, which yields a closed-form posterior of the same family. For each accepted draw $d = 1, \ldots, D$:

1.  Draw $\Sigma_u^{(d)}$ from the marginal Inverse-Wishart posterior.

2.  Conditional on $\Sigma_u^{(d)}$, draw $\Phi^{(d)}$ from the Normal conditional posterior; retain the draw only if the implied VAR is stable (all eigenvalues of the companion matrix strictly inside the unit circle).

3.  Compute the Cholesky factor $P^{(d)}$ of $\Sigma_u^{(d)}$. Draw a random orthogonal matrix $Q_j$ from the Haar measure on the space of $k \times k$ orthogonal matrices, via the QR factorization of a $k \times k$ matrix with i.i.d. standard normal entries.

4.  Form $B_j^{(d)} = P^{(d)} Q_j$ and check whether the implied impact responses satisfy all sign restrictions.

5.  If yes, retain $(B_j^{(d)}, \Phi^{(d)})$. If no, discard and return to step 3.

Steps 1–2 are executed only when . As discussed in Section that section, when inference is disabled via , $(\Phi, \Sigma_u)$ are fixed at their OLS estimates and only steps 3–5 are executed, so the distribution of accepted draws reflects identification uncertainty alone. Each accepted draw is a joint draw from the posterior over the reduced-form parameters *and* over the set of admissible rotations; the resulting credible bands reflect both sources of uncertainty.

The combined scheme is an exception: is always the OLS IV point estimate and is not updated at steps 1–2, regardless of the flag. The credible bands for the IV-identified shock therefore do not reflect parameter uncertainty. Embedding parameter uncertainty for the IV-identified shock requires integrating the instrument into the model likelihood directly, as in ; this is a qualitatively different model class and is not currently supported by the VAR Toolbox.

## Output Fields and Naming Convention

The uncertainty bands are stored in the output struct returned by , following a consistent naming convention. For impulse responses, the relevant fields are:

- — full array of draws, indexed along the fourth dimension; size $(h \times k \times k \times D)$, where $h$ is the number of horizons, $k$ the number of variables, and $D$ the number of draws.

- — pointwise *mean* across the $D$ draws. This is the central-tendency field for *point-identified* schemes.

- — pointwise *median* across the $D$ draws. This is the central-tendency field for *set-identified* (sign-restricted) schemes.

- — the Fry-Pagan median-target response (Section that section, Box that section): the impulse response of the single accepted rotation whose impact matrix is closest to the pointwise-median impact matrix in Frobenius norm. Populated for sign-restricted schemes only.

- , — lower and upper percentile bands at level .

The point estimate of the central tendency thus follows a different convention across the two families: (the mean) for point-identified schemes and (the median), together with the Fry-Pagan draw , for sign-restricted schemes. The percentile bands and are constructed in the same way in both cases. Recall that for point-identified schemes these fields are populated only when (the default); when , only the point-estimate field is available. For sign-restricted models, always populates , , , , and , since the rotation draws are themselves the source of uncertainty.[^3] Section [sec:dynamic](06-structural-dynamic-analysis.md) describes how the plotting functions , , and use these fields to display uncertainty bands alongside point estimates.

[^1]: Variance decompositions and historical decompositions, introduced in Section [sec:dynamic](06-structural-dynamic-analysis.md), are affected by exactly the same sources of uncertainty and are treated analogously.

[^2]: Section [sec:dynamic](06-structural-dynamic-analysis.md) presents a worked example in which the sign-restriction model of Section that section is re-estimated with .

[^3]: Variance decompositions and historical decompositions follow analogous conventions. For point-identified schemes with bootstrap inference, the central-tendency fields are (pointwise mean) and (a struct with a subfield and other components). For sign-restricted models, the central-tendency fields are (unchanged) and (now a struct with a subfield); the band fields and are likewise structs with and other subfields. The fields , , are unchanged across both identification families. These objects are documented in Sections that section and that section respectively, where they are formally defined.
