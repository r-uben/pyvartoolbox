---
title: "VAR Estimation in the VAR Toolbox"
label: "sec:rfvar_toolbox"
source: VAR Handbook (Cesa-Bianchi)
type: reformatted-extract
licence: GPL-3.0
---

# VAR Estimation in the VAR Toolbox

> **Source.** This page is a reformatted extract of the *VAR Handbook* by
> Ambrogio Cesa-Bianchi, from the MATLAB VAR Toolbox (https://github.com/ambropo/VAR-Toolbox). The content is
> his; only the format has changed, so that it can be read in fragments by a
> machine. Redistributed under the GPL-3.0 the original carries. Code
> listings are **MATLAB** and do not apply to `pyvartoolbox` — see
> [conventions](../references/conventions.md) for where the APIs differ.

With the theoretical framework established in Section [sec:overview](02-a-brief-overview-of-var-models.md), this section turns to practical implementation using the VAR Toolbox. We begin by describing how to load and prepare the data, then estimate the reduced-form VAR of Section that section by OLS, and verify the stability condition of Section that section, before connecting the estimation outputs to the identification problem of Section that section and setting the stage for the identification schemes in Section [sec:ident](04-identification-in-the-var-toolbox.md).

## Prelims: Loading and Preparing the Data

The data for the examples in this handbook are stored in the spreadsheet , located in . The file contains two US time series at quarterly frequency, real GDP and the yield on the 1-year Treasury Bill, over the sample period 1989:Q1 to 2019:Q4 ($T=124$ observations). The Data Appendix reports the source of each series used.

The code below shows how to load and manage the data following VAR Toolbox conventions. Specifically, the code reads from the spreadsheet and stores each time series into the structure as a separate variable. The convention of the VAR Toolbox is that time series are stored in column-vectors, so that the number of rows corresponds to the number of observations for a given time series.

The VAR Toolbox can handle data at any frequency. Dedicated helper functions for date management and plotting are provided for quarterly and monthly data, as these are the most common frequencies in macroeconomic analysis; annual or higher-frequency data can be used directly without those helpers. Dates can be supplied in two formats:

- <u>*String format*</u>  Quarters (months) are denoted with $q$ ($m$). For example, () corresponds to the first quarter (month) of the year 2000.

- <u>*Numeric format*</u>  Following the convention in , the first quarter (month) of the year corresponds to the integer of that year. For example, 2000q1 (or 2000m1 for monthly data) corresponds to . Subsequent quarters are encoded as: Q2 $\to$ year$+0.25$, Q3 $\to$ year$+0.50$, Q4 $\to$ year$+0.75$. For monthly data, month $j$ corresponds to year$+(j-1)/12$.

In the code below, dates are read in string format from the spreadsheet and stored in the cell array . The function converts dates from string to numeric format, while performs the reverse conversion (returning a cell array of date strings in the original $q$/$m$ format, e.g. ).

``` matlab
raw         = readcell('data/Primer_Data.xlsx', 'Sheet', 'Sheet1');
dates       = raw(3:end, 1);   % vector of dates in string format
datesnum    = Date2Num(dates); % vector of dates in numeric format
vnames = raw(1, 2:end);   % full variable names (display labels)
mnem   = raw(2, 2:end);   % variable mnemonics (valid identifiers)
nvar   = length(mnem);    % number of variables in spreadsheet
data   = cellfun(@double, raw(3:end, 2:end)); % numeric data matrix

% Store each variable in the DATA struct, keyed by mnemonic
for ii=1:length(mnem)
    DATA.(mnem{ii}) = data(:,ii);
end

% Record the raw number of observations
nobs_raw = size(data,1);

% Helper for bold epsilon shock labels with latex interpreter
bfeps = @(s) ['${\bf \epsilon}_{t}^{\mathrm{' s '}}$'];
```

VAR analysis typically requires transforming the raw data before estimation, and the VAR Toolbox provides built-in functions to perform the most commonly used data treatments. The code below shows how to use the in-built function to compute the log-difference of real GDP and the first difference of the 1-year Treasury Bill yield, adding the two new variables to the structure — this is just an example: recall that, throughout the handbook, the VAR is estimated on the log-difference of GDP and the *level* of the 1-year rate.

The function takes as inputs the data structure ; a cell array of the field names to transform; a vector of transformation codes, one per variable, where 1 = log (), 2 = first difference (), 3 = log-difference (), and 4 = fractional change (); and an optional vector of rescaling factors. Each transformed series is written back into under a prefixed field name, so that the log-difference of is stored as and the first difference of as . The function stops with an error if a target field name already exists, which prevents silent overwriting; difference-based transforms (codes 2–4) use one lag by default, and an optional fifth argument sets the lag order.

``` matlab
tnames = {'gdp','i1yr'};  % variable mnemonics
ttreat = {3, 2};          % transformation: 3=log-diff, 2=diff
tscale = [100 1];         % rescaling factor

% Apply transformations; results stored in DATA as dlngdp and di1yr
DATA = datatreat(DATA,tnames,ttreat,tscale);
```

> **VAR estimation: log-levels versus log-differences.** The standard theory for a stable VAR assumes that the variables are covariance stationary. In practice this means that their unconditional mean, variance, and autocovariances do not depend on time, so that the series fluctuate around a fixed long-run level with a stable degree of persistence rather than trending or drifting. Under this assumption, the VAR has a well-defined unconditional mean, a finite unconditional covariance matrix, and a convergent moving-average representation. This makes the initial condition, constant term, impulse responses, and variance and historical decompositions easier to interpret. Some of these concepts — in particular stationarity, the moving-average representation (Section that section), and stability (Section that section) — were introduced in Section [sec:overview](02-a-brief-overview-of-var-models.md); impulse responses, variance and historical decompositions are developed in Section [sec:dynamic](06-structural-dynamic-analysis.md). This box may become clearer on a return visit after reading those sections.
>
> Many macroeconomic aggregates, however, are not stationary in log-levels. Real GDP, consumption, investment, and similar variables are often well described as containing stochastic trends. This creates a practical choice: transform the data into stationary growth rates, or estimate the VAR in log-levels despite the presence of unit roots.
>
> *Estimation in log-differences.* Taking log-differences removes a unit root in log-levels and turns the variable into a growth rate. If the transformed variables are stationary and the VAR is stable (Section that section), the first term of the vector $(I-\mathcal{F})^{-1}c$ captures the average growth rate of GDP in the VAR sample. Impulse responses describe the temporary effect of shocks on growth rates: these effects dissipate over time, and the growth rate eventually returns to its long-run average. The implied effect on the log-level can be obtained by cumulating the growth-rate responses. Because each growth-rate shock is transitory, cumulating the growth-rate responses still yields a non-zero permanent level shift: a monetary policy shock, for instance, may cause growth to slow for several quarters and then recover, but the accumulated shortfall may leave the log-level of GDP permanently lower. That is, this cumulated response converges to a well-defined long-run level effect, which may be non-zero.
>
> *Estimation in log-levels.* A VAR can also be estimated directly in log-levels, even when some variables contain unit roots. The presence of unit roots does not prevent consistent OLS estimation of the VAR coefficients , though standard $t$- and $F$-tests may not have their usual asymptotic distributions. One reason why many empirical VARs are estimated in levels is that the levels specification preserves low-frequency comovement among the variables and avoids discarding long-run information by differencing.
>
> A VAR in log-levels need not be explosive. With enough lags, the companion matrix can have all eigenvalues strictly inside the unit circle even when individual variables contain unit roots, and the stability condition of Section that section can be verified after estimation. If the VAR is stable, impulse responses describe the effect of shocks on the log-level of each variable: these are persistent but eventually dissipate, so shocks are transitory *in levels*. This is different from the log-differences case, where shocks are transitory in growth rates but leave a permanent imprint on the log-level.
>
> Moreover, the interpretation of the constant and initial condition differs fundamentally from the covariance-stationary case. The constant $c$ implies an unconditional mean equal to $(I - \mathcal{F})^{-1}c$ — which is the sample average of log GDP. Unlike the average growth rate in the log-differences VAR, this has no stand-alone economic interpretation (it grows over time, and is sample dependent). Similarly, the initial condition $x_0$ is the log-level of GDP in the first period of the sample, which for a growing economy will lie below the sample mean.
>
> Together, however, the initial condition and constant in the historical decomposition capture something meaningful. Since the VAR structural shocks are all transitory (I(0) by the stability assumption), everything in log GDP that is not explained by the shocks must be the low-frequency trending component. By a Beveridge-Nelson-type argument, subtracting I(0) shock contributions from an I(1) series leaves an I(1) residual: the sum of the initial-condition and constant contributions traces the underlying stochastic trend in log GDP. Within the sample this is visible in the mechanics: the initial condition contribution decays from $x_0$ toward zero, while the constant contribution rises from zero toward the sample mean; their sum traces an upward path from $x_0$ to the sample mean that resembles the I(1) trend. This is a finite-sample phenomenon — in the model’s own terms, eigenvalues strictly below one imply eventual convergence — but over typical sample lengths the convergence is slow enough that the baseline closely tracks the stochastic trend. See the box on historical decomposition in Section [sec:dynamic](06-structural-dynamic-analysis.md) for further discussion.
>
> In this handbook we estimate the benchmark VAR in log-differences. This choice makes the stationarity assumption transparent and gives the intercept a simple interpretation as average growth. The cost is that the benchmark specification focuses on short-run fluctuations in growth rates and does not explicitly model possible cointegrating relationships among log-levels.

As mentioned above, the example used throughout the handbook is based on a deliberately simple bivariate VAR with $k=2$ endogenous variables: the log-difference of US real GDP (as computed above and denoted by $y_{t}$) and the 1-year yield on the US Treasury bill (denoted by $r_{t}$).[^1] The VAR Toolbox follows the convention that the $k$ endogenous variables are stored as the columns of a $T \times k$ matrix , where $T$ is the number of time periods and $k$ the number of variables.[^2] In our bivariate example $k=2$, so that:
$$

    \text{\mc{X}}=\left[ 
    \begin{array}{cc}
        y_{1} & r_{1} \\ 
        y_{2} & r_{2} \\ 
        ... & ... \\ 
        y_{T} & r_{T}%
    \end{array}%
    \right]
$$
The code below shows a general way to construct such an matrix in MATLAB.

``` matlab
Xmnem = {'dlngdp','i1yr'};
Xvnames = {'Real GDP Growth','1-year Int. Rate'};
% Number of endogenous variables
Xnvar = length(Xmnem);
% Assemble matrix X by pulling columns from the DATA struct
X = nan(nobs_raw,Xnvar);
for ii=1:Xnvar
    X(:,ii) = DATA.(Xmnem{ii});
end
% Balance the sample (dlngdp is missing because of log-differencing)
[X, fo, lo] = CommonSample(X);
% Keep the date vectors aligned with the trimmed data
nobs     = size(X,1);
dates    = dates(fo+1 : fo+nobs);
datesnum = datesnum(fo+1 : fo+nobs);
```

The key elements of this code are the following:

- and . The cell array holds the variable *mnemonics* — short valid-identifier strings (here and ) that select the columns of the struct and, at the estimation stage, name the per-equation sub-structures returned by . The cell array holds the corresponding *display labels* (here and ) used in figure titles and legends.

- . A VAR must be estimated on a balanced set of endogenous variables, but the two series enter with different starting points: log-differencing real GDP costs one observation, so the first entry of is missing (), whereas the 1-year rate is observed from the first period. trims to the largest contiguous block in which every column is observed — here it removes the first row — and returns the number of leading and trailing rows dropped in and (equal to $1$ and $0$, respectively).

- Sample size and dates. After trimming, the working number of observations is $\,=123$, down from the raw count $\,=124$, and the date vectors and are sliced by the same and offsets so that they remain aligned with the data. The resulting is therefore $123 \times 2$, spanning the sample 1989:Q2–2019:Q4.[^3]

The same code, with updated and , can be used to assemble a custom for any set of variables available in .

The VAR Toolbox includes functions to plot time series quickly and export them as high-quality PDFs, so that they can be used directly in research papers. The code shows how to plot the two (common-sample) time series in .

``` matlab
figure;
FigSize(24,6)
for ii=1:Xnvar
    subplot(1,2,ii)
    H(ii) = plot(X(:,ii),'LineWidth',3,'Color',pantone('Blue'));
    title(['\textbf{' Xvnames{ii} '}'],'FontWeight','bold','FontSize',13);
    DatesPlot(datesnum(1),nobs,6,'q') % Set the x-axis labels
    set(gca,'FontSize',11,'Layer','bottom'); grid on;
    set(findobj(gca,'Type','line'),'Clipping','off');
    SetAxesDual(gca);
end
% Save figure
SaveFigure('graphics/data',2)
```

Some useful functions used in the code above are:

- : allows the user to choose the size and the proportions of the window for plotting the figure. This is particularly useful when creating figures with many panels.

- : adds the dates (in numeric format) to the horizontal axis of a chart (at monthly, quarterly, or annual frequency) using a specified number of ticks (6 in the above example).

- : saves the chart to a specified location.

Figure that section shows the behavior of the log-difference of US real GDP and the interest rate on the US 1-year Treasury bill over the common-sample period 1989:Q2 to 2019:Q4.

> **Figure.** Endogenous Variables in the Simple VAR

## Estimation

With the data in hand, we estimate the bivariate VAR(1) introduced in Section that section.[^4] For reference, the model (equations that section–that section) is:
$$
    \begin{array}{c}
        y_{t}=c_y+ \phi _{11}y_{t-1}+\phi _{12}r_{t-1}+u_{yt}, \\
        r_{t}=c_r+ \phi _{21}y_{t-1}+\phi _{22}r_{t-1}+u_{rt},%
    \end{array}
$$
which in matrix form can be written more compactly as
$$
    x_{t}= c + \Phi x_{t-1}+u_{t},
$$
where $x_{t}$ is a $2 \times 1$ column vector collecting the two endogenous variables at time $t$;[^5] $c$ is a $2 \times 1$ vector of constants; $\Phi$ is a $2 \times 2$ matrix of autoregressive coefficients; and $u_{t}$ is a $2 \times 1$ vector of serially uncorrelated innovations, generally referred to as *reduced-form residuals*.[^6] Typically, the reduced-form residuals are correlated among themselves. Their covariance matrix can be written as:
$$
    \mathbb{V}(u_{t})\equiv \Sigma_{u}=\left[
    \begin{array}{cc}
        \sigma _{y}^{2} & \sigma _{yr} \\
        \sigma _{yr} & \sigma _{r}^{2}%
    \end{array}%
    \right].
$$
The covariance matrix $\Sigma_{u}$ is a $2 \times 2$ symmetric matrix. Its diagonal elements are the variances of the estimated reduced-form innovations, $\sigma _{y}^{2}$ and $\sigma _{r}^{2}$; and its off-diagonal elements — equal to each other by symmetry — give the covariance between the reduced-form residuals, $\sigma _{yr}$.

A VAR model is estimated with a single call to the function . There are three required inputs to this function: (i) a matrix of endogenous variables, ; (ii) an integer specifying the number of lags, ; and (iii) an integer specifying the deterministic component, (0 = no deterministic component, 1 = constant, 2 = constant and trend). An optional fourth argument holds all estimation and identification options (created with ; a sensible default is used if omitted). Optional fifth and sixth arguments and accept a matrix of exogenous regressors and their lag order, respectively.

Although is optional — the reduced-form OLS fit can be obtained directly with — in the example below it is created so that the variable mnemonics can be passed to through . These mnemonics are used to label the estimation output, as detailed below. The code estimates the simple VAR model in that section:

``` matlab
VARopt = VARoption;
VARopt.mnem = Xmnem;
% Deterministic component: 1=constant, 2=constant+trend
detc = 1;
% Lag order
nlags = 1;
% Estimate VAR by OLS (reduced form only)
VAR_redform = VARmodel(X,nlags,detc,VARopt);
```

> **Choosing the lag order.**  The lag order $p$ is a critical specification choice. Setting $p$ too low leads to omitted-variable bias and serially correlated residuals; setting $p$ too high wastes degrees of freedom and inflates parameter uncertainty. Several *information criteria* are available to select the VAR lag order. The two most common are:
> $$
> \begin{align*}
> \text{AIC} &= \ln|\hat{\Sigma}_u| + \frac{2}{T}pk^2, \\
> \text{BIC} &= \ln|\hat{\Sigma}_u| + \frac{\ln T}{T}pk^2,
> \end{align*}
> ```
> where $k$ is the number of endogenous variables, $T$ is the sample size, and $|\hat{\Sigma}_u|$ is the determinant of the estimated residual covariance matrix. Here $pk^2$ counts the autoregressive coefficients only. In practice, uses the total number of regressors per equation (including deterministic terms) in the penalty, replacing $pk^2$ with $k(pk+d)$ where $d$ is the number of deterministic regressors ($d=1$ for a constant, $d=2$ for a constant and trend). BIC (also known as the Schwarz Information Criterion, SIC; both acronyms refer to the same criterion) applies a heavier penalty than AIC and tends to select more parsimonious models. A *sequential likelihood-ratio (LR) test* provides an alternative: start from a maximum lag $p_{\max}$ and test down, removing one lag at a time until the LR statistic first becomes insignificant.
>
> In practice, quarterly VARs often use 4–8 lags; monthly VARs typically use 12–24. With $k$ variables and $p$ lags, each equation has $kp + d$ regressors. As a rough guideline, the total number of estimated parameters per equation should remain well below $T/10$ to preserve adequate degrees of freedom. Regardless of the criterion used, it is good practice to verify that the chosen lag order yields serially uncorrelated residuals — a necessary condition for valid inference.
>
> The VAR Toolbox provides the function to automate lag selection. It evaluates AIC and BIC over all lag lengths from 1 to a user-specified maximum and returns the optimal lag under each criterion:
>
> ``` matlab
> [AIC, BIC, logL] = VARlag(X, maxlag, detc);
> ```
>
> where is the matrix of endogenous variables, is the maximum lag length to consider, and is the deterministic specification (same as in ). The function returns the optimal lag length under AIC () and BIC (), and the log-likelihood value at each candidate lag order from 1 to (, a vector of length ). In case of disagreement between AIC and BIC, it is advisable to check robustness of the results under both.

The results of the VAR estimation are stored in the structure . Together with the options structure , it forms one of the two central objects of the VAR Toolbox. The two play complementary roles: is the input side — a MATLAB struct, created once with , that can be reused and modified across successive calls to and related functions, so that options set in one step carry over to the next without re-specification — while is the output side, collecting both the inputs and the estimation results.

Specifically, stores the inputs to — the matrix of endogenous variables (), the chosen number of lags (), the number of endogenous variables (), and so on — alongside the estimation output. Its fields can be inspected with , or, in the MATLAB desktop environment, by double-clicking on the structure in the Workspace browser:

$$ text
>> disp(VAR_redform)
    ENDO: [123×2 double]
    nlag: 1
    const: 1
    EXOG: []
    nvar: 2
    nvar_ex: 0
    nlag_ex: 0
    ncoeff_es: 0
    nobs: 122
    ncoeff: 2
    ntotcoeff: 3
    eqnames: {2×1 cell}
    dlngdp: [1×1 struct]
    i1yr: [1×1 struct]
    Ft: [3×2 double]
    F: [2×3 double]
    sigma: [2×2 double]
    resid: [122×2 double]
    X: [122×3 double]
    Y: [122×2 double]
    Fcomp: [2×2 double]
    maxEig: 0.9559
    B: []
    PSI: []
    Fp: []
    IR: []
    VD: []
    HD: []
    ident: ''
```

A few of the elements of the structure  are worth describing in detail.

- <u>*Estimated coefficients*</u>.  The matrix collects all estimated coefficients following the notation in that section, so that $=[c \ \hat{\Phi}_1 \ \cdots \ \hat{\Phi}_p]$. For the VAR(1) considered here ($p=1$, $k=2$, plus a constant), is a $2\times 3$ matrix, as shown below:

  ``` text
  >> disp(VAR_redform.F)
       0.3630    0.3788    0.0041
      -0.0729    0.2607    0.9541
  ```

- <u>*VAR residuals*</u>  The matrix collects the VAR reduced-form residuals, as defined by that section. The $t$-th row of is the row vector $u_t'$, for $t=p+1,\ldots,T$. For a VAR with $p$ lags, is a $(T-p)\times k$ matrix (as $p$ observations are lost when computing lags of $x_t$), here $122\times 2$.

- <u>*Reduced-form covariance matrix*</u>  The matrix collects the covariance matrix of the VAR reduced-form residuals defined by that section. The convention is such that =$\Sigma_{u}$. The estimate is degrees-of-freedom corrected: $\hat{\Sigma}_u = \hat{u}'\hat{u}\,/\,(T_{\text{eff}} - (pk+d))$, where $T_{\text{eff}}=T-p$ is the number of observations left after lag removal and $pk+d$ is the number of regressors per equation — $k$ coefficients on each of the $p$ lags, plus $d$ deterministic terms ($d=1$ for a constant, $d=2$ for a constant and trend), and any exogenous regressors when present. This count is what the toolbox stores in , equal to $3$ in the printout above ($p=1$, $k=2$, $d=1$). For a VAR with $2$ endogenous variables, the covariance matrix is a symmetric $2\times 2$ matrix:

  ``` text
  >> disp(VAR_redform.sigma)
      0.2891    0.0782
      0.0782    0.1473
  ```

- <span id="item:companion" label="item:companion"></span><u>*Companion matrix*</u>  The matrix stores the companion matrix. The companion matrix allows rewriting VARs with lags greater than $1$ as VAR(1) (see Box that section in Section that section). For a VAR(1), the companion matrix equals with the deterministic columns removed. The companion matrix plays a central role in computing impulse responses and in implementing identification schemes; Section [sec:dynamic](06-structural-dynamic-analysis.md) develops this in detail (see also Box that section in Section that section).

- <u>*Equation-by-equation estimation output*</u>. The structures and include the OLS equation-by-equation estimation results (coefficients, standard errors, $t$-statistics, $p$-values, fitted values, residuals, and goodness-of-fit statistics for each equation). These sub-structures take their names from the mnemonics in , set above to , so each equation is accessed by variable name — convenient for reading the output of larger systems. When is not provided the sub-structures are named , …, instead; the same fallback applies whenever is empty, of the wrong length, non-unique, contains entries that are not valid field names (e.g. labels with spaces), or clashes with a reserved field of the VAR structure. The resolved names are also recorded in , a $k\times 1$ cell array (here ) that downstream functions such as use to read the equations by the same labels. The labelling affects only the field names: the contents and the column order of every output are unchanged. The mnemonics in are used solely to name these sub-structures, while holds the variable labels used by the plotting functions.

The VAR structure includes several empty objects, which fall into two categories. Some are empty because they depend on an identification step that has not yet been performed. The most important is , which stores the *structural impact matrix* $B$ — the $k\times k$ matrix defined by $u_t = B\varepsilon_t$ (equation that section) that links structural shocks to reduced-form residuals. Since identification is taken up in Section [sec:ident](04-identification-in-the-var-toolbox.md), remains empty for now. Others are empty because the current specification does not include the corresponding feature. For example, stores any variables treated as fully exogenous: variables entered as additional regressors in every equation of the VAR but not modeled as endogenous. In the current bivariate VAR no exogenous variables are included (), so is empty. A natural application where one would populate is, for example, a small open economy VAR, where world oil prices are typically treated as fully exogenous on the grounds that the small economy cannot affect them. Rather than adding oil prices as an endogenous variable — which would require modeling their dynamics as a function of the domestic variables — they enter each equation as exogenous regressors, passed as the optional fifth argument of (after ), with a user-specific number of lags.

The structure is created by and holds all options for identification, inference, and plotting. Table that section lists every field, grouped by role, together with its default value and meaning; the table mirrors the content in , which can be inspected directly for the same information. All fields have sensible defaults; the user sets only those relevant to the current step.

<div id="tab:varopt">

<table>
<caption>Fields of the <span style="background-color: script!80"><code>VARopt</code></span> options structure, with default values.</caption>
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
<td style="text-align: left;"><span style="background-color: script!80"><code>mnem = []</code></span></td>
<td style="text-align: left;">Endogenous variable mnemonics: valid MATLAB identifiers (no spaces or special characters) used to name the per-equation sub-structs. Falls back to <span style="background-color: script!80"><code>eq1</code></span>,…,<span style="background-color: script!80"><code>eqN</code></span> if empty or invalid.</td>
</tr>
<tr>
<td style="text-align: left;"><span style="background-color: script!80"><code>vnames = []</code></span></td>
<td style="text-align: left;">Endogenous variable names: display labels for plots and tables (may contain spaces or LaTeX). Falls back to <span style="background-color: script!80"><code>mnem</code></span> if empty.</td>
</tr>
<tr>
<td style="text-align: left;"><span style="background-color: script!80"><code>vnames_ex = []</code></span></td>
<td style="text-align: left;">Exogenous variable names.</td>
</tr>
<tr>
<td style="text-align: left;"><span style="background-color: script!80"><code>snames = []</code></span></td>
<td style="text-align: left;">Shock names (default to <span style="background-color: script!80"><code>vnames</code></span> if empty).</td>
</tr>
<tr>
<td style="text-align: left;"></td>
<td style="text-align: left;"></td>
</tr>
<tr>
<td style="text-align: left;"><span style="background-color: script!80"><code>ident = ’’</code></span></td>
<td style="text-align: left;">Identification scheme: <span style="background-color: script!80"><code>’’</code></span> (none, reduced form only), <span style="background-color: script!80"><code>’short’</code></span> (zero contemporaneous), <span style="background-color: script!80"><code>’long’</code></span> (zero long-run), <span style="background-color: script!80"><code>’sign’</code></span> (sign restrictions), <span style="background-color: script!80"><code>’sign+iv’</code></span> (sign restrictions with an IV-identified first shock), <span style="background-color: script!80"><code>’iv’</code></span> (external instrument), <span style="background-color: script!80"><code>’exog’</code></span> (exogenous variable).</td>
</tr>
<tr>
<td style="text-align: left;"><span style="background-color: script!80"><code>IV = []</code></span></td>
<td style="text-align: left;">External instrument matrix for <span style="background-color: script!80"><code>ident=’iv’</code></span> or <span style="background-color: script!80"><code>’sign+iv’</code></span>.</td>
</tr>
<tr>
<td style="text-align: left;"><span style="background-color: script!80"><code>exoshock = []</code></span></td>
<td style="text-align: left;">Exogenous shock variable for <span style="background-color: script!80"><code>ident=’exog’</code></span>.</td>
</tr>
<tr>
<td style="text-align: left;"><span style="background-color: script!80"><code>nlag_exoshock = 0</code></span></td>
<td style="text-align: left;">Lag order for <span style="background-color: script!80"><code>exoshock</code></span> (0 = contemporaneous only).</td>
</tr>
<tr>
<td style="text-align: left;"></td>
<td style="text-align: left;"></td>
</tr>
<tr>
<td style="text-align: left;"><span style="background-color: script!80"><code>nsteps = 40</code></span></td>
<td style="text-align: left;">Number of horizons for IRFs and FEVDs.</td>
</tr>
<tr>
<td style="text-align: left;"><span style="background-color: script!80"><code>impact = 0</code></span></td>
<td style="text-align: left;">Shock size: 0 = one standard deviation, 1 = unit shock.</td>
</tr>
<tr>
<td style="text-align: left;"><span style="background-color: script!80"><code>shut = 0</code></span></td>
<td style="text-align: left;">Force the IRF of one variable to zero (0 = off).</td>
</tr>
<tr>
<td style="text-align: left;"><span style="background-color: script!80"><code>recurs = ’wold’</code></span></td>
<td style="text-align: left;">MA representation: <span style="background-color: script!80"><code>’wold’</code></span> (recursive Wold) or companion form <span style="background-color: script!80"><code>’comp’</code></span>.</td>
</tr>
<tr>
<td style="text-align: left;"></td>
<td style="text-align: left;"></td>
</tr>
<tr>
<td style="text-align: left;"><span style="background-color: script!80"><code>inference = 1</code></span></td>
<td style="text-align: left;">1 = parameter uncertainty (default); 0 = point estimates only.</td>
</tr>
<tr>
<td style="text-align: left;"><span style="background-color: script!80"><code>ndraws = 1000</code></span></td>
<td style="text-align: left;">Number of bootstrap draws.</td>
</tr>
<tr>
<td style="text-align: left;"><span style="background-color: script!80"><code>mult = 10</code></span></td>
<td style="text-align: left;">Print progress every <span style="background-color: script!80"><code>mult</code></span> draws.</td>
</tr>
<tr>
<td style="text-align: left;"><span style="background-color: script!80"><code>pctg = 95</code></span></td>
<td style="text-align: left;">Outer confidence level for error bands (percent).</td>
</tr>
<tr>
<td style="text-align: left;"><span style="background-color: script!80"><code>method = ’bs’</code></span></td>
<td style="text-align: left;">Bootstrap method: <span style="background-color: script!80"><code>’bs’</code></span> standard, <span style="background-color: script!80"><code>’wild’</code></span> wild.</td>
</tr>
<tr>
<td style="text-align: left;"></td>
<td style="text-align: left;"></td>
</tr>
<tr>
<td style="text-align: left;"><span style="background-color: script!80"><code>R = []</code></span></td>
<td style="text-align: left;">Sign restriction matrix or struct (required for <span style="background-color: script!80"><code>ident=’sign’</code></span> or <span style="background-color: script!80"><code>’sign+iv’</code></span>).</td>
</tr>
<tr>
<td style="text-align: left;"><span style="background-color: script!80"><code>sr_hor = 1</code></span></td>
<td style="text-align: left;">Number of periods over which sign restrictions apply.</td>
</tr>
<tr>
<td style="text-align: left;"><span style="background-color: script!80"><code>sr_rot = 500</code></span></td>
<td style="text-align: left;">Maximum rotations per draw.</td>
</tr>
<tr>
<td style="text-align: left;"><span style="background-color: script!80"><code>sr_draw = 100000</code></span></td>
<td style="text-align: left;">Maximum total draws.</td>
</tr>
<tr>
<td style="text-align: left;"></td>
<td style="text-align: left;"></td>
</tr>
<tr>
<td style="text-align: left;"><span style="background-color: script!80"><code>pick = 0</code></span></td>
<td style="text-align: left;">Shock to plot: 0 = all, <span style="background-color: script!80"><code>j</code></span> = shock <span style="background-color: script!80"><code>j</code></span> only.</td>
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
<td style="text-align: left;"><span style="background-color: script!80"><code>firstdate = []</code></span></td>
<td style="text-align: left;">First sample date (e.g. <span style="background-color: script!80"><code>1999.75</code></span> = 1999Q4); with <span style="background-color: script!80"><code>frequency</code></span>, controls the axis date labels.</td>
</tr>
<tr>
<td style="text-align: left;"><span style="background-color: script!80"><code>frequency = ’q’</code></span></td>
<td style="text-align: left;">Data frequency: <span style="background-color: script!80"><code>’q’</code></span> quarterly, <span style="background-color: script!80"><code>’m’</code></span> monthly, <span style="background-color: script!80"><code>’y’</code></span> yearly.</td>
</tr>
<tr>
<td style="text-align: left;"><span style="background-color: script!80"><code>datenticks = 5</code></span></td>
<td style="text-align: left;">Target number of date ticks on the x-axis (HD plots); fewer avoids slanted year labels in narrow panels.</td>
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
<td style="text-align: left;">Marker style for the IRF line (<span style="background-color: script!80"><code>’o’</code></span>, <span style="background-color: script!80"><code>’none’</code></span>, etc.).</td>
</tr>
<tr>
<td style="text-align: left;"><span style="background-color: script!80"><code>subplot = []</code></span></td>
<td style="text-align: left;">Subplot grid <span style="background-color: script!80"><code>[rows cols]</code></span>; empty = auto from <span style="background-color: script!80"><code>sqrt(nvars)</code></span>.</td>
</tr>
<tr>
<td style="text-align: left;"><span style="background-color: script!80"><code>shorttitle = 0</code></span></td>
<td style="text-align: left;">1 = show the variable name only as the panel title.</td>
</tr>
<tr>
<td style="text-align: left;"><span style="background-color: script!80"><code>color = []</code></span></td>
<td style="text-align: left;">Line and band color (RGB triplet); empty = <span style="background-color: script!80"><code>pantone(’Blue’)</code></span>.</td>
</tr>
<tr>
<td style="text-align: left;"><span style="background-color: script!80"><code>linestyle = ’-’</code></span></td>
<td style="text-align: left;">IRF line style (<span style="background-color: script!80"><code>’-’</code></span>, <span style="background-color: script!80"><code>’--’</code></span>, <span style="background-color: script!80"><code>’:’</code></span>, <span style="background-color: script!80"><code>’-.’</code></span>).</td>
</tr>
<tr>
<td style="text-align: left;"><span style="background-color: script!80"><code>hstart = 1</code></span></td>
<td style="text-align: left;">First horizon label on the x-axis (0 or 1).</td>
</tr>
<tr>
<td style="text-align: left;"><span style="background-color: script!80"><code>xlim = []</code></span></td>
<td style="text-align: left;">x-axis limits <span style="background-color: script!80"><code>[lo hi]</code></span>; empty = auto.</td>
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
<tr>
<td style="text-align: left;"><span style="background-color: script!80"><code>legcols = 1</code></span></td>
<td style="text-align: left;">Number of columns in the legend.</td>
</tr>
<tr>
<td style="text-align: left;"><span style="background-color: script!80"><code>legloc = ’best’</code></span></td>
<td style="text-align: left;">Legend location: <span style="background-color: script!80"><code>’best’</code></span> = auto-corner, or any explicit MATLAB location string.</td>
</tr>
<tr>
<td style="text-align: left;"></td>
<td style="text-align: left;"></td>
</tr>
<tr>
<td style="text-align: left;"><span style="background-color: script!80"><code>hd_colors = []</code></span></td>
<td style="text-align: left;">RGB matrix (<span style="background-color: script!80"><code>ncols</code></span><span class="math inline">×</span>3) overriding bar colors in stack order; empty = use the default colormap.</td>
</tr>
<tr>
<td style="text-align: left;"><span style="background-color: script!80"><code>hd_detc = 1</code></span></td>
<td style="text-align: left;">1 = stack all HD components (const, trend, init, exogenous, shocks), with bars summing to the <span style="background-color: script!80"><code>Data</code></span> line; 0 = stack shock contributions only, with the reference line equal to data minus const and init.</td>
</tr>
<tr>
<td style="text-align: left;"></td>
<td style="text-align: left;"></td>
</tr>
<tr>
<td style="text-align: left;"><span style="background-color: script!80"><code>dates = []</code></span></td>
<td style="text-align: left;">Cell array of date strings, one per observation; required by <span style="background-color: script!80"><code>SR.m</code></span> for string-format narrative periods.</td>
</tr>
</tbody>
</table>

</div>

The most important fields are the identification scheme (<span style="background-color: script!80">`ident`</span>), the external instrument (<span style="background-color: script!80">`IV`</span>), the sign restriction matrix or struct (<span style="background-color: script!80">`R`</span>), the number of IRF horizons (<span style="background-color: script!80">`nsteps`</span>), the mnemonics that name the equation sub-structs (<span style="background-color: script!80">`mnem`</span>), the variable labels used by the plotting functions (<span style="background-color: script!80">`vnames`</span>), the confidence level for bootstrap bands (<span style="background-color: script!80">`pctg`</span>), and the flag for inference for impulse responses, variance decompositions, and historical decompositions (<span style="background-color: script!80">`inference`</span>). Because the default is <span style="background-color: script!80">`inference = 1`</span>, the structural examples in Section [sec:ident](04-identification-in-the-var-toolbox.md) will set <span style="background-color: script!80">`inference = 0`</span> explicitly so that the figures report point estimates; statistical inference is introduced separately in Section [sec:inference](05-statistical-inference.md). For example, the code below adds variable labels before printing the OLS table:

``` matlab
VARopt.vnames = Xvnames;
```

Finally, the VAR Toolbox provides a built-in function to display the most important estimation results in the command window:

``` matlab
[TABLE, beta] = VARprint(VAR_redform,VARopt);
```

which produces the following output in the MATLAB command window:

``` text
Reduced-form VAR estimation:

                         Real GDP Growth    1-year Int. Rate 
constant                       0.3630          -0.0729 
Real GDP Growth(-1)            0.3788           0.2607 
1-year Int. Rate(-1)           0.0041           0.9541 

VAR eigenvalues:
0.3769
0.95592

Reduced-form covariance matrix:
0.28909       0.078151
0.078151      0.14726
```

The columns of the printed table correspond to the equations of the VAR (one per endogenous variable), and the rows list the constant $c$ and the elements of the lag coefficient matrices $\Phi_1, \ldots, \Phi_p$ in equation that section: a row labelled <span style="background-color: script!80">`VariableName(-j)`</span> gives the coefficient on the $j$-period lag of that variable in each equation. The cell array <span style="background-color: script!80">`beta`</span> includes the estimated values of the coefficients in the VAR, while the cell array <span style="background-color: script!80">`TABLE`</span> includes — in addition to the estimated coefficients — their standard errors, t-statistics, and p-values.

**<u>Checking stability</u>.** The VAR Toolbox automatically computes the eigenvalues of the companion matrix $\mathcal{F}$ during estimation, as discussed in Section that section. The maximum eigenvalue (in modulus) is stored in <span style="background-color: script!80">`VAR_redform.maxEig`</span>:

``` text
>> disp(VAR_redform.maxEig)
    0.9559
```

A maximum modulus strictly less than one confirms that all eigenvalues of $\mathcal{F}$ lie inside the unit circle and the VAR is stable. All eigenvalues of the companion matrix <span style="background-color: script!80">`VAR_redform.Fcomp`</span> can be inspected via MATLAB’s <span style="background-color: script!80">`eig`</span> function:[^7]

``` text
>> disp(eig(VAR_redform.Fcomp))
    0.3769
    0.9559
```

If any eigenvalue exceeds one in modulus, the VAR is unstable and the impulse responses, variance decompositions, and other dynamic analyses discussed in Section [sec:dynamic](06-structural-dynamic-analysis.md) will not be well-defined. Common remedies include adjusting the lag order, re-examining the variable selection, or transforming non-stationary variables (e.g. by first-differencing).

**<u>In sum.</u>**  This section has shown how to estimate the reduced-form VAR by OLS, delivering $\hat{c}$, $\hat{\Phi}_1,\ldots,\hat{\Phi}_p$, $\hat{\Sigma}_u$, and the eigenvalues of the companion matrix. These objects fully characterize the linear dynamics of $x_t$ but carry no structural interpretation. Recovering economically meaningful shocks requires solving the identification problem introduced in Section that section: finding a $k\times k$ matrix $B$ such that $\Sigma_u = BB'$. As established there, this system is underdetermined — in the bivariate case, the three independent equations from $\Sigma_u = BB'$ cannot pin down all four elements of $B$. This is reflected directly in the <span style="background-color: script!80">`VAR_redform`</span> structure: after estimation, <span style="background-color: script!80">`VAR_redform.B`</span> is empty (as seen in the output above), because the link between reduced-form residuals and structural shocks has not yet been established. Section [sec:ident](04-identification-in-the-var-toolbox.md) addresses this challenge by imposing economic restrictions that select a unique $B$ matrix.

[^1]: As discussed in more detail in Box that section, such a simple VAR cannot realistically describe the complex interactions of the US economy, but it is a useful pedagogical device: with only two variables and one lag, the algebra is tractable and the toolbox mechanics are easy to follow. The VAR Toolbox also includes more realistic examples based on replications of existing papers (see the appendix); the replication codes can be found in the folder .

[^2]: The two conventions are related as follows: the $t$-th row of is the row vector $x_t'$, for $t=1,\ldots,T$.

[^3]: With one lag and a constant, OLS estimation in turn uses the $122=123-1$ effective observations that remain once the lagged regressor is formed.

[^4]: Estimation hats are suppressed throughout for readability.

[^5]: The relationship between and $x_t$ is described in the footnote attached to equation that section above.

[^6]: The assumption that $u_t$ is serially uncorrelated can be tested using standard portmanteau tests (e.g. the Ljung-Box test) applied to the estimated residuals. Residual serial correlation typically signals that the lag order $p$ is too low or that the model is otherwise misspecified; in practice, it is good practice to increase $p$ until residual autocorrelation is no longer present.

[^7]: Note that is the companion matrix built excluding the constant $c$ from the coefficient matrix . See Box that section for more details on how to construct the companion matrix.
