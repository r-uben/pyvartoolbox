---
title: "Local Projections"
label: "sec:lp"
source: VAR Handbook (Cesa-Bianchi)
type: reformatted-extract
licence: GPL-3.0
---

# Local Projections

> **Source.** This page is a reformatted extract of the *VAR Handbook* by
> Ambrogio Cesa-Bianchi, from the MATLAB VAR Toolbox (https://github.com/ambropo/VAR-Toolbox). The content is
> his; only the format has changed, so that it can be read in fragments by a
> machine. Redistributed under the GPL-3.0 the original carries. Code
> listings are **MATLAB** and do not apply to `pyvartoolbox` — see
> [conventions](../references/conventions.md) for where the APIs differ.

Local projections (LP), introduced by , estimate the impulse response at each horizon $h$ directly by regressing the $h$-step-ahead outcome on the shock of interest and lagged controls, without iterating a fully specified dynamic model forward. More broadly, local projections and VAR-based impulse responses are two implementations of the same object: under a common identification scheme and a common lag structure, both estimate the same population impulse response function, and the distinction is one of implementation. The VAR fits a fully specified dynamic model and iterates the fitted system forward to trace the response; LP estimates the response at each horizon by a separate, direct regression.

## A Brief Overview

A key premise of LP is that the researcher has access either to an identified shock series, used directly, or to an external instrument correlated with the shock of interest. The two cases give the two forms of the LP estimator: LP ordinary least squares (LP-OLS), which regresses directly on the shock series, denoted $s_t$; and LP two-stage least squares (LP-IV), which uses an external instrument, denoted $z_t$, to identify the effect of an endogenous treatment $d_t$. The two symbols follow the convention of the proxy-SVAR and exogenous-variable schemes of Sections that section and that section: $s_t$ for a series that enters the regression directly as the shock, $z_t$ for an instrument.

For a scalar outcome $x_{i,t}$ — the $i$-th element of the endogenous vector $x_t$, i.e. one of the variables of the system — and shock series $s_t$, the LP-OLS estimator runs:
$$

    x_{i,t+h} = \alpha_h + \beta_h s_t + \gamma_h' w_t + e_{t+h}, \qquad h = 0, 1, \ldots, H,
$$
where $i$ indexes the variables of the system $x_t$, $w_t$ is a vector of control variables — typically the lagged values of the same variables that would enter a VAR specification — and $e_{t+h}$ is the $h$-step-ahead forecast error. The projection is run separately for each outcome $i$, so the intercept, slope coefficients, and error carry an implicit $i$ subscript, suppressed throughout for readability. The sequence of estimated coefficients $\{\hat{\beta}_h\}_{h=0}^{H}$ directly traces the impulse response of $x_{i,t+h}$ to $s_t$. The outcome enters in whatever transformation the variable is supplied: when $x_{i,t}$ is a log-difference, $x_{i,t+h}$ is the growth rate $h$ periods ahead, so $\hat{\beta}_h$ traces the response of the growth rate, matching the VAR IRF convention of Section [sec:dynamic](06-structural-dynamic-analysis.md). Confidence bands use Newey-West HAC standard errors with bandwidth $L = h-1$ at each horizon $h$.

When the structural shock cannot be measured directly but an external instrument $z_t$ is available, LP-IV replaces the regressor with the endogenous policy variable $d_t$, instrumented by $z_t$:
$$

    x_{i,t+h} = \alpha_h + \beta_h d_t + \gamma_h' w_t + e_{t+h}, \qquad h = 0, 1, \ldots, H,
$$
where $d_t$ is instrumented by $z_t$ via horizon-by-horizon 2SLS. The coefficient $\hat{\beta}_h^{IV}$ estimates the causal effect of a change in $d_t$ (induced by $z_t$) on $x_{i,t+h}$, rather than the reduced-form effect of $z_t$ itself. The instrument must satisfy the same relevance and exogeneity conditions as in the proxy SVAR of Section that section: $z_t$ must be correlated with $d_t$ and uncorrelated with the other structural shocks.

LP has two main attractions relative to VAR-based IRFs. First, it is *robust to misspecification*: if the true data-generating process is not a finite-order VAR, the LP estimator still consistently estimates the impulse response at each horizon, provided the identifying variable ($s_t$ in LP-OLS, the instrument $z_t$ in LP-IV) is exogenous and $w_t$ is rich enough to absorb the predictable component of $x_{i,t+h}$. Second, the LP framework extends readily to nonlinear and state-dependent settings. The main cost is *efficiency*: by fitting a separate regression at each horizon, LP does not exploit the cross-horizon parameter restrictions implied by the VAR dynamics, so LP estimates are less efficient when the VAR is correctly specified.[^1]

A few practical caveats. LP estimates become noisier at long horizons because the forecast error $e_{t+h}$ grows in variance with $h$, so the trade-off between precision and horizon coverage should inform the choice of $H$. The bandwidth $L = h-1$ matches the MA order of the forecast error under a correctly specified VAR but may be conservative when the true MA order is shorter. Inference relies on asymptotic approximations; bootstrap procedures for LP are not currently implemented in the VAR Toolbox.

## Estimation and Identification

In the VAR Toolbox, local projections are implemented by the function . There are five required inputs: (i) a matrix of outcomes, ; (ii) the shock or treatment series, , common to all outcomes — namely, the shock $s_t$ in LP-OLS, the endogenous treatment $d_t$ in LP-IV; (iii) a matrix of controls, ; (iv) an integer lag length, ; and (v) the deterministic component, (0 = none, 1 = constant, 2 = constant and trend). The controls are passed in contemporaneous form and lagged internally: enters only lags $1,\ldots,$ of as regressors — never their contemporaneous values — so the user does not lag the controls beforehand.[^2] An optional sixth argument holds all estimation, identification, and plotting options (created with ; a sensible default is used if omitted); optional seventh and eighth arguments and accept exogenous regressors and their lag order. The estimator is univariate by construction — each impulse response comes from a separate horizon-by-horizon regression of one outcome on the shock — but when has $N$ columns the same specification (identical shock, controls, lags, and options) is looped over them, returning the responses as $H \times N$ matrices in the manner of . A single column reproduces the classic univariate call.

As with , is the input side of the toolbox: a struct, created once with , that carries estimation, identification, and plotting options across successive calls. Although optional, it is created in the example below so that variable mnemonics can be passed through . The choice between the two LP estimators (OLS and IV) is governed by a single field: when is empty (the default), runs LP-OLS, projecting directly on ; when is set to an external instrument, it runs LP-IV, treating as the endogenous variable instrumented by via horizon-by-horizon 2SLS. The two estimators are otherwise identical in call structure. The running example uses the same bivariate system as the preceding sections: GDP growth () and the level of the 1-year Treasury rate (), with the series from Section that section entering as the shock $s_t$ in LP-OLS and as the external instrument $z_t$ in LP-IV.

**<u>LP-OLS</u>.** Options are passed via (from ); the shock normalization is set to one standard deviation ():

``` matlab
LPopt          = LPoption;
LPopt.nsteps   = VARopt.nsteps; % match VAR horizon
LPopt.pctg     = 90;            % 90% confidence bands
LPopt.impact   = 0;             % 1-std-dev shock
LPopt.mnem     = Xmnem;         % mnemonics names 
LPopt.vnames   = Xvnames;       % labels for plots
```

Table that section documents the fields of that control estimation and plotting, grouped by role, together with their default values and meaning; the table follows , which can be inspected directly for the same information. Of the fields in Table that section, only and are specific to local projections; every other field shares the name and meaning of the corresponding field (Table that section), including the estimation fields , , and and the instrument field . In particular, the figure-export and panel-appearance fields are common to both structures, and reads them as reads them from , so the same plotting conventions apply.

<div id="tab:lpopt">

<table>
<caption>Fields of the <span style="background-color: script!80"><code>LPopt</code></span> options structure, with default values.</caption>
<thead>
<tr>
<th style="text-align: left;"><strong>Field (default)</strong></th>
<th style="text-align: left;"><strong>Description</strong></th>
</tr>
</thead>
<tbody>
<tr>
<td colspan="2" style="text-align: left;"><em>Table that section, continued</em></td>
</tr>
<tr>
<td style="text-align: left;"><strong>Field (default)</strong></td>
<td style="text-align: left;"><strong>Description</strong></td>
</tr>
<tr>
<td colspan="2" style="text-align: right;"><em>continued on next page</em></td>
</tr>
<tr>
<td style="text-align: left;"></td>
<td style="text-align: left;"></td>
</tr>
<tr>
<td style="text-align: left;"><span style="background-color: script!80"><code>nsteps = 40</code></span></td>
<td style="text-align: left;">Number of horizons <span class="math inline"><em>H</em></span> for the projection IRFs.</td>
</tr>
<tr>
<td style="text-align: left;"><span style="background-color: script!80"><code>pctg = 95</code></span></td>
<td style="text-align: left;">Outer confidence level for error bands (percent).</td>
</tr>
<tr>
<td style="text-align: left;"><span style="background-color: script!80"><code>impact = 0</code></span></td>
<td style="text-align: left;">Shock size: 0 = standardize the projection variable (the shock <span class="math inline"><em>s</em><sub><em>t</em></sub></span> in LP-OLS, the treatment <span class="math inline"><em>d</em><sub><em>t</em></sub></span> in LP-IV) to one standard deviation; 1 = leave it unchanged, so the response is per unit of that variable.</td>
</tr>
<tr>
<td style="text-align: left;"><span style="background-color: script!80"><code>longdiff = 0</code></span></td>
<td style="text-align: left;">1 = use the long-difference dependent variable <span class="math inline"><em>x</em><sub><em>i</em>, <em>t</em> + <em>h</em></sub> − <em>x</em><sub><em>i</em>, <em>t</em> − 1</sub></span> instead of the level <span class="math inline"><em>x</em><sub><em>i</em>, <em>t</em> + <em>h</em></sub></span>.</td>
</tr>
<tr>
<td style="text-align: left;"></td>
<td style="text-align: left;"></td>
</tr>
<tr>
<td style="text-align: left;"><span style="background-color: script!80"><code>IV = []</code></span></td>
<td style="text-align: left;">External instrument for the endogenous treatment <span class="math inline"><em>d</em><sub><em>t</em></sub></span> passed to <span style="background-color: script!80"><code>LPmodel</code></span>; empty = LP-OLS. Mirrors the <span style="background-color: script!80"><code>VARopt.IV</code></span> convention.</td>
</tr>
<tr>
<td style="text-align: left;"><span style="background-color: script!80"><code>nlag_iv = 0</code></span></td>
<td style="text-align: left;">Number of instrument lags added as extra instruments under LP-IV: 0 = just-identified (Wald estimator per horizon); <span class="math inline"><em>n</em> &gt; 0</span> adds lags <span class="math inline">1, …, <em>n</em></span> of <span style="background-color: script!80"><code>IV</code></span> after FWL. Requires <span style="background-color: script!80"><code>nlag_iv</code></span> <span class="math inline">≤</span> <span style="background-color: script!80"><code>nlag</code></span>.</td>
</tr>
<tr>
<td style="text-align: left;"></td>
<td style="text-align: left;"></td>
</tr>
<tr>
<td style="text-align: left;"><span style="background-color: script!80"><code>mnem = {}</code></span></td>
<td style="text-align: left;">Outcome mnemonics: valid MATLAB identifiers (no spaces or special characters) used to name the per-outcome sub-structs <span style="background-color: script!80"><code>LP.(.)</code></span>. Falls back to <span style="background-color: script!80"><code>vnames</code></span> if empty.</td>
</tr>
<tr>
<td style="text-align: left;"><span style="background-color: script!80"><code>vnames = {}</code></span></td>
<td style="text-align: left;">Outcome display labels for plots and tables (may contain spaces or LaTeX), one per column of the response matrix. Falls back to <span style="background-color: script!80"><code>mnem</code></span> if empty.</td>
</tr>
<tr>
<td style="text-align: left;"><span style="background-color: script!80"><code>snames = {}</code></span></td>
<td style="text-align: left;">Shock name (single entry for LP).</td>
</tr>
<tr>
<td style="text-align: left;"></td>
<td style="text-align: left;"></td>
</tr>
<tr>
<td style="text-align: left;"><span style="background-color: script!80"><code>figname = []</code></span></td>
<td style="text-align: left;">Prefix string for the exported figure filename.</td>
</tr>
<tr>
<td style="text-align: left;"><span style="background-color: script!80"><code>figsize = []</code></span></td>
<td style="text-align: left;">Figure window size <span style="background-color: script!80"><code>[width, height]</code></span> in cm.</td>
</tr>
<tr>
<td style="text-align: left;"><span style="background-color: script!80"><code>quality = 2</code></span></td>
<td style="text-align: left;">Export quality: 2 = high via <span style="background-color: script!80"><code>exportgraphics</code></span> (recommended, R2020a+), 1 = high via Ghostscript (legacy fallback), 0 = low via <span style="background-color: script!80"><code>print -dpdf</code></span>.</td>
</tr>
<tr>
<td style="text-align: left;"><span style="background-color: script!80"><code>suptitle = 0</code></span></td>
<td style="text-align: left;">1 = add a super-title above the figure panels.</td>
</tr>
<tr>
<td style="text-align: left;"></td>
<td style="text-align: left;"></td>
</tr>
<tr>
<td style="text-align: left;"><span style="background-color: script!80"><code>latex = 1</code></span></td>
<td style="text-align: left;">1 = use the LaTeX interpreter for figure text.</td>
</tr>
<tr>
<td style="text-align: left;"><span style="background-color: script!80"><code>font = ’Helvetica’</code></span></td>
<td style="text-align: left;">Font name for figure text; <span style="background-color: script!80"><code>’’</code></span> = MATLAB default.</td>
</tr>
<tr>
<td style="text-align: left;"><span style="background-color: script!80"><code>grid = 1</code></span></td>
<td style="text-align: left;">1 = show gridlines.</td>
</tr>
<tr>
<td style="text-align: left;"><span style="background-color: script!80"><code>marker = ’o’</code></span></td>
<td style="text-align: left;">Marker style for the IR line (<span style="background-color: script!80"><code>’o’</code></span>, <span style="background-color: script!80"><code>’none’</code></span>, etc.).</td>
</tr>
<tr>
<td style="text-align: left;"><span style="background-color: script!80"><code>subplot = []</code></span></td>
<td style="text-align: left;">Subplot grid <span style="background-color: script!80"><code>[rows cols]</code></span>; empty = auto from <span style="background-color: script!80"><code>sqrt(nvars)</code></span>.</td>
</tr>
<tr>
<td style="text-align: left;"><span style="background-color: script!80"><code>shorttitle = 0</code></span></td>
<td style="text-align: left;">1 = show the variable name only as the panel title; 0 = ‘variable to shock’.</td>
</tr>
<tr>
<td style="text-align: left;"><span style="background-color: script!80"><code>color = []</code></span></td>
<td style="text-align: left;">Line and band color (RGB triplet); empty = <span style="background-color: script!80"><code>pantone(’Blue’)</code></span>.</td>
</tr>
<tr>
<td style="text-align: left;"><span style="background-color: script!80"><code>linestyle = ’-’</code></span></td>
<td style="text-align: left;">IR line style (<span style="background-color: script!80"><code>’-’</code></span>, <span style="background-color: script!80"><code>’--’</code></span>, <span style="background-color: script!80"><code>’:’</code></span>, <span style="background-color: script!80"><code>’-.’</code></span>).</td>
</tr>
<tr>
<td style="text-align: left;"><span style="background-color: script!80"><code>hstart = 1</code></span></td>
<td style="text-align: left;">First horizon label on the x-axis (0 or 1).</td>
</tr>
<tr>
<td style="text-align: left;"><span style="background-color: script!80"><code>xlim = []</code></span></td>
<td style="text-align: left;">x-axis limits <span style="background-color: script!80"><code>[lo hi]</code></span>; empty = auto from <span style="background-color: script!80"><code>hstart:H</code></span>.</td>
</tr>
<tr>
<td style="text-align: left;"><span style="background-color: script!80"><code>ylim = []</code></span></td>
<td style="text-align: left;">y-axis limits <span style="background-color: script!80"><code>[lo hi]</code></span>; empty = auto.</td>
</tr>
<tr>
<td style="text-align: left;"><span style="background-color: script!80"><code>xtick = []</code></span></td>
<td style="text-align: left;">x-tick positions; empty = auto.</td>
</tr>
<tr>
<td style="text-align: left;"><span style="background-color: script!80"><code>xlabel = ’’</code></span></td>
<td style="text-align: left;">x-axis label applied to each panel; empty = none.</td>
</tr>
<tr>
<td style="text-align: left;"><span style="background-color: script!80"><code>ylabel = ’’</code></span></td>
<td style="text-align: left;">y-axis label applied to each panel; empty = none.</td>
</tr>
<tr>
<td style="text-align: left;"><span style="background-color: script!80"><code>dualaxis = 1</code></span></td>
<td style="text-align: left;">1 = dual-axis panel style (tick marks mirrored on the left and right y-axes, box off, closure tick at the top); 0 = off.</td>
</tr>
<tr>
<td style="text-align: left;"><span style="background-color: script!80"><code>visible = 1</code></span></td>
<td style="text-align: left;">1 = show figure windows; 0 = suppress display (save only).</td>
</tr>
</tbody>
</table>

</div>

Passing the full matrix <span style="background-color: script!80">`X`</span> — the two endogenous variables, GDP growth and the 1-year Treasury rate — rather than a single column returns the full set of LP results — impulse responses, confidence bands, and the per-horizon estimation output — for all variables at once. In terms of equation that section: the first argument supplies $x_{i,t+h}$ (one column per outcome), <span style="background-color: script!80">`mps`</span> is the shock $s_t$, and the third argument provides the lag control vector $w_t$ (lags of GDP growth and the 1-year Treasury rate). To keep these roles explicit at the call site, the example aliases the first and third arguments as <span style="background-color: script!80">`ENDO = X`</span> (the outcomes) and <span style="background-color: script!80">`CTRL = X`</span> (the controls) before invoking <span style="background-color: script!80">`LPmodel`</span>. Here both equal <span style="background-color: script!80">`X`</span>, so the assignment is redundant; it serves only to mark the two slots as conceptually distinct and to show where a richer control set would enter — through <span style="background-color: script!80">`CTRL`</span> alone:

``` matlab
ENDO = X;   % outcomes x_{i,t+h}
CTRL = X;   % controls w_t (lags constructed internally)
LP = LPmodel(ENDO, mps, CTRL, nlags, detc, LPopt);
```

At the impact horizon ($h=0$), equation that section reproduces a single reduced-form VAR equation augmented with the contemporaneous shock: GDP growth is regressed on a constant, the shock <span style="background-color: script!80">`mps`</span>, and lags of GDP growth and the 1-year Treasury rate. Given a common lag structure, this $h=0$ regression is exactly one equation of the exogenous-variable VAR of equation that section (Section that section), in which the same shock $s_t$ enters every equation as a contemporaneous regressor: the two are the same OLS projection of GDP growth on the shock and the lag controls. The schemes differ only beyond impact. The exogenous-variable VAR estimates this contemporaneous system once and iterates the estimated coefficients forward to all horizons, so relative to LP — which re-estimates a fresh regression at each horizon — it involves exactly the same regression at impact and (weakly) fewer regressions overall, a trade-off examined in Section that section. The sequence $\{\hat{\beta}_h\}$ then traces how that same contemporaneous innovation propagates as the horizon $h$ grows, one direct regression at a time.

**<u>LP-IV</u>.** To identify the causal effect of the 1-year Treasury rate on output, LP-IV uses the same call with the level of the 1-year rate <span style="background-color: script!80">`ENDO(:,2)`</span> passed as <span style="background-color: script!80">`TREAT`</span> (the endogenous treatment $d_t$) and <span style="background-color: script!80">`mps`</span> supplied through <span style="background-color: script!80">`LPopt.IV`</span> (the external instrument $z_t$). The <span style="background-color: script!80">`ENDO`</span> and <span style="background-color: script!80">`CTRL`</span> aliases defined above carry over unchanged. This mirrors the proxy-SVAR of Section that section, where <span style="background-color: script!80">`VARopt.IV`</span> likewise holds the external instrument:

``` matlab
LPopt_IV         = LPoption;
LPopt_IV.nsteps  = VARopt.nsteps;
LPopt_IV.pctg    = 90;
LPopt_IV.impact  = 0;
LPopt_IV.IV      = mps;   % external instrument
LPopt_IV.mnem    = Xmnem; % name per-variable sub-structs
LP_IV = LPmodel(ENDO, ENDO(:,2), CTRL, nlags, detc, LPopt_IV);
```

The function <span style="background-color: script!80">`LPmodel.m`</span> estimates each horizon’s IV coefficient via the Frisch-Waugh-Lovell (FWL) theorem. Rather than placing the lag controls $w_t$ alongside the treatment in the 2SLS step, it first partials $w_t$ out of the outcome $x_{i,t+h}$, the treatment $d_t$, and the instrument $z_t$ — regressing each on $w_t$ and retaining the residuals — and then runs the first and second stages on the residualized series. By FWL, the coefficient on $d_t$ is numerically identical to the one obtained by including $w_t$ directly, so the per-horizon estimate matches a standard 2SLS routine. The first-stage F-statistic, stored per horizon in <span style="background-color: script!80">`LP_IV.dlngdp.hN.Fstat_fs`</span>, should exceed the conventional rule-of-thumb value of 10 (see the first-stage discussion in Section that section) for the instrument to be considered relevant. With <span style="background-color: script!80">`nlag_iv`</span> $=0$ — a single instrument for a single treatment, the just-identified case — the estimator reduces to the Wald estimator at each horizon.

**<u>Structure of the <span style="background-color: script!80">`LPmodel`</span> output</u>.** The <span style="background-color: script!80">`LPmodel`</span> function returns a single structure <span style="background-color: script!80">`LP`</span> that collects all output from the local projection estimation. Its top-level fields are:

``` text
disp(LP)
    dlngdp: [1×1 struct]
    i1yr: [1×1 struct]
    eqnames: {2×1 cell}
    ENDO: [123×2 double]
    TREAT: [123×1 double]
    CTRL: [123×2 double]
    EXOG: []
    nlag: 1
    nlag_ex: 0
    const: 1
    ntotcoeff: 4
    IR: [20×2 double]
    INF: [20×2 double]
    SUP: [20×2 double]
```

where the main elements are:

- <span style="background-color: script!80">`dlngdp`</span>, <span style="background-color: script!80">`i1yr`</span>: one sub-struct per variable, each the full univariate LP output for that column (its own $H \times 1$ <span style="background-color: script!80">`IR`</span>/<span style="background-color: script!80">`INF`</span>/<span style="background-color: script!80">`SUP`</span>, joint-test fields, and per-horizon sub-structs <span style="background-color: script!80">`h1`</span>, …, <span style="background-color: script!80">`hH`</span>). The names come from <span style="background-color: script!80">`LPopt.mnem`</span> (set to <span style="background-color: script!80">`{’dlngdp’,’i1yr’}`</span> above); if <span style="background-color: script!80">`mnem`</span> is empty, or its entries are not valid unique field names (e.g. display labels with spaces), the sub-structs default to <span style="background-color: script!80">`eq1`</span>, …, <span style="background-color: script!80">`eqN`</span>. The resolved names are also stored in <span style="background-color: script!80">`LP.eqnames`</span> (an $N\times1$ cell), mirroring <span style="background-color: script!80">`VAR.eqnames`</span>.

- <span style="background-color: script!80">`ENDO`</span>, <span style="background-color: script!80">`TREAT`</span>, <span style="background-color: script!80">`CTRL`</span>, <span style="background-color: script!80">`EXOG`</span>: input data echoed back for traceability.

- <span style="background-color: script!80">`nlag`</span>, <span style="background-color: script!80">`const`</span>: lag order and deterministic specification.

- <span style="background-color: script!80">`IR`</span>, <span style="background-color: script!80">`INF`</span>, <span style="background-color: script!80">`SUP`</span>: impulse responses and Newey-West confidence bands ($H \times N$); column $i$ is the response of variable $i$.

Each per-variable sub-struct is itself a complete univariate LP output: it holds that variable’s own impulse responses (<span style="background-color: script!80">`IR`</span>/<span style="background-color: script!80">`INF`</span>/<span style="background-color: script!80">`SUP`</span>), the joint-test fields (<span style="background-color: script!80">`jtest_chi2`</span>, <span style="background-color: script!80">`jtest_df`</span>, <span style="background-color: script!80">`jtest_pval`</span>), and one sub-struct per horizon (<span style="background-color: script!80">`h1`</span>, …, <span style="background-color: script!80">`h20`</span>) storing the horizon-$h$ estimation results (OLS here; 2SLS under LP-IV). For example, the full output for the GDP growth equation (the first column of <span style="background-color: script!80">`X`</span>) is inspected with <span style="background-color: script!80">`disp(LP.dlngdp)`</span>:

``` text
>> disp(LP.dlngdp)
    ENDO: [123×1 double]
    TREAT: [123×1 double]
    CTRL: [123×2 double]
    EXOG: []
    nlag: 1
    nlag_ex: 0
    const: 1
    ntotcoeff: 4
    jtest_chi2: 62.8949
    jtest_df: 20
    jtest_pval: 2.5152e-06
    h1: [1×1 struct]
    h2: [1×1 struct]
    h3: [1×1 struct]
    .
    .
    .   
    h20: [1×1 struct]
    IR: [20×1 double]
    INF: [20×1 double]
    SUP: [20×1 double]
```

**Normalization to 25 bps.** To compare the two methods on a common scale — the response to a 25 basis point increase in the 1-year Treasury rate — both sets of impulse responses are rescaled after estimation. For LP-OLS, the scale factor is the ratio of the target change (0.25 percentage points) to the impact response of the 1-year Treasury to a 1-standard-deviation <span style="background-color: script!80">`mps`</span> shock, <span style="background-color: script!80">`LP_IR(1,2)`</span>. For LP-IV, the impulse responses are already expressed per one-standard-deviation move in the treatment (the <span style="background-color: script!80">`impact = 0`</span> normalization divides by the standard deviation of the 1-year rate); rescaling to a 25 basis point move therefore divides <span style="background-color: script!80">`0.25`</span> by <span style="background-color: script!80">`std(X(:,2))`</span>:

``` matlab
ir_col      = 2;                        % column index of i1yr in X
scale_ols   = 0.25 / LP_IR(1,ir_col);   % LP-OLS normalization
scale_iv    = 0.25 / std(X(:,ir_col));  % LP-IV normalization
LP_IR_n    = LP_IR  * scale_ols;
LP_INF_n   = LP_INF * scale_ols;
LP_SUP_n   = LP_SUP * scale_ols;
LP_IV_IR_n  = LP_IV_IR  * scale_iv;
LP_IV_INF_n = LP_IV_INF * scale_iv;
LP_IV_SUP_n = LP_IV_SUP * scale_iv;
```

Figure that section plots the normalized LP-OLS and LP-IV impulse responses with 90% confidence bands. LP-OLS estimates the reduced-form effect of a monetary policy surprise (<span style="background-color: script!80">`mps`</span>) that moves the 1-year Treasury by 25 bps on impact; LP-IV estimates the causal effect of a 25 bps change in the 1-year Treasury induced by <span style="background-color: script!80">`mps`</span>. The two responses agree closely at short horizons by construction (both normalizations pin down the impact response of the policy rate) but may diverge at longer horizons if the VAR dynamics impose misspecification on the LP-OLS propagation.

> **Figure.** Impulse Responses: LP-OLS vs. LP-IV

> **Newey-West standard errors in LP.**  At horizon $h$, the LP regression error $e_{t+h}$ is the $h$-step-ahead forecast error. When the VAR lag order $p$ is correctly specified and the full $p$-lag vector $w_t$ is included as controls, the forecast error admits the moving-average representation
> ``` math
> \begin{equation*}
>     e_{t+h} = \varepsilon_{t+h} + \psi_1 \varepsilon_{t+h-1} + \cdots + \psi_{h-1}\varepsilon_{t+1},
> \end{equation*}
> ```
> where $\psi_k$ are the MA coefficients of the Wold representation (see Section that section). This MA($h-1$) structure implies that $e_{t+h}$ is serially correlated with $e_{t+1}, \ldots, e_{t+h-1}$ for $h > 1$, even when the structural shocks $\varepsilon_t$ are white noise. The correct estimator is therefore a heteroskedasticity- and autocorrelation-consistent (HAC) estimator. uses Newey-West with bandwidth $L = h-1$, matching the exact MA order, and the reported confidence bands (, ) are based on .

Section that section below compares the local projection and exogenous-variable SVAR impulse responses on the same bivariate example.

## Local Projections versus VAR

Section that section established the key trade-off: LP is robust to VAR misspecification but less efficient when the VAR is correctly specified. This subsection illustrates that trade-off directly, comparing the LP-OLS impulse responses of Section that section with those from the exogenous-variable SVAR of Section that section. Both methods use MPS as the identification variable and produce responses to a 25 basis point increase in the 1-year Treasury rate (using the same LP-OLS normalization as in Figure that section). Full details of the exogenous-variable identification scheme are in Section that section.

The two approaches are mechanically distinct but asymptotically equivalent. In the exogenous-variable SVAR, the exogenous shock $s_t$ enters the system directly as a contemporaneous regressor in each VAR equation, and the structural impact is identified jointly with the VAR dynamics in a single estimation step. The LP estimator, by contrast, projects the $h$-step-ahead outcome directly onto $s_t$ at each horizon, without fitting a fully specified dynamic model. Under exogeneity of $s_t$ and a common lag structure, both approaches recover the same first column of $B$ at the impact horizon: at $h=0$, both reduce to the same OLS projection of each endogenous variable on $s_t$ conditional on the same lag controls, so the two estimators deliver asymptotically equivalent impact responses. Any systematic divergence between the two at horizons $h>0$ is therefore informative about potential misspecification in the VAR dynamics. formalize this result: LP, proxy SVAR, and exogenous-variable SVAR all identify the same population impulse responses under the same identification assumptions, provided the lag order grows with the sample size (formally, $p \to \infty$ as $T \to \infty$).

The two approaches thus present a practical trade-off. LP is agnostic about the dynamic structure at every horizon, making it robust to lag truncation and VAR misspecification. The exogenous-variable SVAR imposes cross-horizon parameter restrictions implied by the autoregressive dynamics, which delivers efficiency gains when the VAR is correctly specified but propagates any misspecification into the estimated responses at all horizons.

> **Figure.** Impulse Responses: LP vs. Exogenous-Variable SVAR

Figure that section compares the impulse responses from the two approaches. For GDP growth, LP and the exogenous-variable SVAR track closely across horizons. For the interest rate, they diverge at longer horizons: the VAR-implied path is smoother, reflecting the cross-horizon restrictions imposed by the autoregressive dynamics, whereas the LP path is less constrained. This divergence may indicate misspecification in the VAR dynamics. LP is robust to such misspecification since it imposes no cross-horizon restrictions. When the two methods yield systematically different responses at long horizons, the divergence warrants investigation: it may signal VAR misspecification, but it may also reflect the additional estimation noise that LP incurs by fitting each horizon independently.

[^1]: See for a formal treatment of the efficiency-robustness trade-off and a proof that LP and VAR-based estimators identify the same population impulse responses when the VAR is correctly specified and lag controls are sufficiently rich (formally, $p\to\infty$ as $T\to\infty$).

[^2]: Unlike , lags of the outcome are not added automatically. Passing the full matrix as reproduces the VAR control set.
