---
title: "Identification in the VAR Toolbox"
label: "sec:ident"
source: VAR Handbook (Cesa-Bianchi)
type: reformatted-extract
licence: GPL-3.0
---

# Identification in the VAR Toolbox

> **Source.** This page is a reformatted extract of the *VAR Handbook* by
> Ambrogio Cesa-Bianchi, from the MATLAB VAR Toolbox (https://github.com/ambropo/VAR-Toolbox). The content is
> his; only the format has changed, so that it can be read in fragments by a
> machine. Redistributed under the GPL-3.0 the original carries. Code
> listings are **MATLAB** and do not apply to `pyvartoolbox` — see
> [conventions](../references/conventions.md) for where the APIs differ.

The identification problem described in the previous section admits several solutions. This section describes how to implement some of the most popular ones through simple examples using the VAR Toolbox. As noted in Section [sec:rfvar_toolbox](03-var-estimation-in-the-var-toolbox.md), the examples throughout this section are run with parameter uncertainty switched off (), so that the figures display point estimates and the discussion can focus on identification alone; although is the toolbox default, it is disabled here and taken up in detail in Section [sec:inference](05-statistical-inference.md). Specifically, the next subsections cover the following identification schemes: zero contemporaneous restrictions, zero long-run restrictions, sign restrictions, narrative sign restrictions, external instruments, combined sign-IV restrictions, and exogenous variables.

## Zero Contemporaneous Restrictions

Identification using zero contemporaneous restrictions — also known as Cholesky or recursive identification (see the notebox below for why this label is imprecise) — was developed by , and has long been one of the most widely used identification schemes in the literature. The underlying idea is that some structural shocks may take time to transmit through the economy, and therefore have no contemporaneous effects on one or more of the endogenous variables in the VAR. For example, it is widely believed that there are substantial lags in the transmission of monetary policy to the real economy. Under this assumption, one could impose that monetary policy shocks have zero contemporaneous effects on one (or a subset) of the endogenous variables in the VAR.

The bivariate VAR makes this intuition precise. As established in Section that section, the VAR is underidentified: the three independent equations from $\Sigma_u = BB'$ leave one element of $B$ unconstrained. Imposing zero contemporaneous restrictions amounts to assuming that some of the non-diagonal elements of $B$ are equal to zero, thus reducing the number of unknown coefficients.

In the simple case considered here, it will therefore suffice to set to zero one element of the $B$ matrix to solve for the remaining three elements with the three available equations. The question is which element of the $B$ matrix to set to zero. One could maintain the assumption that a monetary policy shock affects the short-term interest rate on impact (i.e. $r_{t}$) but takes time to transmit to the real economy, and affect output ($y_{t}$) only with a lag. This identifying assumption implies that $b_{12}=0$, so that the structural VAR can be written as:
$$
    \left[
    \begin{array}{c}
        y_{t} \\
        r_{t}%
    \end{array}%
    \right] =%
    \begin{bmatrix}
        c_{y} \\
        c_{r} %
    \end{bmatrix}
    +
    \begin{bmatrix}
        \phi _{11} & \phi _{12} \\
        \phi _{21} & \phi _{22}%
    \end{bmatrix}%
    \left[
    \begin{array}{c}
        y_{t-1} \\
        r_{t-1}%
    \end{array}%
    \right] +\left[
    \begin{array}{cc}
        b_{11} & 0 \\
        b_{21} & b_{22}%
    \end{array}%
    \right]
    \begin{bmatrix}
        \varepsilon_{t}^{Demand} \\
        \varepsilon_{t}^{MonPol}%
    \end{bmatrix}%
    ,  
$$
so that $y_{t}$ is not contemporaneously affected by $\varepsilon_{t}^{MonPol}$, while $r_{t}$ is contemporaneously affected by both $\varepsilon_{t}^{Demand}$ and $\varepsilon_{t}^{MonPol}$, through the coefficients $b_{21}$ and $b_{22}$. As we now have $3$ independent equations and $3$ unknowns, we can recover the elements of the $B$ matrix by solving the system of equations implied by $\Sigma_u=BB'$. The structural VAR is thus identified.

**<u>Math</u>.** Zero short-run restrictions achieve identification by reducing the number of free parameters in $B$ until it matches the number of independent equations supplied by $\Sigma_u = BB'$. The number of restrictions required depends on the size of the VAR: for a VAR with $k$ endogenous variables, exact identification requires $k(k-1)/2$ zero restrictions — a count that grows quadratically in $k$. In the bivariate case, a single restriction ($b_{12}=0$) suffices, as established above. The explicit solution follows from expanding $\Sigma_u = BB'$:
$$

    \left[
    \begin{array}{cc}
        \sigma _{y}^{2} & \sigma _{yr} \\
        - & \sigma _{r}^{2}%
    \end{array}%
    \right] =\underset{B}{\underbrace{\left[
            \begin{array}{cc}
                b_{11} & b_{12} \\
                b_{21} & b_{22}%
            \end{array}%
            \right] }}\underset{B'}{\underbrace{\left[
            \begin{array}{cc}
                b_{11} & b_{21} \\
                b_{12} & b_{22}%
            \end{array}%
            \right] }}
        \Rightarrow
        \left\{
        \begin{array}{l}
            \sigma _{y}^{2}=b_{11}^{2}+b_{12}^{2} \\
            \sigma _{yr}=b_{11}b_{21}+b_{12}b_{22} \\
            \sigma _{yr}=b_{11}b_{21}+b_{12}b_{22} \\
            \sigma _{r}^{2}=b_{21}^{2}+b_{22}^{2}%
        \end{array}%
        \right.
$$
The middle two equations are identical, leaving three independent equations in four unknowns. Setting $b_{12}=0$ reduces it to:
$$

    \left\{
    \begin{array}{l}
        \sigma _{y}^{2}=b_{11}^{2}, \\
        \sigma _{yr}=b_{11}b_{21}, \\
        \sigma _{r}^{2}=b_{21}^{2}+b_{22}^{2}.%
    \end{array}%
    \right.
$$
which can be solved to yield:
$$

    \left\{
    \begin{array}{l}
        b_{11}=\sigma _{y}, \\
        b_{21}=\sigma _{yr}/\sigma _{y}, \\
        b_{22}=\sqrt{\sigma _{r}^{2}-\frac{\sigma _{yr}^{2}}{\sigma _{y}^{2}}}.%
    \end{array}%
    \right.
$$
which shows that the VAR is identified. The same solution can be obtained directly via the Cholesky decomposition of $\Sigma_u$. Denote by $P$ the unique lower-triangular Cholesky factor of $\Sigma_u$, so that $\Sigma_u = PP'$. Because $P$ is unique, it follows that $B=P$ (see notebox below for details).

> **The Cholesky decomposition.**  The identification by zero short-run restrictions is often referred to as ‘Cholesky’ identification. The reason is that the solution above can be obtained with a Cholesky decomposition of the reduced-form covariance matrix. The label is nonetheless imprecise: the Cholesky factorization is a general-purpose tool that applies to any symmetric positive-definite matrix, and is used in other identification schemes as well — including identification by long-run restrictions (Section that section). What is specific to the present approach is not the factorization method but the economic assumption it encodes: that some structural shocks have no contemporaneous effect on some endogenous variables.
>
> Specifically, a symmetric and positive-definite matrix like $\Sigma_{u}$ always admits the following unique decomposition:
> $$
> \begin{equation}
> 
>     \Sigma_{u}=\left[
>     \begin{array}{cc}
>         \sigma _{y}^{2} & \sigma _{yr} \\
>         \sigma _{yr} & \sigma _{r}^{2}%
>     \end{array}%
>     \right] =\left[
>     \begin{array}{cc}
>         p_{11} & 0 \\
>         p_{21} & p_{22}%
>     \end{array}%
>     \right] \left[
>     \begin{array}{cc}
>         p_{11} & p_{21} \\
>         0 & p_{22}%
>     \end{array}%
>     \right] =PP'
> \end{equation}
> ```
> where the lower-triangular matrix $P$ is known as the Cholesky factor of $\Sigma_{u}$. Recalling that (i) $\Sigma_{u}=BB'$ and (ii) $B$ is lower triangular by assumption ($b_{12}=0$), and noting that the Cholesky factorization of a positive-definite matrix is unique, it follows that $P=B$. This is particularly useful for large VARs, since the system of equations implied by $\Sigma_u = BB'$ becomes increasingly complex as the dimensionality of the VAR increases. Instead of solving by hand the system of equations that section, the Cholesky factor of $\Sigma_u$ can be computed in MATLAB as follows:
>
> ``` text
> >> chol(VAR.sigma,'lower')
> ans= 
>     0.5377         0
>     0.1454    0.3552
> ```
>
> which equals the solution to that section, as can be verified by substitution.

**<u>In MATLAB</u>.** Zero short-run restrictions can be implemented in the VAR Toolbox with a few lines of code. The structure includes a field that allows the user to choose what identification scheme to employ. The mnemonic for the identification by short-run restrictions is the string . So, zero contemporaneous (or short-run) restrictions can be selected by executing the following line of code:

$$ matlab
VARopt.ident = 'short';
```

It is also useful (but not necessary) to update the structure with a few additional details. As discussed above, is set to zero so as to focus on point estimates only. The remaining options are useful for the output, e.g. for equation names for plotting and saving impulse responses:

``` matlab
VARopt.inference = 0;                    % Point estimates only
VARopt.mnem   = Xmnem;                   % mnemonics name the VAR.(.) sub-structs
VARopt.vnames = Xvnames;                 % variable names in plots
VARopt.nsteps = 20;                      % max horizon of IRF
VARopt.figsize = [24,6];                 % size of window (figures)
VARopt.firstdate = datesnum(1);          % first date in plots
VARopt.frequency = 'q';                  % frequency of the data
VARopt.snames = {bfeps('Demand'), bfeps('MonPol')}; % shock names
VARopt.figname = 'graphics/short';
```

Once is set, a single call to performs identification and computes impulse responses (as well as other structural objects such as variance and historical decompositions, which will be discussed in more detail in Section [sec:dynamic](06-structural-dynamic-analysis.md)):

``` matlab
VAR_short = VARmodel(X,nlags,detc,VARopt);
```

The call returns a structure that now contains, in addition to the OLS estimates from Section that section, the identified structural impact matrix and the impulse responses . The $B$ matrix can be printed at screen by executing the following command:

``` text
>> disp(VAR_short.B)
    0.5377         0
    0.1454    0.3552
```

As discussed above in Section that section, the $B$ matrix is crucial to be able to track the effects of a shock through the system. Consider a unit surprise in $\varepsilon_{t}^{MonPol}$, i.e. a surprise tightening in monetary policy, in the structural VAR in equation that section. What are the impact effects of such a shock on output growth $y_{t}$ and the short-term interest rate $r_{t}$? The answer is the second column of $B$. To see this, set $\varepsilon_t^{Demand}=0$ and $\varepsilon_t^{MonPol}=1$:
$$
    \left[
    \begin{array}{c}
        y_{t} \\
        r_{t}%
    \end{array}%
    \right] =%
    \left[
    \begin{array}{cc}
        b_{11} & 0 \\
        b_{21} & b_{22}%
    \end{array}%
    \right]
    \begin{bmatrix}
        \varepsilon_{t}^{Demand} \\
        \varepsilon_{t}^{MonPol}%
    \end{bmatrix} = 
    \small
    \left[
    \begin{array}{cc}
        \texttt{0.5377} & \texttt{0} \\
        \texttt{0.1454} & \texttt{0.3552}%
    \end{array}%
    \right]
    \begin{bmatrix}
        \texttt{0} \\
        \texttt{1}%
    \end{bmatrix}=
    \begin{bmatrix}
        \texttt{0} \\
        \texttt{0.3552}
    \end{bmatrix}\medskip
$$
The response of output is equal to $0$ — not surprisingly, as we assumed so. The response of the interest rate is instead equal to $0.3552$. These impact effects propagate according to the companion matrix $\mathcal{F}$ (which equals $\Phi$ for the VAR(1) considered here). For example, the response at horizon $h=1$ is:
$$
    \left[
    \begin{array}{c}
        y_{t+1} \\
        r_{t+1}%
    \end{array}%
    \right] =%
    \left[
    \begin{array}{cc}
        \phi_{11} & \phi_{12} \\
        \phi_{21} & \phi_{22}%
    \end{array}%
    \right]
    \begin{bmatrix}
        y_{t}\\
        r_{t}%
    \end{bmatrix} = 
    \small
    \left[
    \begin{array}{cc}
        \texttt{0.3788} & \texttt{0.0041} \\
        \texttt{0.2607} & \texttt{0.9541}%
    \end{array}%
    \right]
    \begin{bmatrix}
        \texttt{0} \\
        \texttt{0.3552}%
    \end{bmatrix}=
    \begin{bmatrix}
        \texttt{0.0015} \\
        \texttt{0.3388}
    \end{bmatrix}\medskip
$$
To see that, execute the following command:

``` text
>> disp(VAR_short.Fcomp*VAR_short.B(:,2))
    0.0015
    0.3388
```

This gives the impulse response at horizon $h=1$ (one quarter after the shock). The impulse response at any subsequent horizon can be computed analogously by repeatedly pre-multiplying by $\Phi$ (see Section [sec:dynamic](06-structural-dynamic-analysis.md) for additional details).

> **Variable ordering matters!** As explained above, zero short-run restrictions are achieved with a Cholesky decomposition of the reduced-form covariance matrix. This implies that the ordering of the variables in the matrix matters. The option implicitly assumes that the matrix is lower triangular. In turn this means that the structural shock associated with the first equation affects all variables in the system (as captured by the first column of the matrix); the structural shock associated with the second equation has zero contemporaneous effect on the first endogenous variable, but affects all subsequent variables in the system; etc. The variable ordering therefore encodes an economic assumption: the variable placed first is treated as causally prior to all others at the same point in time. The ordering should therefore be chosen to be consistent with economic theory and prior intuition.

The impulse responses are stored in , with dimension $\times$ $k$ $\times$ $k$ (here $20\times2\times2$, as was set above). Because MATLAB uses 1-based indexing, stores the response at horizon $h$: is the impact response ($h=0$), is $h=1$, and so on. The built-in function can be used to plot the impulse responses:

``` matlab
VARopt.pick = 2;
VARirplot(VAR_short.IR,VARopt);
```

Figure that section reports the point estimates of the impulse responses of the log-difference of US real GDP and the 1-year Treasury bill yield to the monetary policy shock. On impact, the monetary policy tightening has no effect on output growth — by construction, given the zero restriction $b_{12}=0$ — while the interest rate rises on impact, reflecting the tightening. In subsequent periods, output rises, contrary to standard theoretical predictions. This anomalous result reflects the extreme parsimony of the bivariate VAR(1); its purpose is illustrative rather than empirical.

> **Figure.** Impulse Responses to a Monetary Policy Shock:\
> Zero Contemporaneous Restrictions

Finally, note that a time series of structural shocks can be recovered from $\varepsilon_t = B^{-1}u_t$. Since $B$ is lower-triangular with positive diagonal entries (a consequence of the Cholesky factorization with the sign normalization), it is invertible. In MATLAB, the structural shocks can be computed by executing a single line of code:

``` matlab
eps_short = (VAR_short.B\VAR_short.resid')';
```

where is the $T \times 2$ matrix of structural shocks. The structural shocks can be verified to be orthogonal by typing in the command window:

``` text
>> disp(corr(eps_short))
    1.0000    0.0000
    0.0000    1.0000
```

which implies that the covariance matrix of the structural shocks is diagonal.

## Zero Long-Run Restrictions

Zero long-run restrictions, proposed by , achieve identification by the same logic as zero contemporaneous restrictions — but impose the zeros on the long-run cumulative effects of structural shocks rather than on their contemporaneous effects.

A well-known implication of many macroeconomic models is that supply shocks have a permanent effect on the level of output. Monetary policy shocks, by contrast, are assumed to have no long-run effect on output — a property known as long-run monetary neutrality, which provides the identifying restriction imposed below. Under this assumption, one could impose that monetary policy shocks have no cumulative long-run effect on the level of output.

But how does one map the $B$ matrix, which captures the contemporaneous effects of structural shocks on the endogenous variables in the VAR, to the long-run effects of structural shocks? To give intuition in the context of the simple bivariate VAR described in the previous section, assume that the two shocks driving the model economy are a supply shock ($\varepsilon_t^{Supply}$) and a monetary policy shock ($\varepsilon_t^{MonPol}$):
$$
    \left[
    \begin{array}{c}
        y_{t} \\
        r_{t}%
    \end{array}%
    \right] =%
    \begin{bmatrix}
        c_{y} \\
        c_{r} %
    \end{bmatrix}
    +
    \begin{bmatrix}
        \phi _{11} & \phi _{12} \\
        \phi _{21} & \phi _{22}%
    \end{bmatrix}%
    \left[
    \begin{array}{c}
        y_{t-1} \\
        r_{t-1}%
    \end{array}%
    \right] +\left[
    \begin{array}{cc}
        b_{11} & b_{12} \\
        b_{21} & b_{22}%
    \end{array}%
    \right]
    \begin{bmatrix}
        \varepsilon_{t}^{Supply} \\
        \varepsilon_{t}^{MonPol}%
    \end{bmatrix}%
    ,  
$$
The effect of these structural shocks on the endogenous variables at horizon $h \geq 0$ (where $h=0$ is the period when the shock hits) can be traced by iterating the structural VAR forward. Setting all shocks after period $t$ to zero ($\varepsilon_{t+h}=0$ for all $h\geq 1$) and tracing the propagation of a single shock $\varepsilon_t$:
$$
    \begin{array}{l}
        x_{t}=B\varepsilon_{t}, \\
        x_{t+1}=\Phi B\varepsilon_{t}, \\
        ... \\
        x_{t+\infty }=\Phi ^{\infty }B\varepsilon_{t}.%
    \end{array}
    
$$
The long-run (i.e. for $h$ that goes to infinity) cumulative effect of the shock can be obtained by summing all the terms in that section:
$$
    x_{t,t+\infty }=B\varepsilon_{t}+\Phi B\varepsilon_{t}+\Phi
    ^{2}B\varepsilon_{t}+...+\Phi ^{\infty }B\varepsilon
    _{t}=\sum\limits_{j=0}^{\infty }\Phi ^{j}B\varepsilon_{t},  
$$
where $x_{t,t+\infty}$ denotes the cumulative sum of the impulse response vectors in that section from horizon $h=0$ to $\infty$. Finally, note that if the VAR is stable (i.e. if all eigenvalues of $\Phi$ lie strictly inside the unit circle; for the VAR(1) considered here, $\Phi = \mathcal{F}$, the companion matrix), the infinite sum in equation (that section) converges to:
$$
    x_{t,t+\infty }=\left( I-\Phi \right) ^{-1}B\varepsilon_{t}=C\varepsilon
    _{t},  
$$
where
$$

    C\equiv \left( I-\Phi \right) ^{-1}B
$$
is a $2 \times 2$ matrix which captures the cumulative effect of shocks $\varepsilon_{t}$ on $x_{t}$ from time $t$ to $t+\infty$.

The idea behind identification through zero long-run restrictions is to impose a zero restriction on the long-run impact matrix $C$. For example, one could maintain the assumption that monetary policy shocks have no long-run effect on the level of output. This restriction is well-defined only when the log-level of output is integrated of order one, so that the level of output has a well-defined long-run response; in the present example, $y_t$ is the log-difference of GDP, and its cumulative sum measures the log-level change. Equation (that section) allows one to impose this restriction exactly by setting $c_{12}=0$:
$$

    \left[
    \begin{array}{c}
        y_{t,t+\infty } \\
        r_{t,t+\infty }%
    \end{array}%
    \right] =\left[
    \begin{array}{cc}
        c_{11} & 0 \\
        c_{21} & c_{22}%
    \end{array}%
    \right]
    \begin{bmatrix}
        \varepsilon_{t}^{Supply} \\
        \varepsilon_{t}^{MonPol}%
    \end{bmatrix}.
$$
The upper right element of $C$ captures the long-run cumulative effect of $\varepsilon_{t}^{MonPol}$ on the log-difference of GDP. Because the log-difference is the period-on-period growth rate, the cumulative sum of log-difference responses equals the total change in the log-level; setting this sum to zero therefore imposes long-run neutrality on the level.

How does this pin down $B$? Define $\Omega \equiv CC'$. Because $\Phi$ and $\Sigma_u$ are estimated from the reduced-form VAR, $\Omega$ can be computed directly from the data, provided the VAR is stable (see Section that section) so that $(I-\Phi)$ is non-singular. Note that:
$$

    \Omega \equiv CC' = \left( \left( I-\Phi \right)^{-1}\right) \Sigma_{u}\left( \left( I-\Phi \right) ^{-1}\right)',
$$
where we used the fact that $BB'=\Sigma_u$. Equation that section therefore maps the known $2 \times 2$ matrix $\Omega$ to the unobserved $C$ matrix — and thus the $B$ matrix through equation that section — and thereby identifies $B$.

The matrix $\Omega$, however, is a positive-definite symmetric matrix, which implies that it provides only three independent restrictions for four unknowns:
$$

    \left[
    \begin{array}{cc}
        \omega_{y}^2 & \omega_{yr} \\
        \omega_{yr} & \omega_{r}^2%
    \end{array}%
    \right]
    =
    \left[
    \begin{array}{cc}
        c_{11}^2 + c_{12}^2 & c_{11}c_{21} + c_{12}c_{22}\\
        c_{11}c_{21}+ c_{12}c_{22} & c_{21}^2 + c_{22}^2%
    \end{array}%
    \right]
$$
In a similar way to the identification by short-run restrictions, assuming $c_{12}=0$ (i.e. that the long-run *cumulative* effect of $\varepsilon_{t}^{MonPol}$ on the log-difference of US real GDP is zero) allows one to solve the system of equations implied by that section. In fact, we have now three independent equations and three unknowns, and it is straightforward to compute the solution analytically. Finally, once $C$ is known, it is possible to recover the structural impact matrix $B$ by rearranging that section: $B = (I-\Phi)C$. Under stability, $(I-\Phi)$ is non-singular, so $B$ is uniquely determined once $C$ is known.

> **The Cholesky decomposition, again.**  The same Cholesky logic as in Section that section applies here, with $\Omega$ in place of $\Sigma_u$ and $P_\Omega$ in place of $P$. The identification by zero long-run restrictions solves the identification problem by setting to zero some of the non-diagonal elements of the structural long-run matrix $C=(I-\Phi)^{-1}B$, thus reducing the number of unknown coefficients in the $C$ matrix to the same number of equations implied by the condition $\Omega = CC'$.
>
> As shown above, in a simple bivariate VAR a single zero restriction is enough to achieve identification, and the solution is straightforward to compute by hand (3 equations and 3 unknowns). But the number of zeros that need to be imposed to achieve identification depends on the number of variables in the VAR — and, as for zero short-run restrictions, it increases at a faster rate than the number of endogenous variables.
>
> As before, the Cholesky decomposition turns out to be useful, especially as the dimensionality of the VAR increases. Define $\Omega \equiv \left( \left( I-\Phi \right)^{-1}\right) \Sigma_{u}\left( \left( I-\Phi \right) ^{-1}\right)'$ and note that $\Omega$ is a known $2 \times 2$ positive-definite symmetric matrix. Thus, $\Omega$ admits a unique Cholesky decomposition, given by:
> $$
> \begin{equation}
>  
>     \Omega =P_\Omega P_\Omega',
> \end{equation}
> ```
> where the lower-triangular matrix $P_\Omega$ is the Cholesky factor of $\Omega$. Note that $\Omega \neq \Sigma_u$: the notation $P_\Omega$ is used here to distinguish from the Cholesky factor $P$ of $\Sigma_u$ introduced in Section that section. Since the Cholesky factorization of a positive-definite matrix is unique, and $C$ is lower triangular with $CC' = \Omega$ (because we imposed $c_{12}=0$), it follows by the uniqueness of the Cholesky factorization that $C = P_\Omega$. Once $C$ is known, we can recover $B = (I-\Phi)C$ from that section.
>
> As for zero short-run restrictions, the ordering of variables in matters. The shock associated with the variable ordered second is restricted to have no permanent effect on the variable ordered first (here, output). Equivalently, the variable ordered first is associated with the shock that is allowed to have a permanent effect on all variables.

**<u>In MATLAB</u>.** The implementation follows the same pattern as in Section that section; the mnemonic for long-run restrictions is the string :

$$ matlab
VARopt.ident = 'long';
```

As before, it is also useful (but not necessary) to update the structure with a few additional details that will be used when plotting the impulse responses, saving them, etc. Only the shock labels need updating; all other settings carry over from the previous example unchanged:

``` matlab
VARopt.snames = {bfeps('Supply'), bfeps('MonPol')}; % shock names;
VARopt.figname = 'graphics/long';
```

As for zero short-run restrictions, identification and impulse response computation are performed with a single call to :

``` matlab
VAR_long = VARmodel(X,nlags,detc,VARopt);
```

The call returns a new structure — separate from , so that results from different identification schemes can be compared side by side. It contains the identified (consistent with $c_{12}=0$) and . The $B$ matrix can be printed at screen as follows:

``` text
>> disp(VAR_long.B)
    0.5368   -0.0309
    0.1655    0.3462
```

Note that the $B$ matrix, which was left unrestricted, is not lower triangular anymore (as in the case of zero short-run restrictions), but has non-zero entries in both columns. The first column gives the impact responses to the supply shock and the second column gives the impact responses to the monetary policy shock.

Impulse responses are plotted with . By default, plots the responses to all $k$ identified shocks; setting to an integer restricts the output to the shock with that column index in $B$. Here selects the monetary policy shock: as shown by the algebra above, imposing $c_{12}=0$ constrains the cumulative long-run effect of the *second* structural shock on output to zero, thereby identifying that shock as $\varepsilon_{t}^{MonPol}$. The option is useful whenever only a subset of the identified shocks is of interest and the remaining columns of $B$ need not be plotted:

``` matlab
VARopt.pick = 2;
VARirplot(VAR_long.IR,VARopt);
```

Figure that section reports the point estimates of the impulse responses of the log-difference of US real GDP and the 1-year Treasury bill yield to the monetary policy shock identified with zero long-run restrictions. Unlike zero contemporaneous restrictions, zero long-run restrictions leave the impact matrix $B$ unconstrained: no zero is imposed on any element of $B$, so the signs and magnitudes of the on-impact responses are determined entirely by the data. Figure that section bears this out: on impact the shock raises the policy rate and lowers output growth, even though neither response was constrained by the identification assumptions.

> **Figure.** Impulse Responses to a Monetary Policy Shock:\
> Zero Long-Run Restrictions

To check that the structural VAR estimated with the above commands is consistent with the assumptions made, note that the $C$ matrix — the matrix that captures the cumulative long-run effect of shocks on the endogenous variables — should be lower triangular under the assumptions made above, so that the cumulative effect of $\varepsilon_{t}^{MonPol}$ on the log-difference of US real GDP is zero (long-run monetary neutrality). One way to perform this check is visual: plot the cumulative impulse response of the log-difference of US real GDP, $y_t$, to the monetary policy shock over a long enough horizon, and verify that it converges to zero (the cumulative responses are obtained by summing them along the horizon).

Figure that section plots the cumulative impulse responses of output growth and the interest rate to the monetary policy shock over a horizon of $150$ quarters. At horizon zero the cumulative responses coincide with the impact responses of Figure that section, by construction, since the cumulative sum at the first step is just the impact response itself. As the per-period responses accumulate over longer horizons, the cumulative effect of the shock on the *level* of US real GDP returns to zero (left panel). The reason is that $y_t$ is the log-difference of GDP, so the cumulative sum of its responses measures the total change in the log-level; its convergence to zero is exactly the long-run monetary neutrality imposed by the identifying restriction. The cumulative response of the interest rate is left unrestricted and, in this case, does not converge to zero (right panel).

> **Figure.** Cumulative Responses to a Monetary Policy Shock:\
> Zero Long-Run Restrictions

The check can also be performed algebraically: recalling from equation that section that $C\equiv \left( I-\Phi \right) ^{-1}B$, the $C$ matrix can be printed at screen with the following command:

``` text
>> disp((eye(2)-VAR_long.Fcomp)\VAR_long.B)
    0.9224    0.0000
    8.8389    7.5367
```

As assumed, the $c_{12}$ element is equal to zero.

## Sign Restrictions

Zero restrictions can be motivated by economic theory, but theory rarely implies them directly. Even when a theoretical motivation exists, the implied zeros may be hard to defend on substantive grounds. Identification by sign restrictions provides an alternative approach that exploits prior beliefs about the sign that certain shocks should have on certain endogenous variables — a weaker requirement than imposing exact zeros.

The idea is to impose restrictions on specified orthogonalized impulse response functions. Unlike the identification schemes described above — where the identifying restrictions select a unique $B$ matrix (i.e. a unique rotation $Q$ from the orbit $\{B_0Q : QQ'=I_k\}$; see Box that section) — sign-restricted VARs are set-identified: the restrictions narrow the parameter space but do not select a unique structural model. The data are potentially consistent with a wide range of $B$ matrices that are all admissible in that they satisfy the sign restrictions — see , , and .

To fix ideas, consider the sign restrictions needed to separately identify demand and a monetary policy shock, as summarized in Table that section:

<div class="minipage">

<div class="center">

<div class="tabularx">

lYY & &\
& ($\varepsilon_{t}^{Demand}$) & ($\varepsilon_{t}^{MonPol}$)\
Output growth ($y_{t}$) & + & -\
Short-term Interest Rate ($r_{t}$) & + & +\

</div>

</div>

<span class="smallcaps">Note.</span> The signs represent restrictions on the elements of the structural impact matrix $B$. ‘$+$’ and ‘$-$’ indicate a positive and negative contemporaneous response, respectively. A demand shock raises both output growth and the short-term interest rate, as monetary policy tightens to contain the expansion. A contractionary monetary policy shock lowers output growth and raises the interest rate, consistent with an unexpected tightening of monetary policy. <span id="tab:SR" label="tab:SR"></span>

</div>

A demand shock ($\varepsilon_{t}^{Demand}$) should lead to an increase in output growth ($y_{t}$) and to an increase in the short-term interest rate ($r_{t}$). The latter sign reflects the assumption that monetary policy responds endogenously to the expansion, as in a standard Taylor-rule framework. By contrast, a contractionary monetary policy shock ($\varepsilon_{t}^{MonPol}$) should lead to a decrease in output growth and an increase in the short-term interest rate, consistent with an unexpected tightening of monetary policy.

But how can such restrictions be imposed? The implementation of sign-restriction identification proceeds in three steps.

1.  <u>*Draw an orthogonal matrix ($Q$)*</u>.  An orthogonal matrix $Q$ is a real square matrix whose columns form an orthonormal set: each column has unit norm and any two distinct columns are mutually orthogonal.[^1] Take, for example, two $2\times 1$ vectors $q_{1}$ and $q_{2}$, then the matrix $Q=(q_{1},q_{2})$ is orthogonal if (i) the vectors have unit norm ($\parallel q_{i}\parallel =1$), and (ii) the vectors are mutually orthogonal ($q_{1}^{T}q_{2}=0$). It follows that
    $$
            QQ'=I_2 \ \ \ \text{and} \ \ \ Q'=Q^{-1}
    \end{equation*}
    ```
    Such matrices can be generated by computing the QR factorization of a random matrix with i.i.d. standard normal entries — see the function and the examples therein.

2.  <u>*Compute a candidate structural impact matrix ($B_j$)*</u>.  Consider the structural impact matrix $B$ corresponding to the Cholesky factor of the reduced-form covariance matrix $\Sigma_{u}$ of our simple bivariate VAR, namely:
    ``` math
    \begin{equation*}
            \Sigma_{u}=PP'.
    \end{equation*}
    ```
    We know from Section that section that $B=P$ is the unique lower-triangular structural impact matrix with positive diagonal entries consistent with $\Sigma_u = BB'$; it obtains under the zero contemporaneous restriction $b_{12}=0$. Now note that the following equality holds
    ``` math
    \begin{equation}
    
            \Sigma_{u}=PP'=PQ_jQ_j'P'=\underset{B_j}{\underbrace{\left( PQ_j\right) }}\underset{B_j'}{\underbrace{\left( PQ_j\right)'}}
    \end{equation}
    ```
    where $Q_j$ denotes a randomly drawn orthonormal matrix such that $Q_jQ_j'=I_2$. The defining property of $B_j$ is that, in addition to satisfying that section, it is such that the associated structural shocks $\varepsilon_{jt} = B_j^{-1} u_t$ are orthogonal and have unit variance: $E[\varepsilon_{jt}\varepsilon_{jt}'] = I_2$. To verify: $B_j^{-1}\Sigma_u (B_j^{-1})' = B_j^{-1} B_j B_j'(B_j')^{-1} = I_2$. It follows that $B_j$ is a valid candidate structural impact matrix that solves the identification problem. Invertibility of $B_j$ follows because $P$ (a Cholesky factor) and $Q_j$ (an orthogonal matrix) are both invertible, and the product of invertible matrices is invertible. Also note that $B_j$ is not triangular any more. Sign restrictions narrow the set of admissible $B_j$ matrices but generically leave infinitely many. Since the reduced form identifies only $\Sigma_u = BB'$ and not $B$ itself, the data alone cannot resolve this multiplicity. The sign-restriction approach embraces this multiplicity: any $B_j$ consistent with the restrictions is treated as an admissible structural model — the identified set is the collection of all such $B_j$.

3.  <u>*Check the sign restrictions*</u>.  Sign restrictions identify the VAR by requiring the impulse responses to satisfy specified sign conditions; any $B_j$ consistent with those conditions is treated as a valid structural model. Computationally, a large number of candidate matrices $B_j$ are drawn and those satisfying the sign conditions are retained — where recall that the $B_j$ matrix contains the impact response of all endogenous variables to all structural shocks. For example, for a given $Q_j$ matrix and associated structural impact matrix $B_j$, the structural representation of our VAR can be written as:
    ``` math
    \begin{equation}
            \left[
            \begin{array}{c}
                y_{t} \\
                r_{t}%
            \end{array}%
            \right] =%
            \begin{bmatrix}
                \phi _{11} & \phi _{12} \\
                \phi _{21} & \phi _{22}%
            \end{bmatrix}%
            \left[
            \begin{array}{c}
                y_{t-1} \\
                r_{t-1}%
            \end{array}%
            \right] +\left[
            \begin{array}{cc}
                b_{j,11} & b_{j,12} \\
                b_{j,21} & b_{j,22}%
            \end{array}%
            \right]
            \begin{bmatrix}
                \varepsilon_{t}^{Demand} \\
                \varepsilon_{t}^{MonPol}%
            \end{bmatrix}%
            ,  
    \end{equation}
    ```
    where the matrix $B_j = PQ_j$ is now known. We can then check whether the impact response of the two structural shocks to output growth and the short-term interest rate satisfies the sign restrictions. That is:

    <div class="center">

    |  |  |  |
    |:---|:--:|:--:|
    |  | Demand Shock | Monetary Policy Shock |
    |  | ($\varepsilon_{t}^{Demand}$) | ($\varepsilon_{t}^{MonPol}$) |
    | Output growth ($y_{t}$) | $b_{j,11}>0$? | $b_{j,12}<0$? |
    | Short-term Interest Rate ($r_{t}$) | $b_{j,21}>0$? | $b_{j,22}>0$? |

    </div>

If all the elements of $B_j$ satisfy the sign restrictions, we retain the draw and store $PQ_j$; otherwise we discard it and draw a new $Q_j$. After collecting a large number of accepted draws, we have a distribution of $B_j$ matrices — and of the implied impulse responses, variance decompositions, etc. — that summarizes the identified set.

> **Set identification vs. point identification.**  The identification schemes in Sections that section and that section are *point-identified*: given the data, a unique $B$ matrix satisfies the identifying restrictions. The Cholesky decomposition delivers exactly one lower-triangular $B$ consistent with $\Sigma_u = BB'$, provided the diagonal entries are required to be positive (a sign normalization that removes the remaining sign ambiguity); the Blanchard-Quah decomposition delivers exactly one $B$ consistent with a lower-triangular long-run matrix $C$. The only source of uncertainty in the resulting impulse responses is therefore sampling variability.
>
> Sign restrictions, by contrast, are *set-identified*: many $B_j$ matrices are simultaneously consistent with the sign restrictions and with the data. Even with an infinite sample, the data alone cannot select among them — they represent genuinely different structural models, each with its own economic interpretation. This has two important implications. First, summary measures such as the median impulse response across accepted draws need not converge to a unique value as $T\to\infty$, because the identified set remains non-singleton even in the population — the median describes the location of the identified set, not a point estimate of a unique structural parameter. Second, the width of the credible intervals in sign-restricted VARs reflects both sampling uncertainty *and* the width of the identified set; these two sources of uncertainty cannot be disentangled without imposing additional restrictions — see and for formal treatments.
>
> The VAR Toolbox handles parameter uncertainty for sign-restricted VARs through a Bayesian approach: reduced-form parameters are drawn from their posterior distribution, and for each draw the sign-restriction algorithm is applied to find admissible rotations. This is described in Section [sec:inference](05-statistical-inference.md).

**<u>In MATLAB</u>.** Sign restrictions in the VAR Toolbox can be implemented with a few lines of code. The restrictions are specified in a $k \times k$ matrix (here $2 \times 2$). Consistent with the notation in equation that section, each column collects restrictions for a given structural shock and each row collects restrictions for a given endogenous variable. Entry values are $1$ (positive response required), $-1$ (negative response required), or $0$ (unrestricted). The restrictions described in Table that section can be implemented in MATLAB with the following line of code:

$$ matlab
R = [ 1, -1;  % Real GDP
      1,  1]; % 1-year rate
```

The matrix specifies the sign restrictions as in Table that section.

It is also useful, though not necessary, to update some fields in the structure. Two fields are specific to sign restrictions: specifies the number of accepted draws the routine needs to find, and specifies the number of periods for which the sign restrictions in are required to hold. In this specific example, we set the restrictions to hold for one quarter only (namely, on impact), but they can be specified to hold for longer horizons. The remaining fields, as for other identification schemes, control how the impulse responses are plotted, saved, etc. As most settings have been set for the previous example, it will suffice to run the following lines of code:

``` matlab
VARopt.ndraws = 1000;     % number of desired accepted draws
VARopt.sr_hor = 1;        % horizon over which restrictions hold
VARopt.nsteps = 20;       % horizon of impulse responses
VARopt.figsize = [24, 6]; % size of window (figures)
VARopt.snames = {bfeps('Demand'), bfeps('MonPol')}; % shock names
```

To implement the approach, as for other identification schemes, set the structure . Then store the restriction matrix in , and call :

``` matlab
VARopt.ident = 'sign';
VARopt.R = R;
VAR_sr = VARmodel(X,nlags,detc,VARopt);
```

The structure contains all relevant output. Of particular interest for the discussion in this section are two matrices. The matrix includes all the accepted draws of $B_j$, and thus has a dimension of $2 \times 2 \times 1000$. Each of the accepted $B_j$, which by definition satisfies the sign restrictions in Table that section, is associated with an impulse response function, stored in the matrix .

Figure that section reports all such responses of the log-difference of US real GDP and the 1-year rate to the monetary policy shock. As the figure makes clear, every accepted draw satisfies the sign restrictions on impact — GDP falls and the 1-year rate rises — but the magnitude of the impact responses and the subsequent transmission of the shock differ across draws, reflecting the set-identified nature of the model.

> **Figure.** Impulse Responses to a Monetary Policy Shock:\
> All Accepted Draws

While all accepted draws satisfy the identifying restrictions, it is common to report a summary measure of the identified set. The VAR Toolbox provides two distinct objects for this purpose — the element-wise median and the Fry-Pagan median-target rotation — and it is important to understand what each represents.

The first object, , is the *element-wise median* across all : each entry — that is, the response of variable $i$ to shock $j$ at horizon $h$ — is the median of the corresponding entry across all $J$ accepted draws. While is a convenient summary of the central tendency of the identified set, the associated impact matrix is in general a ‘*Frankenstein*’ object: it corresponds to no accepted draw and will in general not satisfy $\Sigma_u = B_{\text{med}}B'_{\text{med}}$, so it does not represent any valid structural model. The second object, due to , addresses this by selecting, among the accepted draws, the single genuine rotation whose responses are closest to the element-wise median. Box that section defines this *median-target* rotation and its relationship to the element-wise median.

Figure that section plots the two summaries together for the monetary policy shock — the element-wise median and the median-target draw . In this bivariate example the two are visually indistinguishable, but they are not identical, and they need not be: as Box that section explains, the element-wise median and the median-target rotation differ in general even when the reduced-form parameters are held fixed, and the gap grows with the dimension of the VAR and the width of the identified set.

> **Figure.** Impulse Responses to a Monetary Policy Shock:\
> Element-Wise Median and Median-Target Rotation

> \[label=box:fp\] **The Fry-Pagan median-target rotation.**   pointed out that the element-wise median , though a convenient summary of the identified set, does not correspond to any single structural model: the associated impact matrix matches no accepted draw and will in general not satisfy $\Sigma_u = B_{\mathrm{med}}B_{\mathrm{med}}'$. They proposed instead selecting the single accepted draw $B_{j^*}$ whose implied impulse responses are closest to the element-wise median in a least-squares sense:
> $$
> \begin{equation*}
>     j^* = \arg\min_{j} \sum_{h,i,k} \bigl[\mathrm{IR}_{j,hik} - \mathrm{IRmed}_{hik}\bigr]^2.
> \end{equation*}
> ```
> This *median-target* rotation is a genuine structural representation of the VAR: it satisfies all sign restrictions and $\Sigma_u = B_{j^*} B_{j^*}'$ by construction. The VAR Toolbox stores it in and , with companion fields and for variance decompositions (Section that section) and historical decompositions (Section that section). The plotting functions (as well as and , which will be discussed in Section [sec:dynamic](06-structural-dynamic-analysis.md)) take whichever field the user explicitly supplies, so the choice between the element-wise median and the Fry-Pagan draw rests with the user. The two options entail different trade-offs. The element-wise median (, , ) summarizes the central tendency of the identified set and is easy to compute, but the associated does not correspond to any accepted draw, VD shares need not sum to one at every horizon, and HD contributions need not exactly reproduce the observed series — all three being artefacts of element-wise aggregation across draws. The Fry-Pagan draw (, , ) is a genuine structural representation: VD shares sum to one and HD contributions reproduce the data exactly, but it selects a single draw from the identified set, which introduces a different form of arbitrariness.
>
> The element-wise median and the median-target rotation differ in general, and the distinction does not depend on whether parameter uncertainty is accounted for. The reason is geometric. The admissible impact matrices satisfy $\Sigma_u = B_j B_j'$, so they lie on a curved set — the orthonormal rotations of a fixed Cholesky factor of $\Sigma_u$. The element-wise median is taken coordinate by coordinate across draws and is, in general, not a point of this set; this is precisely why need not satisfy $\Sigma_u = B_{\mathrm{med}}B_{\mathrm{med}}'$. The median-target rotation returns the single admissible draw whose responses are closest to the element-wise median, which differs from the median itself whenever the median lies off the set. This holds even when : in that case all draws share the OLS estimates $(\hat\Phi,\hat\Sigma_u)$ and vary only through the rotation $B_j$, yet the impulse responses still trace a non-linear set as the rotation varies, so their coordinate-wise median need not be attainable by any single rotation. Accounting for parameter uncertainty () lets $\Phi_h$ vary across draws as well, adding a second source of dispersion, but it is not what creates the gap. The magnitude of the gap depends on the geometry of the identified set: it is small when the set is tight and low-dimensional — as in the bivariate example of Figure that section, where the two summaries are visually indistinguishable — and grows with the dimension of the VAR and the width of the identified set. Note that the running example of this section sets (Section [sec:inference](05-statistical-inference.md)), so the comparison in Figure that section isolates identification (rotation) uncertainty; the difference between the two summaries is therefore not an artefact of parameter uncertainty.

## Narrative Sign Restrictions

Sign restrictions, as described in Section that section, restrict the *sign* of the impulse responses over some horizon. A large set of rotation matrices $Q_j$ can satisfy the sign restrictions, producing a correspondingly wide set of admissible structural impact matrices $B_j$ and, consequently, wide credible sets for impulse responses. propose to sharpen identification by incorporating *narrative restrictions* — additional constraints tied to specific, well-documented historical events. The insight is that historical records (monetary policy announcements, oil supply disruptions, fiscal interventions) carry information about the sign or relative magnitude of a structural shock at a particular date. Restricting the model to be consistent with that information reduces the set of admissible rotations and, in practice, substantially tightens inference.

To fix ideas, suppose that in a particular quarter there was an unambiguous monetary policy tightening. This historical knowledge carries two pieces of information. First, the monetary policy shock must have been positive in that quarter — the direction of the move is known from the historical record. Second, if historical records further suggest that no major competing shock was operating simultaneously, then monetary policy was plausibly the dominant driver of the policy rate in that quarter. These two pieces of information motivate the two types of narrative restriction defined by . Let $\varepsilon_{jt} = B_j^{-1}u_t$ denote the vector of structural shocks under candidate $B_j$, where $j$ indexes a particular draw.

- <u>*Sign restriction (type 1).*</u> At date $t^*$, the $m$-th structural shock $\varepsilon_{j,m,t^*}$ must have a specified sign:
  ``` math
  \begin{equation}
      s \cdot \varepsilon_{j,m,t^*} > 0, \qquad s \in \{+1, -1\}.
      
  \end{equation}
  ```
  In the example above, this encodes the knowledge that the monetary policy shock was positive ($s=+1$) in the quarter of the unambiguous tightening.

- <u>*Dominance restriction (type 2).*</u> At date $t^*$, the contribution of shock $m$ to the unexpected movement in variable $i$ must exceed the combined contribution of all other shocks:
  ``` math
  \begin{equation}
      \bigl|b_{j,im}\,\varepsilon_{j,m,t^*}\bigr| > \sum_{k \neq m} \bigl|b_{j,ik}\,\varepsilon_{j,k,t^*}\bigr|,
      
  \end{equation}
  ```
  where $b_{j,im}$ is the $(i,m)$ element of $B_j$. In the example above, this encodes the knowledge that monetary policy was the dominant driver of the policy rate in that quarter.

Both restrictions are applied as additional acceptance criteria *after* a rotation satisfying the sign constraints has been found. A draw $j$ that passes the sign restrictions but fails any narrative restriction is discarded. Because narrative restrictions are layered on top of the sign constraints, the number of accepted draws can only decrease or remain unchanged relative to the sign-only baseline. A substantial decrease indicates that the historical episodes are genuinely informative and narrow the identified set; little or no decrease indicates that the narrative restrictions add little beyond what the sign constraints already impose.[^2]

**<u>In MATLAB</u>.** Narrative sign restrictions are implemented via the same call used for standard sign restrictions. The second argument accepts either a plain sign-restriction matrix — in which case behaves identically to its non-narrative version — or a struct that combines sign and narrative restrictions. When is a struct, it has to contain three fields:

- : the sign-restriction matrix, in the same format as the matrix of Section that section.

- : encodes Type 1 restrictions (sign of the shock at a specific date). It is a struct with three row vectors. is the index for the column of $B$ identifying the structural shock to restrict. identifies the quarter in which the shock to be restricted occurred, indexed against the input data passed to . It accepts either a date string (e.g. , which requires to be set) or the integer row of that quarter in the input data; the two forms are equivalent and point to the same observation. The toolbox handles the internal alignment with the residual sample, so a quarter falling inside the first $p$ rows — absorbed as initial lags and hence without an associated shock — is rejected with an error. specifies the required direction of the shock: $+1$ for a positive realization, $-1$ for a negative one. Multiple Type 1 restrictions are stacked as additional rows in each vector.

- : encodes Type 2 restrictions (dominance of the shock at a specific date). It is a struct with three row vectors: and follow the same conventions as in . The third row vector is the index of the variable that the shock must dominate — the shock’s contribution to the reduced-form residual of that variable must exceed the combined contribution of all other shocks. Multiple Type 2 restrictions are stacked as additional rows.

Both and are optional; omit either field to skip that class of restrictions. The code below illustrates the implementation for the bivariate monetary VAR of Section that section, using two historical episodes chosen to illustrate both the power and the limits of narrative identification at quarterly frequency.

- <u>*1994:Q1 — sign and dominance.*</u> Greenspan’s February 4 hike was an unambiguous surprise tightening in a quarter with no major competing macroeconomic disturbance. Historical records leave little doubt that the monetary policy shock was positive that quarter, motivating a Type 1 restriction. Since no major non-monetary shock was operating simultaneously, monetary policy was plausibly the dominant driver of the variation in the 1-year yield, motivating a Type 2 restriction as well.

- <u>*2001:Q1 — sign only.*</u> The January 3 unscheduled inter-meeting cut was an unambiguous easing surprise — historical records clearly place the monetary policy shock in negative territory, motivating a Type 1 restriction. A Type 2 restriction is not warranted, however. The quarter also contains a large concurrent non-monetary disturbance: the dot-com bust and the peak of the business cycle in March, as dated by the NBER.

These restrictions can be implemented in MATLAB as follows:

$$ matlab
R.sign = [ 1, -1;  % Real GDP
           1,  1]; % 1-year rate

% Sign of MP shock for both episodes
R.narr_sign.shock  = [2;        2      ];
R.narr_sign.period = {'1994q1'; '2001q1'};
R.narr_sign.sign   = [1;       -1      ];

% MP shock is the dominant driver of i1yr only in 1994q1
R.narr_dom.shock  = [2;        ];
R.narr_dom.period = {'1994q1'; };
R.narr_dom.var    = [2;        ];
```

With the struct in place, it must be assigned to the structure, together with a few additional options.

``` matlab
VARopt.R       = R;      % assign R to VARopt
VARopt.dates   = dates;  % date strings aligned with VAR input data
VARopt.sr_draw = 500000; % total number of draws to attempt
VARopt.figsize = [24, 6];
VARopt.snames  = {bfeps('Demand'), bfeps('MonPol')};
```

The two key fields are , which assigns the restriction struct, and , which supplies the date strings that align with the VAR input data. Note that (set earlier to 1000) specifies the number of *accepted* draws to collect, while specifies the total number of *candidate* draws to attempt. Because narrative restrictions are more stringent, a larger candidate pool is needed.[^3] The ratio of accepted to total draws also signals how informative the narrative restrictions are: a low ratio indicates that the restrictions substantially constrain the identified set.

With the options set, the narrative-restriction identification is run as usual through the call:

``` matlab
VAR_nsr = VARmodel(X, nlags, detc, VARopt);
```

where recall that the field had been already set in the sign restrictions example. The output has the same structure as from Section that section. Adding narrative restrictions tightens identification at the cost of a lower acceptance rate: in this example, the acceptance rate falls from 73.9% under sign restrictions alone to 31.9% under sign plus narrative restrictions, as the additional constraints screen out a substantial share of sign-consistent rotations. The acceptance rates are stored in and , respectively.

Figure that section compares impulse responses to a monetary policy shock under sign restrictions alone (blue) and under sign plus narrative restrictions (red). Shaded areas show the set spanned by all accepted draws; solid lines show the element-wise median across draws. Two effects are visible. First, the narrative restrictions shrink the identified set: the red shaded area is noticeably narrower than the blue one. Second, the median responses shift — narrative information changes the central estimate, not only its precision. The additional restrictions screen out rotations that are sign-consistent but historically at odds with the narrative evidence, leaving a smaller and differently centred set of admissible impulse responses.

> **Figure.** Impulse Response to a Monetary Policy Shock:\
> Sign Only vs. Narrative Sign Restrictions

Figure that section shows the distribution of the identified monetary policy shock at each narrative date, across all accepted draws under sign restrictions alone (blue) and under sign plus narrative restrictions (red). Each panel corresponds to one narrative event, and the shift from blue to red reveals which restriction is binding and how it alters the set of admissible draws. In 1994:Q1, the sign-only distribution is already entirely in positive territory: the sign restrictions alone were sufficient to pin down the direction of the shock in that quarter, so the Type 1 narrative restriction (which requires a positive shock) does not eliminate any additional draws and is not the binding constraint. What does bite is the dominance restriction, which requires the monetary policy shock to be the largest contributor to the policy rate in that quarter. This additional requirement screens out draws that, while sign-consistent, attribute a larger share of the policy-rate move to the demand shock; the result is that the red distribution is shifted toward larger positive values relative to the blue.

> **Figure.** Distribution of the Monetary Policy Shock:\
> Sign Only vs. Narrative Sign Restrictions

In 2001:Q1, the sign-only distribution is predominantly negative — consistent with the historical narrative of a policy easing — but retains a non-negligible right tail of positive realizations. These are draws for which the sign restrictions happened to be satisfied yet the shock took the wrong sign in that quarter. The Type 1 narrative restriction, which requires a negative monetary policy shock at 2001:Q1, removes exactly this tail: the red distribution is entirely negative, and its support is tighter than the blue.

## External Instruments (or Proxies)

External instruments identification was introduced by and . It is also known in the literature as the *proxy SVAR*, a term that reflects the role of the instrument as a proxy for the unobserved structural shock. It uses standard instrumental variable techniques to isolate the variation in the VAR reduced-form residuals that is due to the structural shock of interest. The approach requires an instrument correlated with the structural shock of interest and orthogonal to all other structural shocks.

For the example in this section, assume that the data are driven by a monetary policy shock, as well as another shock (or a combination of shocks) that we leave unidentified. Also assume that a valid instrument ($z_{t}$) for the monetary policy shock exists, namely that $z_{t}$ is correlated with $\varepsilon_{t}^{MonPol}$ and uncorrelated with the other shock $\varepsilon_{t}^{Other}$. More formally, $z_t$ satisfies the following properties:
$$
\begin{eqnarray}
    \mathbb{E}\left[ \varepsilon_{t}^{MonPol}z_{t}\right]  &=&\alpha \neq 0, \\
    \mathbb{E}\left[\varepsilon_{t}^{Other}z_{t}\right] &=&0,
    
\end{eqnarray}
$$
The condition $\alpha \neq 0$ is the *relevance* condition; it ensures the instrument has nonzero correlation with the shock of interest. If such an instrument exists, one can identify the impact response of each endogenous variable to the monetary policy shock. That is, one can identify one column of the $B$ matrix — here, the first column, which corresponds to the monetary policy shock, namely:[^4]
$$
    B=\left[
    \begin{array}{cc}
        b_{11} & - \\
        b_{21} & -%
    \end{array}%
    \right]
    
$$

The intuition is as follows. Recall that the reduced-form residuals $u_{yt}$ and $u_{rt}$ are a linear combination of two orthogonal shocks $\varepsilon_{t}^{MonPol}$ and $\varepsilon_{t}^{Other}$:
$$
    \begin{array}{c}
        u_{yt}=b_{11}\varepsilon_{t}^{MonPol}+b_{12}\varepsilon_{t}^{Other},
        \\
        u_{rt}=b_{21}\varepsilon_{t}^{MonPol}+b_{22}\varepsilon_{t}^{Other}.%
    \end{array}
    
$$
It is therefore possible to isolate the variation in $u_{yt}$ attributable to the shock of interest by regressing $u_{yt}$ on the instrument $z_{t}$:
$$
    u_{yt}=\beta z_{t}+\xi _{t},
    
$$
The fitted values of this first-stage regression $\hat{u}_{yt}=\hat{\beta}z_t$ capture the variation in $u_{yt}$ attributable to the monetary policy shock. As $z_t$ is orthogonal to $\varepsilon_{t}^{Other}$, the variation in $u_{yt}$ attributable to the other shock (namely, the component $b_{12}\varepsilon_{t}^{Other}$) ends up in the residual $\xi_t$. By projecting the residuals of the interest rate equation $u_{rt}$ on the fitted values of the previous regression $\hat{u}_{yt}$, it is possible to obtain a consistent estimate of the ratio $b_{21}/b_{11}$:
$$
    u_{rt}=\underset{b_{21}/b_{11}}{\underbrace{\gamma }}\hat{u}_{yt}+\zeta _{t},
    
$$

Because $\hat{u}_{yt}$ inherits orthogonality to $\varepsilon_{t}^{Other}$ from the first-stage projection, the variation in $u_{rt}$ attributable to the other shock is absorbed into the residual $\zeta_t$, while the fitted values $\hat{\gamma}\hat{u}_{yt}$ isolate the variation in $u_{rt}$ attributable to the monetary policy shock. If we normalize $b_{11}=1$ (that is, if we consider a monetary policy shock that raises the log-difference of US real GDP by 1 percentage point) we can easily recover $b_{21}=\gamma$.[^5] The procedure described in this section thus provides an estimate of the first column of $B$ up to a scaling factor:
$$
    B=\left[
    \begin{array}{cc}
        1 & - \\
        \gamma & -%
    \end{array}%
    \right]
    
$$
which can then be used to compute the impulse response to the monetary policy shock as described above.

**<u>In MATLAB</u>.** As for other identification schemes, set the field to identify the VAR with the external instrument. The mnemonic for the external instruments identification is the string . Unlike the other identification schemes, requires a second mandatory input: the external instrument itself must be supplied through the field. Without it the routine has no instrument to project the reduced-form residuals on, and identification cannot proceed. The remaining field set below, , is optional and is used only when plotting and saving the impulse responses.

``` matlab
VARopt.ident    = 'iv';
VARopt.IV       = mps;
VARopt.snames   = {bfeps('MonPol'), bfeps('Other')};
```

> \[label=box:mps\] **the instrument used in this example is fictitious and must never be replicated in applied work.**  A valid external instrument must satisfy two conditions: *relevance* (correlation with the structural shock of interest) and *exogeneity* (orthogonality to all other structural shocks). A canonical example meeting both conditions is the high-frequency monetary policy surprise of , constructed from narrow windows around FOMC announcements to isolate exogenous policy movements from the broader macroeconomic environment.
>
> The series used here is constructed by adding random noise to the monetary policy shock derived from the sign-restriction exercise of Section that section: , where $\sim \mathcal{N}(0,1)$. This makes no economic sense as an instrument, but it delivers something that works mechanically. The sole reason for using it is that the bivariate VAR(1) estimated throughout this handbook is too parsimonious to deliver credible results with any real-world instrument. The example is intended to illustrate the *mechanics* of proxy SVAR identification — how the code is set up, how the output is structured, and how the results compare to other approaches — not to serve as a model for instrument construction.

The identification with external instruments is then implemented with the usual call:

``` matlab
VAR_iv = VARmodel(X,nlags,detc,VARopt);
```

The structure is populated with consistent with the IV identification scheme and with , a structure containing the first-stage regression results. As in a standard instrumental variable approach, the F-statistic of the first stage is important to assess instrument relevance. Only the first column of the $B$ matrix is identified (the monetary policy shock); the second column is set to zero as a placeholder, since the other shock is left unidentified.[^6] As usual, the $B$ matrix can be printed as follows:

``` text
>> disp(VAR_iv.B)
    0.5375   0
    0.1538   0
```

A practical limitation of the exogeneity condition is that it is *not testable* in the exactly-identified case — that is, when there is one instrument for one structural shock. Since exogeneity requires orthogonality between the instrument and all other structural shocks, and these shocks are unobserved, there is no sample analog from which to construct a test. In the over-identified case (more instruments than structural shocks to identify), the over-identifying restrictions can be tested via the Sargan-Hansen $J$-test in a GMM framework (the Sargan test is a special case under homoskedasticity); these provide indirect evidence on instrument validity. See for an overview of weak-instrument and instrument-validity issues in IV estimation.

> **Assessing instrument strength: the first-stage F-statistic.**  The F-statistic of the first-stage regression tests whether the instrument is sufficiently correlated with the reduced-form residual of interest. A weak instrument — one with low partial correlation with the target variable — produces biased and imprecise IV estimates, regardless of whether the exogeneity condition is satisfied. The conventional rule of thumb, due to , is that the first-stage F-statistic should exceed 10. This threshold applies to the benchmark case of one instrument and one endogenous regressor at a 5% size-distortion tolerance; the appropriate critical value differs with the number of instruments and regressors — see for the full table. Below that threshold, the instrument is considered weak and the two-stage estimates are unreliable.
>
> report a first-stage F-statistic well above 10 for their high-frequency monetary policy surprise instrument, confirming its relevance. In the VAR Toolbox, the first-stage F-statistic is stored in and can be inspected directly:
>
> ``` text
> >> disp(VAR_iv.FirstStage.F)
>    13.2691
> ```
>
> In this example, the F-statistic of 13.27 exceeds the conventional threshold of 10, suggesting the instrument has adequate relevance.

The two-stage IV procedure delivers only the identified column of $B$, that is, the contemporaneous (impact, $h=0$) responses of the two variables to the monetary policy shock. These impact responses are the stars in Figure that section. From the impact responses onward, no further identifying information is needed: the responses at horizons $h \geq 1$ are obtained by propagating the impact vector through the estimated reduced-form VAR dynamics, exactly as for any other identification scheme described above. In other words, identification pins down where the impulse response starts, and the estimated VAR coefficients determine how it propagates over time. The full set of responses, from $h=0$ to the chosen horizon, is stored in . Figure that section reports the resulting impulse responses to the identified monetary policy shock.

> **Figure.** Impulse Responses to a Monetary Policy Shock

## Combining Sign Restrictions and External Instruments

The external instruments and sign restriction identification approaches can be combined as proposed by . The main idea of this approach is to identify one (or more) shocks with external instruments and the remaining shocks (or a subset of them) with sign restrictions. The motivation is practical: in many applications the researcher has a credible instrument for one shock of interest — typically the monetary policy shock — but no equally credible instrument for the other shocks driving the system. Rather than discarding the instrument and identifying all shocks with sign restrictions, or leaving the remaining shocks unidentified, this approach uses the instrument to point-identify the shock for which it is available and sign restrictions to set-identify the rest. The two strategies are complementary: the instrument delivers a sharp, point estimate for one column of $B$, while sign restrictions impose weaker, inequality-based constraints on the remaining columns.

This section builds on the example used in the previous section, where a monetary policy shock is identified with external instruments and a second shock is left unidentified. Unlike the previous section, assume here that the second shock driving the data is a demand shock, so that the system is now fully identified rather than only partially. Since the monetary policy shock is point-identified with the external instrument, no further restrictions are needed on its column of $B$; sign restrictions are therefore required only for the demand shock, as discussed in Section that section. Table that section summarizes the identifying restrictions on the elements of the structural impact matrix $B$, noting that the first column is identified with the external instrument while the second is restricted in sign:

<div class="minipage">

<div class="center">

<div id="tab:iv_SR">

|  |  |  |
|:---|:--:|:--:|
|  | Monetary Policy Shock | Demand Shock |
|  | ($\varepsilon_{t}^{MonPol}$) | ($\varepsilon_{t}^{Demand}$) |
| Output growth ($y_{t}$) | Ext. Instrument | \+ |
| Short-term Int. Rate ($r_{t}$) | Ext. Instrument | \+ |

<span class="smallcaps">Restrictions for Monetary Policy and Demand Shocks</span>

</div>

</div>

<span class="smallcaps">Note.</span> The signs represent restrictions on the elements of the structural impact matrix $B$. ‘$+$’ and ‘$-$’ indicate sign restrictions on the contemporaneous response. ‘Ext. Instrument’ indicates identification via an external instrument proxy. <span id="tab:iv_SR" label="tab:iv_SR"></span>

</div>

To see how to combine the external instrument and sign restrictions approaches, start by partitioning the matrix $B$ into a column vector $B^{IV}$, which captures the impact of the monetary policy shock, and a column vector $B^{SR}$, which captures the impact of the demand shock:
$$
    B=\left[
    \begin{array}{cc}
        B^{IV} & B^{SR}%
    \end{array}%
    \right] .  
$$
where $B^{IV}$ and $B^{SR}$ are $2\times 1$ vectors.[^7] Assuming that a valid instrument for the monetary policy shock exists, the first column of the $B$ matrix ($B^{IV}$) is point-identified as explained in the previous section.

We now show how to combine the external instruments identification approach with a standard sign restriction approach to identify the remaining structural shock ($\varepsilon_{t}^{Demand}$) conditional on the shock identified with the external instrument ($\varepsilon_{t}^{MonPol}$). To identify $B^{SR}$ (i.e. the contemporaneous impact of the demand shock) we proceed as follows. First, using (that section), re-write the covariance matrix of the reduced-form residuals as:
$$
    \Sigma_{u}=BB'=\left[
    \begin{array}{cc}
        B^{IV} & B^{SR}%
    \end{array}%
    \right] \left[
    \begin{array}{cc}
        B^{IV} & B^{SR}%
    \end{array}%
    \right]'.  
$$
As we have seen above, this decomposition of the covariance matrix is not unique. Let $P$ be the Cholesky decomposition of the covariance matrix $\Sigma_{u}$, and let $Q_j$ be a randomly drawn orthonormal matrix (where, as before, $j$ denotes a random draw) such that $Q_jQ_j'=I_k$, then:
$$
    \Sigma_{u}=PP'=PQ_jQ_j'P'=\left( PQ_j\right) \left(
    PQ_j\right)'
$$
Similarly to the sign restriction procedure, the identification strategy described in this section consists in constructing a large number of orthonormal matrices $Q_j$ that satisfy the following condition:
$$
    PQ_j=\left[
    \begin{array}{cc}
        B^{IV} & B_j^{SR}
    \end{array}%
    \right]
$$
where $B^{IV}$ is point-identified with the external instrument and $B_j^{SR}$ is set-identified with the sign restrictions. Thus, the main difference with the standard sign restriction procedure lies in the construction of the $Q_j$ matrix. Instead of obtaining $Q_j$ from a QR factorization of a random matrix with elements from the standard normal distribution, here we construct the $Q_j$ matrix sequentially, with the following two steps:

1.  Find a unit vector $Q^{IV}$ of dimension $k \times 1$ that rotates the first column of $P$ into the vector $B^{IV}$. That is, we find a $k\times 1$ unit vector $Q^{IV}$ such that the following equality holds:
    $$
            PQ^{IV}=B^{IV}
    \end{equation}
    ```

2.  Given $Q^{IV}$, build the remaining column of an orthonormal $2 \times 2$ matrix $Q_j$ following a standard Gram-Schmidt process.[^8] That is, find a $(k \times 1)$ vector $Q^{SR}_j$ such that the following equality holds:
    ``` math
    \begin{equation}
            \begin{bmatrix}
                Q^{IV} & Q^{SR}_j%
            \end{bmatrix}%
            \begin{bmatrix}
                Q^{IV} & Q^{SR}_j%
            \end{bmatrix}%
            '=Q_jQ_j'=I.
    \end{equation}
    ```

As in the standard sign restriction procedure, the matrix $B_j=PQ_j$ then represents a candidate structural representation because:
$$ math
\begin{equation}
        \Sigma_u = 
        \begin{bmatrix}
            B^{IV} & B_j^{SR}%
        \end{bmatrix}%
        \begin{bmatrix}
            B^{IV} & B_j^{SR}%
        \end{bmatrix}'
        =
        \underset{B_j}%
        {\underbrace{%
                P 
                \begin{bmatrix}
                    Q^{IV} & Q^{SR}_j%
                \end{bmatrix}}}%
        \underset{B_j'}%
        {\underbrace{
                \begin{bmatrix}
                Q^{IV} & Q^{SR}_j%
            \end{bmatrix}'
            P'}}
\end{equation}
```
and because $B_j=PQ_j$ is such that the associated structural shocks $\varepsilon_{jt} = B_j^{-1}u_t$ are orthogonal and have unit variance. It is therefore possible to check whether the elements of $B_j$ associated with a given random matrix $Q_j$ are consistent with the restrictions in Table that section — and, if so, retain the draw.

**<u>In MATLAB</u>.**  The implementation uses a single call to with . This unified interface performs the two-step identification internally: it first point-identifies the monetary policy column via IV, then searches over rotations of the remaining columns using sign restrictions. Three fields of are required: selects the scheme; supplies the instrument (carried over from Section that section); and encodes the sign restrictions on the remaining shocks. A key difference relative to the traditional sign restriction approach is that the sign restriction matrix has to be defined for the unidentified shocks only. That is, because the monetary policy column is fixed by the instrument, has now dimension $k \times k-1$ rather than $k \times k$ — one column for each shock that is still to be (set) identified:

``` matlab
% Unrestricted 0:
R = [ 1;  % Real GDP: positive
      1]; % 1-year rate: positive
```

The function infers from the number of columns of how many shocks remain to be identified and adjusts the rotation search accordingly. The combined identification is then invoked by setting and supplying via :

``` matlab
VARopt.figname = 'graphics/iv_sign';
VARopt.snames = {bfeps('MonPol'), bfeps('Demand')};

% Run hybrid identification. VARopt.IV=mps (from previous Section)  
% pins column 1 of B via the IV stage; VARopt.R rotates the 
% orthogonal complement via sign restrictions.
VARopt.ident = 'sign+iv';
VARopt.R = R;
VAR_ivsr = VARmodel(X, nlags, detc, VARopt);
```

The function internally calls the IV step to fix the first column of $B$, then constrains every candidate rotation so that the corresponding columns of $B_j$ equal $B^{IV}$ exactly, and applies Gram-Schmidt orthogonalization to search only over the remaining columns (Steps 1 and 2 of the algorithm above). The monetary policy shock is therefore never touched by the sign restriction loop; it enters each draw $j$ unchanged.[^9]

The structure has the same layout as from Section that section. The matrix contains all accepted draws of $B_j$ with dimension $2 \times 2 \times 1000$. The first column of every draw equals $B^{IV}$: fixed at the IV estimate, it is never altered by the sign restriction loop.[^10] As for the standard sign restriction approach, point-wise median impulse responses are stored in , and the Fry-Pagan median-target draw is likewise available in . Because the first column of $B_j$ is held fixed at $B^{IV}$ across all accepted draws, the median-target selection operates only on the sign-restricted (demand) column; the median-target responses to the monetary policy shock therefore coincide with both and the IV responses of Section that section, and can differ from only for the demand shock. The impulse responses to the monetary policy shock are, by construction, equal to those in the external instrument example of Section that section, since $B^{IV}$ is held fixed at the OLS estimate and parameter uncertainty is not accounted for. The impulse responses to the demand shock can be plotted with the following lines of code:

``` matlab
VARopt.pick = 2;
VARirplot(VAR_ivsr.IRmed,VARopt);
```

Figure that section reports the impulse responses of the log-difference of US real GDP and the 1-year rate to the demand shock.

> **Figure.** Impulse Responses to a Demand Shock

## Identification with Exogenous Variables

In some applications, the researcher observes a series $s_t$ that can be treated as contemporaneously exogenous to the VAR system — an observed measure of the structural shock of interest, distinct from the latent shock vector $\varepsilon_t$. Rather than using $s_t$ as an external instrument in a two-stage IV regression (as in the proxy SVAR approach of Section that section), one can include it directly as a contemporaneous regressor in each equation of the VAR:
$$

    x_t = c + \sum_{j=1}^{p}\Phi_j x_{t-j} + \delta s_t + u_t,
$$
where $\delta$ is a $k\times 1$ vector of impact coefficients. Because $s_t$ is exogenous, the OLS estimate $\hat{\delta}$ admits a direct structural reading: it is the on-impact response of each endogenous variable to a one-unit movement in $s_t$, with the other shocks held fixed. This is exactly the object that a column of the structural impact matrix $B$ records — the contemporaneous effect of a single structural shock on the system (see Section that section). This lets us read $\hat{\delta}$ as the first column of $B$, up to a choice of shock size: a one-unit change in $s_t$ gives the column as $\hat{\delta}$, while a one-standard-deviation change gives $\hat{\delta}\,\hat{\sigma}_s$, with $\hat{\sigma}_s$ the sample standard deviation of $s_t$.

Note that this approach is closely related to the proxy SVAR: both exploit the same external series to identify one structural shock, and they differ only in how that series enters. Here it enters directly as a contemporaneous regressor in the reduced-form VAR — in the role of the shock $s_t$ — whereas in the proxy SVAR of Section that section the same series enters as an instrument $z_t$ in a two-stage IV regression. Under instrument exogeneity and a common lag structure, the two estimators are asymptotically equivalent . The running example makes this concrete: the single series is reused in both roles — directly as the exogenous shock $s_t$ here, and as the instrument $z_t$ in the proxy SVAR of Section that section — which is harmless for illustration and is exactly the equivalence just stated.

**In MATLAB.** The exogenous-variable identification scheme is selected by setting and supplying $s_t$ via . A dedicated struct (i.e. different from the structure used throughout this section) keeps settings isolated from the rest of the examples. The identified responses are computed as:

``` matlab
VARopt_exog = VARoption;
VARopt_exog.mnem      = Xmnem;
VARopt_exog.vnames    = Xvnames;
VARopt_exog.nsteps    = 20;
VARopt_exog.ident     = 'exog';
VARopt_exog.exoshock  = mps;
VARopt_exog.snames    = {bfeps('MonPol')};
VAR_exog = VARmodel(X, nlags, detc, VARopt_exog);
```

The field is populated with the estimated $B$ matrix, where the first column equals $\hat{\delta}\,\hat{\sigma}_s$: the OLS coefficient vector $\hat{\delta}$ from equation that section, scaled by $\hat{\sigma}_s$ (the sample standard deviation of $s_t$) to represent a one-standard-deviation shock. Storing this column in $B$ is a slight abuse of notation: the object recovered here is $\hat{\delta}$ (scaled), not a column of the structural impact matrix in the sense of the recursive or sign-restricted schemes. It is nonetheless convenient to place it in $B$, since the impact responses it generates are directly comparable across identification schemes.

As in the external-instrument case of Section that section, the exogenous variable identifies a single structural shock, so only the first column of $B$ is identified; the remaining $k-1$ columns are set to zero because the other shocks are left unidentified.[^11] Lags of $s_t$ can be included by setting (default 0, contemporaneous only). General exogenous regressors not used for identification are passed via the fifth positional argument of , separate from . For example, in a VAR for a small open economy, one may want to control for lags of world GDP; this can be done by passing a matrix of world GDP lags as , so that the domestic block conditions on global conditions without treating foreign output as endogenous.

Figure that section reports the impulse responses to the identified monetary policy shock, which can be obtained with the standard function (setting ):

> **Figure.** Impulse Responses to a Monetary Policy Shock

## Summary and Next Steps

Section [sec:ident](04-identification-in-the-var-toolbox.md) has established seven approaches for recovering the structural impact matrix $B$ from the estimated reduced-form parameters. With an identified $B$ in hand, two tasks remain. Section [sec:inference](05-statistical-inference.md) describes how to quantify uncertainty around structural impulse responses, variance decompositions, and historical decompositions. Section [sec:dynamic](06-structural-dynamic-analysis.md) then develops the three main tools for structural dynamic analysis: impulse response functions (Section that section), forecast error variance decompositions (Section that section), and historical decompositions (Section that section), together with their implementation in MATLAB. Statistical inference is covered before structural dynamic analysis because the figures and tables in Section [sec:dynamic](06-structural-dynamic-analysis.md) routinely display bootstrap confidence bands and Bayesian credible bands; the procedures introduced in Section [sec:inference](05-statistical-inference.md) are therefore a prerequisite for that material.

[^1]: To ensure draws are spread uniformly over the orthogonal group, $Q$ is generated via the QR factorization of a random normal matrix. The sign of each column of $Q$ is adjusted so that the corresponding diagonal element of $R$ is positive, which guarantees $\det Q = +1$ and ensures draws are uniformly spread over the rotation subgroup $SO(n)$ in a manner that approximates the Haar measure — see .

[^2]: The toolbox imposes the narrative restrictions by equal-weight acceptance-rejection: every accepted draw enters the reported set with the same weight. When parameter uncertainty is accounted for (), this is not the posterior derived by . Because the probability that a sign-admissible rotation also satisfies the narrative restrictions varies with the reduced-form parameters $(\Phi,\Sigma_u)$, plain acceptance-rejection reweights the reduced-form posterior toward regions where the narrative restrictions are easier to satisfy. The correct posterior is recovered by importance sampling: each accepted draw receives a weight proportional to the reciprocal of that probability, estimated by Monte Carlo over rotations at each reduced-form draw, and the draws are resampled accordingly. The toolbox follows the common convention of omitting this reweighting. The two schemes coincide when parameter uncertainty is switched off (, as in the example of this section), since the importance weight is then constant across draws.

[^3]: imposes a hard ceiling on the total number of candidate draws, preventing the algorithm from running indefinitely when the restrictions are very tight and accepted draws are rare.

[^4]: Note that in the sign-restriction example of Section that section, the monetary policy shock occupied the second column; the ordering is a modeling choice with no substantive implications.

[^5]: In the VAR Toolbox, the impulse responses are further normalized to match the standard deviations of the shocks, as explained in . See Appendix that section for details.

[^6]: Setting the unidentified columns to zero rather than setting them to NaN ensures that the plotting functions (, , etc.) do not produce errors when iterating over all columns of $B$.

[^7]: Note that both $B^{IV}$ and $B^{SR}$ can be matrices, i.e. can include more than one shock, as in the original paper by .

[^8]: Let $j$ index the columns of $Q.$ Let $Q_{j-1}$ denote the first $j-1$ columns of $Q$, such that $Q_{2-1}=Q_{1}=q_{1}.$ Let $x_{j}$ be a draw from a Normal distribution on $\mathbb{R}^{k}.$ Then the $j-$th column of $Q$ can be constructed as: $q_{j}=\left( I_{k}-Q_{j-1}Q_{j-1}'\right) x_{j}/\left\Vert\left( I_{k}-Q_{j-1}Q_{j-1}'\right) x_{j}\right\Vert$.

[^9]: is the IV point estimate, held fixed across all draws regardless of ; see Section [sec:inference](05-statistical-inference.md).

[^10]: This can be verified by displaying the IV column from Section that section, namely , and the first column of ; the two must agree to numerical precision.

[^11]: Internally, completes $B$ to an invertible matrix in order to back out the structural shocks required by the historical decomposition; the unidentified columns are then zeroed in the stored , and their impulse responses, variance-decomposition shares, and historical-decomposition contributions are zeroed accordingly, since they carry no economic meaning.
