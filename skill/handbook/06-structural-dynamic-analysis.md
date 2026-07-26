---
title: "Structural Dynamic Analysis"
label: "sec:dynamic"
source: VAR Handbook (Cesa-Bianchi)
type: reformatted-extract
licence: GPL-3.0
---

# Structural Dynamic Analysis

> **Source.** This page is a reformatted extract of the *VAR Handbook* by
> Ambrogio Cesa-Bianchi, from the MATLAB VAR Toolbox (https://github.com/ambropo/VAR-Toolbox). The content is
> his; only the format has changed, so that it can be read in fragments by a
> machine. Redistributed under the GPL-3.0 the original carries. Code
> listings are **MATLAB** and do not apply to `pyvartoolbox` — see
> [conventions](../references/conventions.md) for where the APIs differ.

Section [sec:ident](04-identification-in-the-var-toolbox.md) has established how to identify the $B$ matrix that maps structural shocks $\varepsilon_t$ into the reduced-form innovations $u_t$ via $u_t = B\varepsilon_t$, using zero contemporaneous restrictions, zero long-run restrictions, sign restrictions, narrative sign restrictions, external instruments, identification with exogenous variables, or combinations thereof. Section [sec:inference](05-statistical-inference.md) has introduced the bootstrap and Bayesian procedures for quantifying uncertainty around the resulting structural objects. With an identified $B$ matrix in hand, one can define the three main tools of structural dynamic analysis, each addressing a distinct question about the role of shocks in driving economic fluctuations:

1.  <u>*How do shocks propagate over time?*</u>  When a structural shock hits the economy, how do the endogenous variables respond dynamically? This question is answered by *impulse response functions* (computed informally in each identification subsection of Section [sec:ident](04-identification-in-the-var-toolbox.md)).

2.  <u>*How important are different shocks on average?*</u>  What portion of the forecast error variance in our variables is attributable to each structural shock? This is quantified through *forecast error variance decompositions*.

3.  <u>*What drove specific historical episodes?*</u>  Looking back at the data, which structural shocks were responsible for pushing the economy away from its equilibrium at particular points in time? This is revealed by *historical decompositions*.

The three tools provide complementary perspectives on the role of structural shocks: impulse responses trace dynamic propagation, variance decompositions measure average importance, and historical decompositions attribute observed fluctuations to specific shocks. Together, they allow us to move beyond estimating a VAR to understanding the underlying economic forces that shape macroeconomic outcomes.

Sections that section–that section develop the mechanics of each tool; each subsection closes with its MATLAB implementation and the corresponding output figures from the built-in plotting functions. For the MATLAB implementation, this section uses the sign-restriction identification of Section that section. The only substantive change relative to that section is , which incorporates parameter uncertainty in the rotation draws and populates the /, /, and / fields of the output struct:

``` matlab
VARopt.ident     = 'sign';
VARopt.R         = [ 1, -1;  % Real GDP
                     1,  1]; % 1-year rate
VARopt.IV        = [];
VARopt.snames    = {bfeps('Demand'), bfeps('MonPol')};
VARopt.inference = 1;
VARopt.pick      = 0;
VARopt.firstdate = datesnum(1);
VARopt.frequency = 'q';
rng(4)
VAR_infer = VARmodel(X, nlags, detc, VARopt);
```

## Impulse Response Functions

Impulse response functions (henceforth, $IR$) answer the following question: *What is the response over time of each endogenous variable in the VAR to a one-time increase in one of the structural shocks, holding all other structural shocks at zero?* By isolating the impact of a single shock while keeping all else constant, impulse responses allow us to trace the causal effect of that shock on the economy. They capture both the *impact response* (the response at horizon $h=0$) and the *persistence* (how long it takes for the effect to dissipate).

For example, for a monetary policy shock that raises the policy rate unexpectedly, the impulse response function traces how much GDP falls, how long the effect persists, and how the 1-year Treasury rate responds over the adjustment period.

**<u>How to compute impulse response functions</u>.**  To understand how to compute impulse responses, we return to the simple bivariate structural VAR(1):
$$
\left[ 
\begin{array}{c}
y_{t} \\ 
r_{t}
\end{array}
\right] =
\begin{bmatrix}
\phi_{11} & \phi_{12} \\ 
\phi_{21} & \phi_{22}
\end{bmatrix}
\left[ 
\begin{array}{c}
y_{t-1} \\ 
r_{t-1}
\end{array}
\right] +
\begin{bmatrix}
b_{11} & b_{12} \\ 
b_{21} & b_{22}
\end{bmatrix}
\begin{bmatrix}
\varepsilon_{t}^{Demand} \\ 
\varepsilon_{t}^{MonPol}
\end{bmatrix}
$$
To compute the impulse response to a specific shock, we first define an *impulse selection vector* $s$ that picks out which shock we want to study. This is a $(k \times 1)$ vector that takes the value 1 for the shock of interest and 0 for all others. For example, to study the demand shock (the first shock), we set:
$$
s = \left[ 
\begin{array}{c}
1 \\ 
0
\end{array}
\right]
$$
The impulse response to $\varepsilon_t^{Demand}$ can then be computed using:
$$
x_t = \Phi x_{t-1} + Bs
$$
This equation describes how the system evolves when we “shock” it at time $t=0$ by setting $\varepsilon_0^{Demand} = 1$ (while keeping $\varepsilon_0^{MonPol} = 0$; here $Bs$ is the impact of the unit demand shock, not a structural shock entering the system every period), and then allow the system to evolve, setting $\varepsilon_h = 0$ for all $h \geq 1$.

More specifically, the impulse response at different horizons can be computed recursively:
$$
\left\{ 
\begin{array}{ll}
IR_0 = Bs & \quad \text{(impact response)} \\[6pt]
IR_h = \Phi \cdot IR_{h-1} & \quad \text{for } h = 1, 2, ..., H \text{ (dynamic responses)}
\end{array}
\right.

$$
Define $\Theta_h \equiv \Phi^h B$ (henceforth the *impulse response matrix* at horizon $h$; also written $IR_h$ in the MATLAB output). The $(i,j)$ element $(\Theta_h)_{ij}$ gives the response of variable $i$ to shock $j$ at horizon $h$. This is stored in the MATLAB array , with giving the response of variable $i$ to shock $j$ at horizon $h$ (MATLAB uses 1-based indexing, so horizon $h=0$ is stored in row 1).

**<u>Interpretation</u>.**  The impact response to shock $j$ is the $j$-th column of $B$. The rate at which the response dissipates is governed by the eigenvalues of $\Phi$ (or of the companion matrix $\mathcal{F}$ for $p > 1$): a dominant eigenvalue close to one in modulus implies slow decay; one close to zero implies rapid return to baseline. For a demand shock (first column of $B$), the impact responses are:
$$
IR_0 = 
\begin{bmatrix}
b_{11} & b_{12} \\ 
b_{21} & b_{22}
\end{bmatrix}
\begin{bmatrix}
1 \\ 
0
\end{bmatrix}
=
\begin{bmatrix}
b_{11} \\ 
b_{21}
\end{bmatrix}
$$
The response at horizon $h=1$ is then:
$$
IR_1 = \Phi \cdot IR_0 = 
\begin{bmatrix}
\phi_{11} & \phi_{12} \\ 
\phi_{21} & \phi_{22}
\end{bmatrix}
\begin{bmatrix}
b_{11} \\ 
b_{21}
\end{bmatrix}
=
\begin{bmatrix}
\phi_{11}b_{11} + \phi_{12}b_{21} \\ 
\phi_{21}b_{11} + \phi_{22}b_{21}
\end{bmatrix}
$$
and similarly for all subsequent horizons.

**<u>In MATLAB</u>.**  Once has been run, impulse responses are plotted with . The function takes the array, a populated structure, and optionally and for uncertainty bands. Two additional optional arguments, and , add a second (inner) uncertainty band when both are supplied. Key options: sets the save path; (default) produces one figure per shock; produces a single figure for shock $j$:

``` matlab
VARopt.figname = 'graphics/sign_IR';
VARirplot(VAR_infer.IRmed, VARopt, VAR_infer.IRinf, VAR_infer.IRsup);
```

Figure that section shows the output from the sign-restriction identification with identification and parameter uncertainty: the solid blue line shows the element-wise median impulse response (), while the shaded area spans the 95% credible bands.

> **Figure.** Impulse Responses with Uncertainty Bands

The figure reports one additional line beyond those plotted by . The solid red line is the Fry-Pagan median-target rotation (), the single accepted draw whose responses lie closest to the element-wise median (Box that section). The two summaries differ in general, but the gap is more visible here than in Figure that section: that figure set , whereas this one accounts for parameter uncertainty, which widens the dispersion across draws and separates the median-target rotation from the element-wise median (Box that section explains that this dispersion is not the fundamental source of the gap, only what makes it larger here). Note that the red line is not produced by but superimposed separately — see the Primer for the corresponding code.

> **Growth-rate IRFs versus level IRFs.**  The VAR Toolbox computes impulse responses for the variables as they enter the VAR — in our running example, the *log-difference* of US real GDP, i.e. the quarterly growth rate. The impulse response $IR_h^y$ measures how many percentage points the growth rate deviates from baseline $h$ periods after the shock.
>
> This is often not the object of interest. When the question concerns the *level* of output — e.g. “a monetary easing raises the level of GDP by $x\%$” — the relevant object is the *cumulative impulse response*:
> $$
> \begin{equation*}
> \sum_{i=0}^{h} IR_i^y.
> \end{equation*}
> ```
> This follows directly from the Wold representation: since $y_t = \Delta \log Y_t$, the log-level $\log Y_{t+h}$ deviates from baseline by $\sum_{i=0}^{h} IR_i^y$.
>
> Two consequences deserve attention. First, the zero long-run restriction of Section that section (monetary neutrality) is a restriction on $\sum_{i=0}^{\infty} IR_i^y = 0$, not on any individual growth-rate response. The condition $c_{12}=0$ — the $(1,2)$ element of the long-run matrix $C = (I-\Phi)^{-1}B$ in that section — translates exactly to this cumulative sum being zero. Second, Figures that section and that section illustrate the difference directly: Figure that section plots the growth-rate responses, while Figure that section plots the cumulative (level) responses (which converge to zero by construction under neutrality).

## Forecast Error Variance Decomposition

Forecast error variance decompositions (henceforth, $VD$) answer the following question: *What portion of the forecast error variance in each variable (at horizon $h$) is attributable to each structural shock?* While impulse responses tell us *how* variables respond to shocks, variance decompositions tell us how *important* each shock is in driving fluctuations in the variables of interest. This provides a different perspective: rather than tracing out the path of a single shock, we ask what fraction of the overall uncertainty about future values of our variables can be attributed to each structural shock.

For example, suppose we find that demand shocks explain 90% of the forecast error variance in GDP at the 4-quarter horizon, while monetary policy shocks explain only 10%. This tells us that, on average over the sample, demand shocks are the dominant source of GDP fluctuations, at least in the short run.

**<u>How to compute forecast error variance decompositions</u>.**  To understand variance decompositions, we first need to define what we mean by a forecast error. The $h$-step-ahead forecast error is the difference between the actual value of the variable at time $t+h$ and what we would have predicted for that value based on information available at time $t-1$:[^1]
$$ math
\begin{equation}
FE_{t+h} = x_{t+h} - \mathbb{E}_{t-1}[x_{t+h}]
\end{equation}
```

For a VAR(1), we can write the forecast error at different horizons as (note that under $\mathbb{E}_{t-1}$ conditioning, the $h$-step error accumulates $h+1$ new shocks):
$$
\begin{align*}
FE_{t} &= x_t - \mathbb{E}_{t-1}[x_t] = B\varepsilon_t \\
FE_{t+1} &= x_{t+1} - \mathbb{E}_{t-1}[x_{t+1}] = \Phi B\varepsilon_t + B\varepsilon_{t+1} \\
FE_{t+2} &= x_{t+2} - \mathbb{E}_{t-1}[x_{t+2}] = \Phi^2 B\varepsilon_t + \Phi B\varepsilon_{t+1} + B\varepsilon_{t+2}
\end{align*}
$$
In general, the $h$-step-ahead forecast error is:
$$
FE_{t+h} = \sum_{i=0}^{h} \Phi^{h-i} B \varepsilon_{t+i}

$$
Now consider the variance of the forecast error. Consider the case $h=0$. Under the $\mathbb{E}_{t-1}$ convention, the forecast error is $FE_t = B\varepsilon_t$, corresponding to the 1-step-ahead error and capturing the contemporaneous impact of shocks on the endogenous variables. Since the structural shocks are orthogonal and have unit variance, the variance of the forecast error for each variable is:
$$
\begin{align*}
\text{Var}(y_t - \mathbb{E}_{t-1}[y_t]) &= b_{11}^2 + b_{12}^2 \\
\text{Var}(r_t - \mathbb{E}_{t-1}[r_t]) &= b_{21}^2 + b_{22}^2
\end{align*}
$$
The forecast error variance decomposition for variable $y$ at horizon $h=0$ is then:
$$
\begin{align*}
VD_y^{\varepsilon^{Demand}} &= \frac{b_{11}^2}{b_{11}^2 + b_{12}^2} \\[6pt]
VD_y^{\varepsilon^{MonPol}} &= \frac{b_{12}^2}{b_{11}^2 + b_{12}^2}
\end{align*}
$$
Note that these decompositions sum to 1 for each variable — this is by construction, since the structural shocks are the only sources of variation in the forecast error.

For longer horizons $h > 0$, the same logic applies, but we need to account for the cumulative effect of shocks from the present through horizon $h$. Let $\Theta_i = \Phi^i B$ denote the impulse response matrix at horizon $i$, as in Section that section. Then the variance decomposition at horizon $h$ is:
$$
VD_{y,h}^{\varepsilon^{j}} = \frac{\sum_{i=0}^{h} (\theta_{1j}^i)^2}{\sum_{i=0}^{h} \sum_{m=1}^{k} (\theta_{1m}^i)^2}

$$
where $\theta_{1j}^i$ is the $(1,j)$ element of $\Theta_i$ (the response of variable $y$ to shock $j$ at horizon $i$). For a VAR($p$) with $p > 1$, replace $\Theta_i = \Phi^i B$ with the companion-form equivalent (see Box that section); the VAR Toolbox handles this substitution internally.

**<u>Interpretation</u>.**  Unlike impulse responses, which trace out the effect of a single shock over time, variance decompositions aggregate across all possible shock realizations to give us an average measure of importance.

**<u>In MATLAB</u>.**   operates in two distinct modes depending on the arguments supplied. The array has dimension $(H \times k \times k)$, where element is the FEVD share of shock $j$ for variable $i$ at horizon $h$ (1-indexed, matching the array convention). The first mode requires only the array and . With (the default), it produces a single figure with stacked area panels — one panel per variable — where each panel shows the FEVD shares of all shocks simultaneously; shares sum to one at every horizon. Setting ($j \geq 1$) restricts the output to variable $j$ only:

``` matlab
VARopt.figname = 'graphics/sign_VD';
VARvdplot(VAR_infer.VDmed, VARopt);
```

Figure that section shows the stacked area FEVD from the sign-restriction identification of Section that section. The code passes the element-wise median () to ; passing the Fry-Pagan draw () instead is equally valid — the function accepts either. The trade-off is described in Box that section: element-wise median VD shares need not sum to one at every horizon, while Fry-Pagan shares do by construction. While convenient as they show the relative importance of all shocks simultaneously, stacked area charts do not display uncertainty bands. The second mode of , described below, addresses this by plotting the FEVD share of a single shock with uncertainty bands, as described next.

> **Figure.** Forecast Error Variance Decomposition (Stacked Area)

The second mode is activated by supplying and as additional arguments. In band mode, indexes *shocks* (not variables): produces one figure per shock; ($j \geq 1$) restricts to shock $j$ only. Each figure has one panel per variable, showing the forecast error variance decomposition share of the selected shock with uncertainty bands. A color can optionally be set via ; if unset, the function defaults to . If is reused for subsequent calls with different settings, reset and to their defaults afterward:

``` matlab
VARopt.figname = 'graphics/sign_VD_bands';
VARopt.pick    = 2;
VARopt.color   = pantone('Tomato');
VARvdplot(VAR_infer.VDmed, VARopt, VAR_infer.VDinf, VAR_infer.VDsup);
VARopt.pick    = 0;
VARopt.color   = [];
```

Figure that section shows the band chart for the monetary policy shock. The wide credible bands reflect the identification uncertainty inherent in sign-restricted inference.

> **Figure.** Forecast Error Variance Decomposition (Bands)

> **Three properties of the variance decomposition.** Variance decompositions have several important properties that are worth highlighting:
>
> *<u>1. The adding-up property</u>.* For any variable and any horizon $h$, the shares across all $k$ structural shocks sum to one:
> $$
> \begin{equation*}
> \sum_{j=1}^{k} VD_{y,h}^{\varepsilon^j} = 1.
> \end{equation*}
> ```
> This follows immediately from that section: the denominator equals the total forecast error variance, and the numerators partition it exactly because the structural shocks are orthonormal and span the full space of reduced-form innovations — provided $B$ is square and invertible (full identification). Under partial identification, where not all shocks are identified, the shares need not sum to one.
>
> *<u>2. The long-run limit</u>.* For a covariance-stationary VAR, as $h \to \infty$, the FEVD converges to the unconditional variance shares — the fraction of the long-run variance of each variable attributable to each shock. These limiting shares depend on both the VAR dynamics $\Phi$ and the impact matrix $B$.
>
> *<u>3. FEVD inherits identification</u>.* The shares are computed from $\Theta_i = \Phi^i B$, so they depend on the identifying assumptions through $B$. Two identification schemes that agree on one column of $B$ — i.e. that identify the same shock in the same way — will in general disagree on the variance shares, because the decomposition of residual variance among the remaining shocks depends on the full $B$ matrix. This contrasts with impulse responses: to characterize the dynamic effects of a single shock $j$, one column of $B$ suffices. The FEVD share of shock $j$, however, requires the full $B$ because the denominator aggregates the forecast error variance across all $k$ shocks.

## Historical Decomposition

Historical decompositions (henceforth, $HD$) answer the following question: *At each point in time, what is the contribution of each structural shock (past and present) to the deviation of each variable from its equilibrium?* While impulse responses describe hypothetical scenarios (“what if a shock hits?”) and variance decompositions provide average measures of importance, historical decompositions attribute observed fluctuations, period by period, to specific structural shocks.

For example, suppose GDP fell sharply in 2008:Q4. A historical decomposition would attribute that shortfall to the cumulative contributions of all past structural shocks — demand and monetary policy shocks — each weighted by its propagation through the VAR dynamics up to that date. The decomposition thus explains where GDP stands at any point in time as the sum of contributions from the entire history of shocks, not merely those that arrived in the current period. This provides a narrative of what drove the economy during that episode.

**<u>How to compute historical decompositions</u>.**  To understand historical decompositions, recall the moving-average representation of the VAR (Section that section), now written in finite-horizon form with the constant contribution and initial condition shown explicitly:
$$ math
\begin{equation}
x_t = \sum_{s=0}^{t-1}\Phi^{s}c + \Phi^t x_0 + \sum_{s=0}^{t-1} \Phi^s B \varepsilon_{t-s}

\end{equation}
```
For a VAR($p$) with $p > 1$, replace $\Phi$ and $B$ in that section with the companion matrix $\mathcal{F}$ and the expanded impact matrix $\mathcal{B}$ (see Box that section), retaining only the first $k$ rows of the resulting decomposition. The first term, $\sum_{s=0}^{t-1}\Phi^{s}c$, captures the cumulative contribution of the constant; the second term, $\Phi^t x_0$, captures the effect of the initial condition; and the third term is the cumulative contribution of all structural shocks from the initial period through period $t$, running backwards from the most recent shock $\varepsilon_t$ (at lag 0) to the oldest shock $\varepsilon_1$ (at lag $t-1$).

For concreteness, consider $t=2$ in our simple bivariate VAR:
$$
x_2 = \underbrace{(I+\Phi)c}_{\text{Constant}} + \underbrace{\Phi^2 x_0}_{\text{Initial condition}} + \underbrace{B}_{=\Theta_0} \varepsilon_2 + \underbrace{\Phi B}_{=\Theta_1} \varepsilon_1
$$
Writing this out in matrix form:
$$
\begin{bmatrix}
y_2 \\
r_2
\end{bmatrix}
=
\begin{bmatrix}
\text{const}_y \\
\text{const}_r
\end{bmatrix}
+
\begin{bmatrix}
\text{init}_y \\
\text{init}_r
\end{bmatrix}
+
\begin{bmatrix}
\theta_{11}^1 & \theta_{12}^1 \\
\theta_{21}^1 & \theta_{22}^1
\end{bmatrix}
\begin{bmatrix}
\varepsilon_1^{Demand} \\
\varepsilon_1^{MonPol}
\end{bmatrix}
+
\begin{bmatrix}
\theta_{11}^0 & \theta_{12}^0 \\
\theta_{21}^0 & \theta_{22}^0
\end{bmatrix}
\begin{bmatrix}
\varepsilon_2^{Demand} \\
\varepsilon_2^{MonPol}
\end{bmatrix}
$$
For variable $y$, this becomes:
$$
y_2 = \text{const}_y + \text{init}_y + \theta_{11}^1 \varepsilon_1^{Demand} + \theta_{12}^1 \varepsilon_1^{MonPol} + \theta_{11}^0 \varepsilon_2^{Demand} + \theta_{12}^0 \varepsilon_2^{MonPol}
$$
The historical decomposition groups the terms by shock:
$$
\begin{align*}
HD_{y,2}^{\varepsilon^{Demand}} &= \theta_{11}^1 \varepsilon_1^{Demand} + \theta_{11}^0 \varepsilon_2^{Demand} \\
HD_{y,2}^{\varepsilon^{MonPol}} &= \theta_{12}^1 \varepsilon_1^{MonPol} + \theta_{12}^0 \varepsilon_2^{MonPol} \\
HD_{y,2}^{\text{init}}  &= \text{init}_y \\
HD_{y,2}^{\text{const}} &= \text{const}_y
\end{align*}
$$
These four components sum to $y_2$. The interpretation is straightforward:

- $HD_{y,2}^{\varepsilon^{Demand}}$ is the cumulative contribution of all past demand shocks (that haven’t fully dissipated yet) to $y$.

- $HD_{y,2}^{\varepsilon^{MonPol}}$ is the cumulative contribution of all past monetary policy shocks (that haven’t fully dissipated yet) to $y$.

- $HD_{y,2}^{\text{init}}$ captures the influence of the initial condition, which decays toward zero as $t$ grows, provided the VAR is stable.

- $HD_{y,2}^{\text{const}}$ captures the cumulative contribution of the constant. In a stable VAR (all eigenvalues of the companion matrix strictly inside the unit circle), this term converges to $\mu_y$, the $y$-th element of the equilibrium vector $\mu=(I-\Phi)^{-1}c$ defined in that section, as $t\to\infty$: it traces the path from zero toward the value $(I-\Phi)^{-1}c$. When the variables are covariance stationary, this limit equals the unconditional mean of $y$ and acts as the long-run level around which the shock contributions fluctuate; when the data are non-stationary (e.g. integrated variables estimated in log-levels), $(I-\Phi)^{-1}c$ is mathematically well-defined but economically uninterpretable as an unconditional mean (see Box that section below).

**<u>Interpretation</u>.** At each date, the decomposition assigns observed movements in each variable to specific structural shocks — for instance, whether a recession was driven by demand shocks or monetary policy shocks.

> <span id="box:hd_loglevels" label="box:hd_loglevels"></span> **Historical decomposition: log-levels versus log-differences.** The economic content of the initial condition and constant components depends on whether the VAR is estimated in log-differences or log-levels.
>
> *Log-differences VAR.* If the variables are growth rates, both components have a clean interpretation. The constant contribution converges to the average growth rate — a structurally meaningful, finite number that is stable across sample windows and carries a direct economic interpretation. The initial condition captures the deviation of the economy from its long-run average at the start of the sample. The pre-sample history that drove the economy to $x_0$ is unobserved and unidentified; this deviation is therefore treated as a residual initial state rather than attributed to any specific structural shock. It decays toward zero just as any shock contribution does, provided the VAR is stable.
>
> *Log-levels VAR.* If the variables include log-levels of trending series such as log GDP, neither component has an economic interpretation on its own. The constant converges to the sample mean of log GDP — a number that grows with the trend and changes with the sample window. The initial condition starts at the log-level of GDP in the first observation, which for a growing economy lies below the sample mean.
>
> Together, however, the two components capture the underlying stochastic trend. Since all VAR structural shocks are transitory (I(0) by the stability assumption), subtracting their I(0) contributions from the approximately I(1) log-level series leaves an approximately I(1) residual — a Beveridge-Nelson-type argument. That residual is the init-plus-constant baseline. Within the sample its mechanics are visible: the initial condition decays from $x_0$ toward zero while the constant rises from zero toward the sample mean, and their sum traces an upward path from $x_0$ to the sample mean that closely resembles the stochastic trend of log GDP. This is a finite-sample phenomenon — eigenvalues strictly below one imply eventual convergence of both terms — but over typical macroeconomic sample lengths the convergence is slow enough that the sum tracks the stochastic trend closely. When reading a historical decomposition from a levels VAR, the init and constant components should be lumped together and read as the stochastic trend, not interpreted individually.
>
> *A special case: $c = 0$.* The constant contribution is identically zero when the VAR is estimated without an intercept ($c = 0$). In a log-differences VAR this is a valid specification on demeaned growth rates, since average growth is zero by construction and the init contribution captures the initial deviation, which decays. In a log-levels VAR estimated on trending data, setting $c = 0$ is inadvisable: without a constant, the init contribution alone must absorb the entire I(1) stochastic trend, the model’s long-run forecast converges to zero (not the sample mean), and the estimated AR coefficients are pushed toward unit roots to compensate. The constant is necessary in any levels VAR applied to trending series.

**<u>In MATLAB</u>.**   operates in two distinct modes depending on the arguments supplied. Unlike , which takes a plain array, takes a struct; the shock contributions are stored in the field. In sign-restricted VARs, holds the element-wise median historical decomposition: the field is the element-wise median of shock contributions across all accepted draws, while the deterministic components (, , etc.) are copied from the Fry-Pagan draw (see Box that section). The function also accepts (the Fry-Pagan draw) as the argument. The trade-off mirrors that for variance decompositions: element-wise median contributions need not exactly reproduce the observed series when stacked, while Fry-Pagan contributions do by construction; any visible gap between the stacked contributions and the reference line in the stacked area figure reflects this non-summability. The first mode requires only the struct and . With (the default), the function produces a single stacked area figure with one panel per variable, decomposing the observed path into the cumulative contributions of each structural shock and the deterministic components (constant and initial condition):

``` matlab
VARopt.pick    = 0; % default: all shocks, stacked area
VARopt.figname = 'graphics/sign_HD';
VARhdplot(VAR_infer.HDmed, VARopt);
```

Figure that section shows the stacked area decomposition from the sign-restriction identification of Section that section.

> **Figure.** Historical Decomposition (Stacked Area)

The second mode is activated by supplying and as additional arguments. In band mode, indexes *shocks* (not variables): produces one figure per shock; ($j \geq 1$) restricts to shock $j$ only. Each figure has one panel per variable, showing the time-varying contribution of shock $j$ with uncertainty bands. A color can optionally be set via ; if unset, the function defaults to . If is reused for subsequent calls with different settings, reset and to their defaults afterward:

``` matlab
VARopt.figname = 'graphics/sign_HD_bands';
VARopt.pick    = 2;
VARopt.color   = pantone('Tomato');
VARhdplot(VAR_infer.HDmed, VARopt, VAR_infer.HDinf, VAR_infer.HDsup);
```

Figure that section shows the band chart for the monetary policy shock. The impulse responses, variance decompositions, and historical decompositions developed in Sections that section–that section rest on the assumption that the true data-generating process is well approximated by a finite-order VAR. When this assumption is in doubt — for instance, when the true lag order is large relative to the number of lags included in the estimated VAR, or when the VAR is otherwise misspecified — the VAR-based IRFs may be biased. Section [sec:lp](07-local-projections.md) introduces local projections as a specification-robust alternative: rather than iterating the fitted model forward, LP estimates the response at each horizon $h$ by a direct regression, delivering consistent estimates under weaker assumptions at the cost of efficiency when the VAR is correctly specified.

> **Figure.** Historical Decomposition (Bands)

[^1]: This handbook conditions on $\mathcal{F}_{t-1}$, so the $h$-step-ahead forecast error spans $h+1$ new shocks ($\varepsilon_t, \ldots, \varepsilon_{t+h}$). Some texts condition on $\mathcal{F}_t$, in which case the $h$-step error spans only $h$ new shocks.
