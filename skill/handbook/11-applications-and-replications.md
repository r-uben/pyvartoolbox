---
title: "Applications and Replications"
label: "sec:applications"
source: VAR Handbook (Cesa-Bianchi)
type: reformatted-extract
licence: GPL-3.0
---

# Applications and Replications

> **Source.** This page is a reformatted extract of the *VAR Handbook* by
> Ambrogio Cesa-Bianchi, from the MATLAB VAR Toolbox (https://github.com/ambropo/VAR-Toolbox). The content is
> his; only the format has changed, so that it can be read in fragments by a
> machine. Redistributed under the GPL-3.0 the original carries. Code
> listings are **MATLAB** and do not apply to `pyvartoolbox` — see
> [conventions](../references/conventions.md) for where the APIs differ.

The applications and replications in this section complement the theoretical exposition in the main text by showing the identification methods at work on canonical empirical datasets. The simple bivariate VAR used throughout the handbook serves a purely pedagogical purpose: with only two variables and one lag, the algebra remains transparent and the mechanics of the toolbox are not obscured by complexity. These six applications take a step closer to genuine empirical practice.

Each replication selects a canonical study from the VAR literature, reproduces its key findings using the VAR Toolbox, and connects the implementation to the identification methods developed in the main text. The first five replications span the main SVAR identification strategies: recursive identification , long-run restrictions , sign restrictions , narrative sign restrictions , and external instruments . The sixth replication illustrates local projection methods (both LP-OLS and LP-IV) following the treatment in .

Replication scripts are stored in and named . The MATLAB boxes below show concise snippets that highlight the key steps of each application. The complete executable code, including data loading, transformations, and figure options, is in .[^1]

## Stock and Watson (2001): Zero Short-Run Restrictions

What are the effects of monetary policy shocks on inflation and unemployment? address this question using a trivariate VAR estimated on quarterly US data from 1960:Q1 to 2000:Q4. The three endogenous variables are inflation ($\pi_t = 400(\log P_t - \log P_{t-1})$, annualized quarterly log change in the chain-weighted GDP price index), the unemployment rate ($u_t$, percent), and the federal funds rate ($r_t$, percent at annual rate). The specification is a VAR(4) with a constant.

The identification strategy rests on two timing assumptions. First, the policy rate can respond contemporaneously to inflation and unemployment, reflecting the Federal Reserve’s ability to observe current-quarter macroeconomic conditions, so the federal funds rate is ordered last. Second, monetary policy shocks have no contemporaneous effect on inflation or unemployment, reflecting the well-known long and variable lags of monetary transmission. Together, these assumptions imply a lower-triangular impact matrix $B$:
$$
\begin{bmatrix}
\pi_t \\
u_t \\
r_t
\end{bmatrix}
= \sum_{p=1}^{4} \Phi_p x_{t-p} +
\begin{bmatrix}
b_{11} & 0 & 0 \\
b_{21} & b_{22} & 0 \\
b_{31} & b_{32} & b_{33}
\end{bmatrix}
\begin{bmatrix}
\varepsilon_t^{1} \\
\varepsilon_t^{2} \\
\varepsilon_t^{MonPol}
\end{bmatrix}
$$
The lower-triangular structure is implemented by a Cholesky decomposition of the reduced-form covariance matrix $\Sigma_u = BB'$; see Section that section for the algebraic derivation. Inflation is ordered first, unemployment second, and the policy rate third, reflecting the assumption that the inflation and unemployment shocks are unaffected by the monetary policy shock on impact, while the federal funds rate can respond to their contemporaneous values.

Assuming the data have been loaded into the struct, the key implementation steps are:

``` matlab
X = [DATA.infl, DATA.unemp, DATA.ff]; 
nlags = 4;  detc = 1;
% Identification setup and impulse responses with bootstrap bands
VARopt = VARoption;
VARopt.vnames    = {'Inflation','Unemployment','Fed Funds'};
VARopt.nsteps    = 24;
VARopt.snames    = {bfeps('1'), bfeps('2'), bfeps('MonPol')};
VARopt.ident     = 'short';
VARopt.inference = 1;
```

Identification and the computation and plotting of the impulse responses then follow from the usual lines of code:

``` matlab
VAR = VARmodel(X, nlags, detc, VARopt);
VARirplot(VAR.IRbar, VARopt, VAR.IRinf, VAR.IRsup);
```

Figure that section reports the impulse responses to the three identified shocks. The identified monetary policy shock delivers the expected pattern: a contractionary shock raises the federal funds rate and, after a lag, increases unemployment and lowers inflation.

> **Figure.** Stock and Watson (2001): Figure 3

The other two shocks carry no a priori economic label: they are simply the remaining orthogonal components defined by the Cholesky ordering. Their impulse responses suggest supply- and demand-like patterns, but these labels are *ex post* interpretations rather than identifying restrictions. This is a general limitation of recursive identification: the chosen variable order embeds strong timing assumptions that determine which shocks are identified and how, and the economic content of each shock depends on that choice.

## Blanchard and Quah (1989): Zero Long-Run Restrictions

How do aggregate supply and demand shocks differ in their effects on output and unemployment? exploit the long-run neutrality of demand shocks implied by classical macroeconomic theory to answer this question. Using quarterly US data from 1948:Q1 to 1987:Q4, they estimate a VAR(8) with a constant that includes two variables: real GNP growth ($\Delta y_t$, percent at quarterly rate) and the unemployment rate ($u_t$, percent). The VAR is specified in growth rates for output, not levels, which matters for how the long-run restriction is expressed.

The key identifying assumption is that demand shocks have no long-run effect on the level of output, while supply shocks do. The restriction imposes long-run neutrality of demand shocks: their cumulative effect on the level of output is zero. The classical interpretation is that in the long run, output is governed by supply-side factors such as technology and capital accumulation, while demand shocks produce only transitory fluctuations. Since the VAR is in growth rates, the restriction on output levels translates into a zero cumulative impulse response of output growth to the demand shock. In matrix notation, the long-run impact matrix must be lower triangular:
$$
\begin{bmatrix}
\Delta y_{t,t+\infty} \\
u_{t,t+\infty}
\end{bmatrix}
=
\begin{bmatrix}
c_{11} & 0 \\
c_{21} & c_{22}
\end{bmatrix}
\begin{bmatrix}
\varepsilon_t^{Supply} \\
\varepsilon_t^{Demand}
\end{bmatrix}
$$
where $C \equiv (I-\Phi)^{-1}B$ is the long-run impact matrix defined in equation that section of Section that section. The zero upper-right element $c_{12} = 0$ imposes long-run neutrality of demand shocks on output, which is why output growth is ordered first; no restriction is placed on the long-run response of unemployment to either shock. See Section that section for the algebraic derivation.

Assuming the data have been loaded into the struct, the key implementation steps are:

``` matlab
X = [DATA.y, DATA.u]; % GDP growth, unemployment
nlags = 8;  detc = 1;
% Identification setup and impulse responses with bootstrap bands
VARopt = VARoption;
VARopt.vnames    = {'GDP growth','Unemployment'};
VARopt.nsteps    = 40;
VARopt.frequency = 'q';
VARopt.snames    = {bfeps('Supply'), bfeps('Demand')};
VARopt.ident     = 'long';
VARopt.inference = 1;
```

Identification and the computation and plotting of the impulse responses then follow from the usual lines of code:

``` matlab
VAR = VARmodel(X, nlags, detc, VARopt);
VARirplot(VAR.IRbar, VARopt, VAR.IRinf, VAR.IRsup);
```

Figure that section reports the impulse responses to the two identified shocks: the supply shock (panel A) and the demand shock (panel B). Each panel plots the responses of output growth and the unemployment rate, with the solid line denoting the bootstrap mean and the shaded bands the 95% bootstrap confidence intervals.

> **Figure.** Impulse Responses to a Supply and a Demand Shock

Figure that section reports the *cumulative* impulse responses, obtained by cumulating the responses of output growth into the implied response of the output level. Plotting the responses in cumulative form makes the identifying restriction directly visible: the cumulative response of output to the demand shock converges to zero at long horizons, exactly as imposed by long-run neutrality, while the response to the supply shock settles at a non-zero level. The identified supply shock thus produces a permanent increase in output — the cumulative impulse response of GDP growth converges to a positive value, reflecting a lasting shift in productive capacity.

> **Figure.** Blanchard and Quah (1989): Figures 1 and 2

The demand shock has no long-run effect on output by construction, but lowers unemployment on impact and drives it back toward baseline over subsequent quarters — a pattern consistent with transitory demand fluctuations. These patterns align with the classical supply–demand dichotomy: supply shocks permanently shift the productive frontier, while demand shocks trace out cyclical fluctuations around it. What makes the exercise instructive is that a single long-run exclusion restriction — demand shocks are neutral for the level of output — suffices to separate permanent from transitory sources of fluctuations, with no restriction imposed on the short-run dynamics.

## Uhlig (2005): Sign Restrictions

What are the effects of monetary policy on output? revisits this classic question with a deliberately agnostic approach. Rather than relying on timing assumptions or long-run restrictions, Uhlig imposes only sign restrictions that capture conventional wisdom about monetary transmission, allowing the data to speak more freely about the output effects of monetary policy (see Section that section).

Using monthly US data from 1965:M1 to 2003:M12, Uhlig estimates a VAR(12) with a constant that includes six variables: real GDP ($rgdp_t$, log, interpolated at monthly frequency), the GDP deflator ($p_t$, log), a commodity price index ($p_t^{com}$, log), total reserves ($tr_t$, log), non-borrowed reserves ($nbr_t$, log), and the federal funds rate ($ff_t$, percent). Log-level variables are scaled by 100. The sign restrictions on impulse responses, imposed for $h = 0, 1, \ldots, 5$ (six months), are shown in equation that section: $+$ and $-$ denote required signs; $?$ denotes no restriction. Any rotation matrix $Q_j$ producing responses that violate these restrictions at any of the first six horizons is discarded; see Section that section for the algorithm. No restriction is imposed on industrial production — the variable of interest — allowing the data to determine its response freely. In practice, the restrictions look like as follows:
$$

\begin{bmatrix}
rgdp_t \\ p_t \\ p_t^{com} \\ tr_t \\ nbr_t \\ ff_t
\end{bmatrix}
= \sum_{p=1}^{12} \Phi_p x_{t-p} +
\begin{bmatrix}
{?} & {?} & {?} & {?} & {?} & {?} \\
{-} & {?} & {?} & {?} & {?} & {?} \\
{-} & {?} & {?} & {?} & {?} & {?} \\
{?} & {?} & {?} & {?} & {?} & {?} \\
{-} & {?} & {?} & {?} & {?} & {?} \\
{+} & {?} & {?} & {?} & {?} & {?}
\end{bmatrix}
\begin{bmatrix}
\varepsilon_t^{MonPol} \\ \varepsilon_t^{2} \\ \varepsilon_t^{3} \\ \varepsilon_t^{4} \\ \varepsilon_t^{5} \\ \varepsilon_t^{6}
\end{bmatrix}
$$

In the VAR Toolbox, sign restrictions are encoded in a matrix with rows for variables and columns for shocks. Only the first column (the monetary policy shock) carries non-zero entries; the remaining columns are zero, leaving the other five shocks unrestricted. The option enforces the restrictions for the first 6 months. Assuming the data have been loaded into the struct, the key implementation steps are:

``` matlab
X = [DATA.y, DATA.pi, DATA.comm, DATA.res, DATA.nbres, DATA.ff];
nlags = 12;  detc = 1;
% Identification setup and impulse responses
VARopt = VARoption;
VARopt.ndraws    = 500;
VARopt.sr_hor    = 6;
VARopt.inference = 1;  
VARopt.nsteps    = 60;
VARopt.frequency = 'm';
VARopt.pctg      = 68;
VARopt.snames    = {bfeps('MonPol')};
% R: 1 = positive, -1 = negative, 0 = unrestricted
R = [ 0, 0, 0, 0, 0, 0;   % Industrial production (unrestricted)
     -1, 0, 0, 0, 0, 0;   % GDP Deflator (negative)
     -1, 0, 0, 0, 0, 0;   % Commodity Prices (negative)
      0, 0, 0, 0, 0, 0;   % Total Reserves (unrestricted)
     -1, 0, 0, 0, 0, 0;   % NonBorr. Reserves (negative)
      1, 0, 0, 0, 0, 0];  % Fed Funds (positive)
% Identify with sign restrictions
VARopt.ident = 'sign';
VARopt.R = R;
```

Identification and the computation and plotting of the impulse responses then follow from the usual lines of code:

``` matlab
VAR_sr = VARmodel(X, nlags, detc, VARopt);
VARirplot(VAR_sr.IRmed, VARopt, VAR_sr.IRinf, VAR_sr.IRsup);
```

> **Figure.** Uhlig (2005): Figure 6

Figure that section reports the impulse responses to the contractionary monetary policy shock. The key finding is that the output response is ambiguous: while the restricted variables respond as assumed — the federal funds rate rises, the price level and non-borrowed reserves fall — the impulse response of industrial production (top-left panel) is highly uncertain, with the 68% credible interval spanning both positive and negative values. Uhlig interprets this as evidence that the data, under minimal identifying restrictions, do not deliver a clear verdict on the output effects of monetary policy.

Two features of the figure are worth emphasizing for interpretation. First, the model is set-identified: each accepted rotation $Q_j$ generates one admissible impulse response, and the shaded bands trace the 16th–84th percentiles of the responses across all accepted draws ( and ), with the solid line the element-wise median (). The bands thus summarize identification (rotation) uncertainty and, when , sampling uncertainty as well; they are not the confidence intervals of a single point estimate. Second, the restricted responses carry the imposed sign over the constrained horizons $h = 0, \ldots, 5$ by construction, whereas their behavior at longer horizons — and the entire path of real GDP — is governed by the estimated reduced-form dynamics. The contrast between the tightly signed responses of the restricted variables and the diffuse response of industrial production is precisely what the agnostic identification is designed to surface.

Antolín-Díaz and Rubio-Ramírez (2018):\
Narrative Sign Restrictions
---------------------------------------

Can narrative evidence about specific historical episodes sharpen inference from sign restrictions? propose to augment the standard sign restrictions approach with *narrative restrictions* — additional constraints tied to well-documented historical events. They apply this idea to the Uhlig (2005) six-variable monetary VAR, retaining the same sign restrictions but extending the sample to 1965:M1–2007:M11 and estimating without a constant (following footnote 8 of , p. 27, who demean the data prior to estimation). The additional identifying information comes from October 1979, the month of the Volcker disinflation announcement.

Historical records leave little doubt about two facts regarding that episode. First, the monetary policy shock was strongly positive: the Fed tightened aggressively and unexpectedly. Second, monetary policy was the dominant driver of the unexpected movement in the federal funds rate that month, with no comparably large competing shocks. These two observations motivate two narrative restrictions targeted at 1979:M10:

- $\varepsilon_{1979:M10}^{MonPol} > 0$

- $\bigl|b_{6m}\,\varepsilon_{1979:M10}^{MonPol}\bigr| > \textstyle\sum_{k\neq m}\bigl|b_{6k}\,\varepsilon_{k,1979:M10}\bigr|$

where $b_{6m}$ is the element of $B$ in row 6 (federal funds rate) and column $m$ (monetary policy shock), so each product $b_{6k}\,\varepsilon_{k,1979:M10}$ measures the contribution of structural shock $k$ to the federal funds rate residual in that month. The Type 2 inequality therefore requires the monetary policy shock to account for more of the unexpected movement in the federal funds rate than all other shocks combined. Any candidate rotation matrix $Q_j$ that satisfies the sign restrictions but violates any narrative constraint is discarded. See Section that section for the algebraic formulation and acceptance-rejection algorithm.

In the VAR Toolbox, narrative restrictions are passed to via , a struct combining the sign restriction matrix with the narrative fields and . Assuming the data have been loaded into the struct, the key implementation steps are:

``` matlab
X = [DATA.y, DATA.pi, DATA.comm, DATA.res, DATA.nbres, DATA.ff];
nlags = 12;  detc = 0;
% Identification setup and impulse responses
VARopt = VARoption;
VARopt.nsteps = 60;
VARopt.sr_hor = 6;
VARopt.snames = {bfeps('MonPol')};
VARopt.dates  = dates;
% Sign restrictions matrix (column 1: MP shock)
R.sign = [ 0, 0, 0, 0, 0, 0;
          -1, 0, 0, 0, 0, 0;
          -1, 0, 0, 0, 0, 0;
           0, 0, 0, 0, 0, 0;
          -1, 0, 0, 0, 0, 0;
           1, 0, 0, 0, 0, 0];
% Type 1: MP shock positive at October 1979
R.narr_sign.shock  = 1;
R.narr_sign.period = '1979m10';
R.narr_sign.sign   = 1;
% Type 2: MP shock dominant for ff at October 1979
R.narr_dom.shock  = 1;
R.narr_dom.period = '1979m10';
R.narr_dom.var    = 6;
% Identify with sign + narrative restrictions
VARopt.ident = 'sign';
VARopt.R = R;
```

Identification and the computation and plotting of the impulse responses then follow from the usual lines of code:

``` matlab
VAR_nsr = VARmodel(X, nlags, detc, VARopt);
VARirplot(VAR_nsr.IRmed, VARopt, VAR_nsr.IRinf, VAR_nsr.IRsup);
```

Figure that section reports the impulse responses to the contractionary monetary policy shock under sign restrictions alone (blue) and under sign plus narrative restrictions (red). Adding the October 1979 narrative restrictions substantially narrows the identified set relative to sign restrictions alone: the red credible bands are noticeably tighter than the blue ones, and the central estimates shift. Both effects reflect the same mechanism: candidates that satisfy the sign restrictions but are inconsistent with the Volcker episode are discarded, leaving a smaller and differently located set of admissible impulse responses.

In particular, monetary policy now has a clear effect on output: the sign-only response (blue, top-left panel) is positive or indeterminate, whereas the narrative restrictions push the median output response (red) below zero at medium and longer horizons, so that a contractionary monetary policy shock now lowers output — resolving the ambiguity left by the agnostic identification of . The result is sharper inference about the effects of monetary policy, achieved by conditioning on one well-documented historical episode.

> **Figure.** Antolín-Díaz and Rubio-Ramírez (2018): Figure 8

The mechanism is seen most directly in the distribution of the identified monetary policy shock at the targeted date. Figure that section plots, across accepted draws, the structural monetary policy shock in October 1979 under sign restrictions alone (blue) and under sign plus narrative restrictions (red). Under sign restrictions alone the shock is roughly symmetric about zero, so the data are consistent with either an expansionary or a contractionary impulse in that month. The narrative restrictions truncate and reshape this distribution: Type 1 discards every draw with a non-positive shock, removing all mass to the left of zero, while Type 2 retains only draws in which the monetary policy shock dominates the federal funds rate movement, concentrating the surviving mass on large positive values. The tighter impulse response bands in Figure that section are the downstream consequence of this reweighting of the admissible draws.

> **Figure.** Antolín-Díaz and Rubio-Ramírez (2018): Distribution of the monetary policy shock at October 1979

## Gertler and Karadi (2015): External Instruments

How does monetary policy affect credit markets? focus on the credit channel of monetary transmission, exploiting high-frequency movements in asset prices around FOMC announcements to identify monetary policy shocks cleanly.

Using monthly US data from 1979:M7 to 2012:M6, they estimate a VAR(12) with a constant that includes four variables: the 1-year Treasury bill rate (percent), the consumer price index (log), industrial production (log), and the excess bond premium (percent). The excess bond premium (EBP), constructed by , measures the component of corporate credit spreads orthogonal to expected default risk; it captures financial market frictions and tightening credit conditions. The policy rate is placed first in the variable ordering; this is required by the VAR Toolbox implementation, which instruments the residual of the first variable, and does not reflect a theoretical restriction of the external-instrument approach.

The instrument is constructed from changes in federal funds futures prices in a narrow window around FOMC announcements:
$$
z_t = -(P_{t,\tau+20} - P_{t,\tau-10})
$$
where $P_{t,\tau}$ is the futures price at time $\tau$ (measured in minutes relative to the announcement) on day $t$. The subscripts $\tau-10$ and $\tau+20$ define a 30-minute window; the negative sign converts a futures price increase into a positive rate reading, since futures prices move inversely to interest rates, so $z_t > 0$ corresponds to an unexpected policy tightening. The instrument must satisfy relevance ($\mathbb{E}[\varepsilon_t^{MonPol} z_t'] \neq 0$) and exogeneity ($\mathbb{E}[\varepsilon_t^i z_t'] = 0$ for $i \neq \text{MonPol}$). See Section that section for the identification argument. Assuming the data have been loaded into the struct, the key implementation steps are:

``` matlab
X  = [DATA.gs1, DATA.logcpi, DATA.logip, DATA.ebp];
IV = DATA.ff4_tc;  % FF4 futures surprise
nlags = 12;  detc = 1;
% Options
VARopt = VARoption;
VARopt.nsteps    = 48;
VARopt.frequency = 'm';
VARopt.method    = 'wild';
VARopt.ndraws    = 500;
VARopt.inference = 1;
VARopt.pick      = 1;
% (1) Recursive (Cholesky) identification: policy rate ordered first
VARopt.ident     = 'short';
VAR_chol = VARmodel(X, nlags, detc, VARopt);
% (2) External-instrument identification (proxy SVAR)
VARopt.ident     = 'iv';
VARopt.IV        = IV;
VAR_iv   = VARmodel(X, nlags, detc, VARopt);
```

Figure that section reproduces the central comparison of : the same four-variable VAR(12) is identified two ways, and the two sets of impulse responses are plotted side by side. The left column (red) identifies the monetary policy shock by a recursive (Cholesky) ordering with the policy rate ordered first; the right column (black) identifies it with the external instrument (proxy SVAR) of Section that section, using the FF4 futures surprise. Because the reduced-form dynamics are held fixed and only the identifying assumption changes, the figure isolates the contribution of the identification scheme itself to the estimated transmission.

> **Figure.** Gertler and Karadi (2015): Figure 1

The recursive identification displays the familiar pathologies of timing restrictions in monetary VARs. The price level rises for roughly two years after a contractionary shock — the *price puzzle* — and industrial production increases on impact before turning negative, neither of which matches the textbook response to a tightening. The excess bond premium barely moves: its point response hovers near zero and the confidence band straddles zero at every horizon, so the recursive scheme detects no role for credit-spread movements in transmission.

The external instrument removes these anomalies. The price level now falls and keeps falling over the horizon, industrial production declines to a trough around a two-year horizon, and the one-year rate rises significantly on impact before reverting. Most consequentially for the credit channel, the excess bond premium jumps sharply on impact — by several basis points — and the response is statistically significant for the first several months before decaying to zero. The contrast with the muted, insignificant recursive response is the empirical core of : once the policy shock is identified cleanly from high-frequency surprises, a monetary tightening is found to widen credit spreads well beyond the movement in the risk-free rate it induces. This excess-bond-premium response is read as evidence that financial frictions play an important role in the transmission of monetary policy.

## Jordà and Taylor (2025): Local Projections and LP-IV

This application illustrates the local projection framework developed in Section [sec:lp](07-local-projections.md). In LP-OLS, causal identification rests on the exogeneity of the shock measure $s_t$; in LP-IV, the endogenous treatment $d_t$ is instrumented by an external proxy $z_t$. Both approaches recover impulse responses without fitting a full structural model, but through different identification arguments. survey local projections, covering both the case where the shock enters the LP regression directly as the treatment variable (LP-OLS) and the case where the shock instruments an endogenous treatment variable (LP-IV). Their survey also introduces the long-difference specification as a practical device for persistent outcome variables. We replicate their Examples 5 and 6 (Figures 5a and 6a in the paper), which together demonstrate both variants of the LP estimator in the context of monetary policy transmission.

**Example 5 (Figure 5a): LP-OLS.** The first exercise estimates the response of log CPI (scaled to percent) to a unit Romer-Romer narrative monetary policy shock using quarterly US data, 1985:Q1–2007:Q4. The Romer-Romer shock $s_t$ is constructed to capture exogenous variation in monetary policy intentions; it enters the LP regression directly as the treatment variable, with no instrumentation required. The dependent variable is specified in long-difference form, $(\log \text{CPI}_{t+h} - \log \text{CPI}_{t-1}) \times 100$. This measures the cumulative change in log CPI from one period before the shock (period $t-1$) to horizon $h$, which is appropriate for persistent series: expressing the outcome as a net change relative to the pre-shock level avoids the level-stationarity problems of a pure level specification. The LP-OLS regression for each $h = 0, 1, \ldots, 18$ is
$$

    (\log \text{CPI}_{t+h} - \log \text{CPI}_{t-1}) \times 100 = \alpha_h + \beta_h \, s_t + \gamma_h' w_t + e_{t+h},
$$
where $w_t$ contains four lags of log real GDP growth, CPI inflation, and the short-term interest rate. The coefficient sequence $\{\hat\beta_h\}_{h=0}^{18}$ directly traces the cumulative CPI response to a unit Romer-Romer shock.

**Example 6 (Figure 6a): LP-IV.** The second exercise estimates the response of the unemployment rate to a 1 percentage point federal funds rate (FFR) shock using monthly US data, 1985:M1–2000:M1. The FFR is an endogenous variable: the Fed adjusts rates in response to economic conditions, so using it directly as $s_t$ would confound the structural shock with the endogenous policy reaction. The solution is instrumental variables. The Romer-Romer narrative shock $z_t$ , as used in , is a measure of exogenous monetary policy variation constructed from Federal Reserve documents and instruments the FFR. The LP-IV regression for each $h = 0, 1, \ldots, 49$ is
$$

    (\text{urate}_{t+h} - \text{urate}_{t-1}) = \alpha_h + \beta_h \, d_t + \gamma_h' w_t + e_{t+h},
$$
where $d_t$ is the FFR (endogenous treatment) and $w_t$ includes six lags of the unemployment rate, inflation, and the FFR. The instrument set consists of the current Romer-Romer shock and its six lags, $\{z_t, z_{t-1}, \ldots, z_{t-6}\}$. With seven instruments for one endogenous regressor the system is over-identified. The VAR Toolbox estimates the LP-IV horizon by horizon via 2SLS rather than two-step GMM as in ; this accounts for some of the quantitative differences between the toolbox output and the original paper’s results. Under 2SLS with multiple instruments, consistency is maintained but the estimator is not asymptotically efficient relative to two-step GMM. At each horizon, $\hat\beta_h$ recovers the cumulative unemployment response to a unit FFR shock, purged of the endogenous variation in $d_t$.

The conceptual distinction between the two exercises reflects a general principle of the LP framework. In LP-OLS, $s_t$ is a direct, exogenous measure of the structural shock and enters as the treatment: consistency requires that $s_t$ be orthogonal to $e_{t+h}$ (exogeneity) and that $s_t$ retain variation after partialling out the controls $w_t$ (a rank condition). In LP-IV, $z_t$ is a noisy proxy that instruments the endogenous treatment $d_t$: consistency requires both instrument relevance ($\mathbb{E}[d_t z_t'] \neq 0$ after partialling out controls) and exogeneity ($\mathbb{E}[e_{t+h} z_t'] = 0$ for all $h$). The LP-IV estimator applies 2SLS horizon by horizon, without fitting a fully specified dynamic model for the endogenous treatment.

Both exercises use Newey-West standard errors with bandwidth $h - 1$, consistent with the MA($h-1$) structure of the LP residuals discussed in Section that section. Confidence bands at 68% and 95% are both reported: the narrower 68% bands are derived from the 95% bands by rescaling. Under the approximation that the sampling distribution of $\hat\beta_h$ is asymptotically normal, the ratio of standard-normal quantiles $\Phi^{-1}(0.84)/\Phi^{-1}(0.975)\approx 1.00/1.96$ maps the 95% half-width to the 68% half-width. Assuming the data have been loaded and samples trimmed to the relevant windows, the key implementation steps are:

``` matlab
LPopt_OLS          = LPoption;
LPopt_OLS.nsteps   = 18;        % 18-quarter horizon
LPopt_OLS.longdiff = 1;         % LHS: lcpi_{t+h} - lcpi_{t-1}
LPopt_OLS.impact   = 1;         % unit shock
LPopt_OLS.pctg     = 95;
CTRL_OLS = [dlrgdp dlcpi dstir];
LP_OLS   = LPmodel(lcpi, rr_shock, CTRL_OLS, 4, 1, LPopt_OLS);
IR_OLS     = LP_OLS.IR;
INF95_OLS  = LP_OLS.INF;
SUP95_OLS  = LP_OLS.SUP;

% LP-IV -- unemployment response to FFR shock (monthly)
LPopt_IV          = LPoption;
LPopt_IV.nsteps   = 49;        % 49-month horizon
LPopt_IV.longdiff = 1;         % LHS: urate_{t+h} - urate_{t-1}
LPopt_IV.impact   = 1;         % unit shock
LPopt_IV.pctg     = 95;
LPopt_IV.IV       = RRCGShock;
LPopt_IV.nlag_iv  = 6;             % lags of instrument
CTRL_IV = [urate infl ffr];
LP_IV   = LPmodel(urate, ffr, CTRL_IV, 6, 1, LPopt_IV);
IR_IV     = LP_IV.IR;
INF95_IV  = LP_IV.INF;
SUP95_IV  = LP_IV.SUP;
```

Figure that section reports both exercises side by side: the LP-OLS response in the left panel (the paper’s Figure 5a) and the LP-IV response in the right panel (the paper’s Figure 6a). The LP-OLS results (Figure 5a) show a negative cumulative response of the price level to a contractionary Romer-Romer shock: log CPI falls by around 2–4 percent (cumulative) over the first 12 quarters, consistent with the standard monetary transmission channel; the magnitude reflects the scale of the Romer-Romer shock measure, which captures large identified policy changes. The LP-IV results (Figure 6a) show that a 1 percentage point contractionary FFR shock raises unemployment, with the response building gradually over 12–24 months before plateauing. Confidence bands are wider in the LP-IV case, reflecting the additional uncertainty from the IV correction and the longer horizon. The comparison between the two exercises illustrates the scope of the LP framework: LP-OLS suffices when a clean shock measure is available, while LP-IV extends the approach to settings where the treatment variable is endogenous and must be instrumented. See Section [sec:lp](07-local-projections.md) for the general LP framework and its connection to the exogenous-variable SVAR.

> **Figure.** Jordà and Taylor (2025): Figures 5a and 6a

[^1]: Sections 11–15 of replicate Stock and Watson (2001), Blanchard and Quah (1989), Uhlig (2005), Antolín-Díaz and Rubio-Ramírez (2018), and Gertler and Karadi (2015), respectively. The sixth replication (Jordà and Taylor, 2025) is in the dedicated script and is not covered in the Primer.
