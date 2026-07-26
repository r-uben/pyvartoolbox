---
title: "A Brief Overview of VAR Models"
label: "sec:overview"
source: VAR Handbook (Cesa-Bianchi)
type: reformatted-extract
licence: GPL-3.0
---

# A Brief Overview of VAR Models

> **Source.** This page is a reformatted extract of the *VAR Handbook* by
> Ambrogio Cesa-Bianchi, from the MATLAB VAR Toolbox (https://github.com/ambropo/VAR-Toolbox). The content is
> his; only the format has changed, so that it can be read in fragments by a
> machine. Redistributed under the GPL-3.0 the original carries. Code
> listings are **MATLAB** and do not apply to `pyvartoolbox` — see
> [conventions](../references/conventions.md) for where the APIs differ.

This section develops the core theoretical objects — the reduced-form and structural representations, the moving-average (Wold) representation, the stability condition, and the identification problem — before turning to practical implementation in Section [sec:rfvar_toolbox](03-var-estimation-in-the-var-toolbox.md). Readers already familiar with VAR theory may proceed directly to Section [sec:rfvar_toolbox](03-var-estimation-in-the-var-toolbox.md).

## The Reduced-Form VAR

A VAR with $k$ endogenous variables and $p$ lags — a VAR($p$) — describes the evolution of the $k\times 1$ vector $x_t$ as a function of its own lags, a constant, and a serially uncorrelated error term:
$$
    x_{t}= c + \Phi_1 x_{t-1} + \cdots + \Phi_p x_{t-p} + u_{t}, 
$$
where $c$ is a $k\times 1$ vector of intercepts; $\Phi_1,\ldots,\Phi_p$ are $k\times k$ matrices of autoregressive coefficients; and $u_t$ is a $k\times 1$ vector of serially uncorrelated reduced-form residuals with zero mean and time-invariant covariance matrix $\mathbb{V}(u_{t})\equiv \Sigma_{u}$ (homoskedasticity). The covariance matrix $\Sigma_u$ is symmetric and positive definite. Its off-diagonal elements capture the contemporaneous co-movement of the reduced-form residuals.

The running example used throughout this handbook is a bivariate VAR(1) in $x_t=(y_t,r_t)'$, where $y_t$ is the log-difference of US real GDP and $r_t$ is the 1-year US Treasury bill yield. Setting $p=1$ leaves a single autoregressive matrix, and we write $\Phi\equiv\Phi_1$ from here on. The notebox below explains the role this example plays throughout the handbook and the limitations that come with it.

> \[label=box:example\] **The running example.** The bivariate VAR(1) in real GDP growth and the short-term interest rate serves a purely pedagogical purpose. With $k=2$ variables and $p=1$ lag, every object encountered in the handbook — the companion matrix, the Wold (moving-average) representation, the structural impact matrix $B$, and the identifying restrictions — can be written out in full and matched line by line to the corresponding output of the VAR Toolbox. A larger system would bury this mapping in matrices too big to display, and the connection between theory and code would be lost.
>
> The two variables are also chosen so that the identification schemes introduced later carry a recognisable economic interpretation. A recursive ordering in which output does not respond within the period to the interest rate, sign restrictions on the response of output to a monetary shock, or the use of an external instrument for the policy rate all have a natural reading in a system of activity and a policy variable. This keeps the identifying assumptions easy to motivate while the algebra stays transparent.
>
> These assumptions are illustrative, not substantive. A two-variable, single-lag system is far too small to serve as a credible empirical model: it omits variables that any serious analysis of output and interest rates would include — prices first among them — and a single lag is too short to capture the dynamics of macroeconomic data. The shortage of variables and the shortage of shocks are the same limitation seen from two sides: because the structural impact matrix $B$ is square, a system with $k$ variables admits exactly $k$ structural shocks, so the bivariate example attributes every movement in output to just two disturbances. The fluctuations of GDP reflect many more — technology, demand, fiscal, and financial shocks among them — and these cannot be recovered from a system that allows only two. The identifying restrictions are therefore defensible only as teaching devices. The numerical results reported throughout should be read as demonstrations of the toolbox, not as empirical findings, and no economic conclusions should be drawn from them.

The reduced-form representation is:
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
    \end{bmatrix}%
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
    \begin{array}{c}
        u_{yt} \\
        u_{rt}%
    \end{array}%
    \right]   
$$
or:
$$
    \begin{array}{c}
        y_{t}=c_y+ \phi _{11}y_{t-1}+\phi _{12}r_{t-1}+u_{yt}, \\
        r_{t}=c_r+ \phi _{21}y_{t-1}+\phi _{22}r_{t-1}+u_{rt},%
    \end{array}
    
$$
with residual covariance matrix:
$$
    \Sigma_{u}=\left[
    \begin{array}{cc}
        \sigma _{y}^{2} & \sigma _{yr} \\
        \sigma _{yr} & \sigma _{r}^{2}%
    \end{array}%
    \right].  
$$
The diagonal elements $\sigma_y^2$ and $\sigma_r^2$ are the variances of the two residuals; the off-diagonal element $\sigma_{yr}$ captures their contemporaneous co-movement after controlling for persistence. This covariance is particularly important: it collects the information on the contemporaneous relations among the variables in the system and is the key input to the identification problem (Section that section). The parameters $c$ and $\Phi$ can be estimated consistently by OLS; $\Sigma_u$ is estimated as the sample covariance matrix of OLS residuals. No distributional assumption is required for OLS consistency; normality is introduced only where it is explicitly invoked. Section [sec:rfvar_toolbox](03-var-estimation-in-the-var-toolbox.md) describes the implementation in the VAR Toolbox.

## The Structural VAR Representation

The reduced-form VAR(1) introduced above can be written in its structural form as:
$$
    x_{t} = c + \Phi x_{t-1}+B\varepsilon_{t}
    
$$
where $x_{t}$, $c$, and $\Phi$ have already been defined above; $B$ is a $k \times k$ matrix of coefficients, typically referred to as the *structural impact matrix*; and $\varepsilon_{t}$ is a $k \times 1$ vector of serially uncorrelated innovations (with $k=2$ in the running example), known as *structural shocks*, which are assumed to be mutually uncorrelated with zero mean and unit variance.[^1] The relation between the structural shocks and the reduced-form innovations is therefore given by the following identity:
$$

    u_{t} = B\varepsilon_{t}.
$$
The structural VAR (that section) provides a finite-order linear approximation to the dynamics implied by the *solution* of a structural model of the economy (for example, the equilibrium dynamics of a DSGE model); the structural shocks $\varepsilon_t$ are designed to recover the model’s economic shocks (for example, TFP shocks or monetary policy shocks).[^2]

In our simple example of a bivariate VAR(1), let the two structural shocks be a demand shock $\left( \varepsilon_{t}^{Demand} \right)$ and a monetary policy shock $\left( \varepsilon_{t}^{MonPol} \right)$. With only two shocks, all variation in output growth and the interest rate is attributed to these two disturbances, whereas in reality many more drive both series. The impulse responses reported below should therefore be read as illustrations of the identification schemes, not as realistic estimates, and need not match standard economic priors. Box that section discusses this simplification and its limitations in detail.

The simple structural VAR(1) can be written as a system of linear equations:
$$

    \begin{bmatrix}
        y_{t} \\
        r_{t}%
    \end{bmatrix}%
    =%
    \begin{bmatrix}
        c_{y} \\
        c_{r}
    \end{bmatrix}%
    +
    \begin{bmatrix}
        \phi _{11} & \phi _{12} \\
        \phi _{21} & \phi _{22}%
    \end{bmatrix}%
    \begin{bmatrix}
        y_{t-1} \\
        r_{t-1}%
    \end{bmatrix}%
    +%
    \begin{bmatrix}
        b_{11} & b_{12} \\
        b_{21} & b_{22}%
    \end{bmatrix}%
    \begin{bmatrix}
        \varepsilon_{t}^{Demand} \\
        \varepsilon_{t}^{MonPol}%
    \end{bmatrix}%
$$
or:
$$

    \begin{array}{c}
        y_{t}=c_{y} + \phi _{11}y_{t-1}+\phi _{12}r_{t-1}+b_{11}\varepsilon
        _{t}^{Demand}+b_{12}\varepsilon_{t}^{MonPol} \\
        r_{t}=c_{r} + \phi _{21}y_{t-1}+\phi _{22}r_{t-1}+b_{21}\varepsilon
        _{t}^{Demand}+b_{22}\varepsilon_{t}^{MonPol}%
    \end{array}
$$
Moreover, as $\varepsilon_{t}=\left( \varepsilon_{t}^{Demand},\varepsilon_{t}^{MonPol}\right)'$ is assumed to be a $2\times 1$ vector of mutually uncorrelated white noise processes, its covariance matrix can be written as:
$$
 
    \mathbb{V}(\varepsilon_{t})\equiv \Sigma_{\varepsilon }=\left[
    \begin{array}{cc}
        1 & 0 \\
        0 & 1%
    \end{array}%
    \right] =I_{2}.
$$
The assumption that the elements of $\varepsilon_{t}$ are mutually uncorrelated is crucial for interpreting each element as a distinct, independent structural shock. It implies that we can track the effects that a shock to, say, $\varepsilon_{t}^{Demand}$ has on all variables in the VAR keeping the other shock to zero (and vice versa). The $B$ matrix is also crucial. To see that, consider a unit surprise in $\varepsilon_{t}^{MonPol}$, i.e. a surprise tightening in monetary policy. What are the consequences for output growth $y_{t}$ and the short-term interest rate $r_{t}$? The answer to this question is given by the second column of the $B$ matrix: $y_{t}$ will move by $b_{12}$ and $r_{t}$ will move by $b_{22}$. This is why the $B$ matrix is also known as the structural impact matrix. The $\Phi$ matrix can then be used to track the dynamic effects of the shocks in $t+1$, $t+2$, etc. (as we shall see in more detail in Sections [sec:ident](04-identification-in-the-var-toolbox.md) and [sec:dynamic](06-structural-dynamic-analysis.md)).

The structural innovations $\varepsilon_{t}$ are unobservable, which means that we cannot directly estimate (that section). However, we can link the structural innovations and impact matrix to the reduced-form innovations using that section:
$$
    \begin{array}{c}
        u_{yt}=b_{11}\varepsilon_{t}^{Demand}+b_{12}\varepsilon_{t}^{MonPol},
        \\
        u_{rt}=b_{21}\varepsilon_{t}^{Demand}+b_{22}\varepsilon_{t}^{MonPol}.%
    \end{array}
    
$$
Equation that section shows how the reduced-form innovations $u_{t}=\left( u_{yt}',u_{rt}'\right)'$ are a linear combination of the structural innovations. Thus, a reduced-form VAR cannot be used to trace the causal effects of economically interpretable shocks: absent an estimate of $B$, any observed movement in $u_{yt}$ cannot be attributed to a single structural source. Recovering the $B$ matrix is therefore the prerequisite for tracing the causal effects of structural shocks. This is the essence of identification in VARs, which is the subject of Section [sec:ident](04-identification-in-the-var-toolbox.md).

## The Moving-Average (Wold) Representation

The structural moving-average (MA) representation — also known as Wold representation — underpins both the stability analysis of the next subsection and the structural dynamic analysis of Section [sec:dynamic](06-structural-dynamic-analysis.md). It expresses each observation as a function of a deterministic component, past structural shocks, and initial conditions.

The structural MA representation can be obtained by recursively substituting the lagged values on the right-hand side of the structural VAR. Starting from:
$$
    x_{t}= c + \Phi x_{t-1}+B\varepsilon_{t},
$$
we can substitute $x_{t-1}= c + \Phi x_{t-2}+B\varepsilon_{t-1}$ into the equation above to get:
$$
    x_{t}= c + \Phi(c + \Phi x_{t-2}+B\varepsilon_{t-1})+B\varepsilon_{t}= (I + \Phi)c + \Phi^{2}x_{t-2}+\Phi B\varepsilon_{t-1}+B\varepsilon_{t}.
$$
Repeating this process recursively yields:
$$

    x_{t}=\sum_{j=0}^{t-1}\Phi^{j}c + \Phi^{t}x_{0}+\sum_{j=0}^{t-1}\Phi^{j}B\varepsilon_{t-j},
$$
where $x_{0}$ is the initial condition of the process (in practice, the first observation of the available data in a finite sample). The sums run to $t-1$ because the representation is anchored at $t=0$: the shock term at position $j$ is $\varepsilon_{t-j}$, so at $j=t-1$ it equals $\varepsilon_{t-(t-1)}=\varepsilon_{1}$, the shock at the first period. The initial condition $x_0$ is taken as given; the representation holds for $t \geq 1$. This is the structural MA representation of the VAR. It shows that each observation ($x_{t}$) can be decomposed into three components:

- A term capturing the cumulative effect of the constant: $\sum_{j=0}^{t-1}\Phi^{j}c$

- A term capturing the influence of the initial condition: $\Phi^{t}x_{0}$

- A weighted sum of all past and present structural shocks: $\sum_{j=0}^{t-1}\Phi^{j}B\varepsilon_{t-j}$

The structural MA representation is more than a mathematical curiosity. It provides the foundation for the structural dynamic analysis tools we will develop in Section [sec:dynamic](06-structural-dynamic-analysis.md): impulse response functions trace out the matrices $\Phi^{j}B$, forecast error variance decompositions measure, for each horizon $h$, the share of the forecast error variance $\text{Var}\!\left(\sum_{j=0}^{h}\Phi^{j}B\varepsilon_{t-j}\right)$ attributable to each structural shock, and historical decompositions use this representation to attribute observed movements in $x_t$ to specific realizations of past shocks, initial conditions, and deterministic trends. It is also essential for understanding the stability properties of VARs, as discussed next.

## Stability

Now consider the limiting case in which we let $t\to\infty$, extending the Wold representation to the infinite past. Then we can re-write the finite-horizon representation that section as:
$$
    x_{t}=\sum_{j=0}^{\infty}\Phi^{j}c + \lim_{j\to\infty}\Phi^j x_{t-j}+\sum_{j=0}^{\infty}\Phi^{j}B\varepsilon_{t-j}.
$$
The matrix $\Phi$ (and its powers) plays a crucial role here: it determines whether a shock from the infinitely distant past still has an effect on $x_t$ today. Recall that (in most cases) VARs are tools designed to study cyclical variations around trends, i.e. business cycle fluctuations — not permanent shifts. During a recession, growth slows down but eventually rebounds and output resumes its trend pace. In other words, the shocks that drive business cycles are transitory: they move variables away from their equilibrium, but eventually their effects fade. Stability is the formal expression of this idea: deviations of the modeled variables from their mean are temporary, not permanent. For this to happen, two conditions must hold: the infinite sums $\sum_{j=0}^{\infty}\Phi^{j}$ must converge to finite values, and the middle term $\Phi^{\infty}x_{t-\infty}$ must vanish.

Mathematically, stability requires all eigenvalues of $\Phi$ to lie strictly inside the unit circle:
$$
    |\lambda_i(\Phi)| < 1 \quad \forall i,
$$
where $\lambda_i(\Phi)$ are the eigenvalues of $\Phi$. When this condition holds, $\Phi^j \to 0$ as $j\to\infty$, and the Wold representation that section simplifies to the infinite-horizon form:
$$

    x_{t}=\sum_{j=0}^{\infty}\Phi^{j}c+\sum_{j=0}^{\infty}\Phi^{j}B\varepsilon_{t-j}.
$$
In the absence of new shocks, $x_t$ converges to its equilibrium at a rate governed by the eigenvalues of $\Phi$. For a VAR($p$) with $p>1$, the stability condition must be applied to the $(kp\times kp)$ companion matrix $\mathcal{F}$ (formally defined in Box that section) rather than to $\Phi_1$ alone: checking $|\lambda_i(\Phi_1)|<1$ is neither necessary nor sufficient.

> \[label=box:companion\] **The companion-form representation.** So far we have focused on VAR(1) models for simplicity. To extend the same machinery to a VAR($p$) with $p > 1$ lags, we rewrite the model in companion form: a VAR($p$) in $k$ variables is stacked into an equivalent VAR(1) in $kp$ variables, so that all the VAR(1) results derived above apply unchanged.
>
> Consider a VAR(2):
> $$
> \begin{equation*}
> \begin{bmatrix}
> y_t \\
> r_t
> \end{bmatrix}
> =
> \underbrace{
> \begin{bmatrix}
> \phi_{11}^1 & \phi_{12}^1 \\
> \phi_{21}^1 & \phi_{22}^1
> \end{bmatrix}}_{\Phi_1}
> \begin{bmatrix}
> y_{t-1} \\
> r_{t-1}
> \end{bmatrix}
> +
> \underbrace{
> \begin{bmatrix}
> \phi_{11}^2 & \phi_{12}^2 \\
> \phi_{21}^2 & \phi_{22}^2
> \end{bmatrix}}_{\Phi_2}
> \begin{bmatrix}
> y_{t-2} \\
> r_{t-2}
> \end{bmatrix}
> +
> \underbrace{
> \begin{bmatrix}
> b_{11} & b_{12} \\
> b_{21} & b_{22}
> \end{bmatrix}}_{B}
> \begin{bmatrix}
> \varepsilon_t^{Demand} \\
> \varepsilon_t^{MonPol}
> \end{bmatrix}
> \end{equation*}
> ```
>
> We can rewrite this as a VAR(1) by defining an expanded state vector that includes lagged values:
> ``` math
> \begin{equation*}
> \begin{bmatrix}
> y_t \\
> r_t \\
> y_{t-1} \\
> r_{t-1}
> \end{bmatrix}
> =
> \underbrace{
> \begin{bmatrix}
> \phi_{11}^1 & \phi_{12}^1 & \phi_{11}^2 & \phi_{12}^2 \\
> \phi_{21}^1 & \phi_{22}^1 & \phi_{21}^2 & \phi_{22}^2 \\
> 1 & 0 & 0 & 0 \\
> 0 & 1 & 0 & 0
> \end{bmatrix}}_{\text{Companion matrix } \mathcal{F}}
> \begin{bmatrix}
> y_{t-1} \\
> r_{t-1} \\
> y_{t-2} \\
> r_{t-2}
> \end{bmatrix}
> +
> \underbrace{
> \begin{bmatrix}
> b_{11} & b_{12} \\
> b_{21} & b_{22} \\
> 0 & 0 \\
> 0 & 0
> \end{bmatrix}}_{\text{Impact matrix } \mathcal{B}}
> \begin{bmatrix}
> \varepsilon_t^{Demand} \\
> \varepsilon_t^{MonPol}
> \end{bmatrix}
> \end{equation*}
> ```
>
> The companion matrix $\mathcal{F}$ has dimension $(kp \times kp)$, and the expanded impact matrix $\mathcal{B}$ has dimension $(kp \times k)$: the original $k \times k$ structural impact matrix $B$ padded with zeros, as shown above. With this representation, impulse responses for a VAR($p$) of any order follow from the same recursion used for the VAR(1) in Section that section, with $\mathcal{F}$ and $\mathcal{B}$ in place of $\Phi$ and $B$; only the first $k$ rows of the result correspond to the original variables of interest, while the remaining rows track lagged values and are not reported. In the VAR Toolbox, the companion form is constructed internally by ; users never need to form $\mathcal{F}$ explicitly.

> **Why eigenvalues govern stability.**  Start with the scalar case: suppose $x_t = \phi\, x_{t-1}$. After $j$ periods, $x_t = \phi^j x_0$. The sequence $\{x_t\}$ is a geometric series in $\phi$: it converges to zero if $|\phi| < 1$ and diverges if $|\phi| > 1$. The scalar $\phi$ encodes the persistence of the system in a single number.
>
> A VAR is the same idea with matrices. The matrix $\Phi$ can scale different directions of the system by different amounts. A scalar $\lambda$ is an eigenvalue of $\Phi$ if there exists a non-zero vector $v$ such that $\Phi v = \lambda v$: that is, $\Phi$ acts on $v$ purely as scalar multiplication by $\lambda$, with no rotation. The $k$ values of $\lambda$ for which such a $v$ exists are the solutions to the characteristic equation $\det(\Phi - \lambda I) = 0$. Each eigenvalue $\lambda_i$ plays exactly the role of $\phi$ along the direction defined by its eigenvector $v_i$: it is the scalar that summarizes how the system evolves along that particular direction.
>
> To see this, decompose $\Phi = P\Lambda P^{-1}$, where $P$ is the matrix of eigenvectors and $\Lambda = \mathrm{diag}(\lambda_1,\ldots,\lambda_k)$. Raising to the $j$-th power gives:
> ``` math
> \begin{equation*}
> \Phi^j = P\Lambda^j P^{-1} = P\,\mathrm{diag}(\lambda_1^j,\ldots,\lambda_k^j)\,P^{-1}.
> \end{equation*}
> ```
> This is again a geometric series, now running independently along each axis. It converges to zero if and only if $|\lambda_i| < 1$ for all $i$: a single eigenvalue with $|\lambda_i| \geq 1$ is sufficient for non-stationarity.
>
> The largest eigenvalue in modulus governs how slowly the system returns to equilibrium. An eigenvalue close to 1 implies highly persistent responses to shocks; an eigenvalue close to 0 implies rapid decay. This is why impulse responses of persistent VARs remain elevated for many horizons.

Stability is verified numerically after estimating the VAR. Section [sec:rfvar_toolbox](03-var-estimation-in-the-var-toolbox.md) describes how the VAR Toolbox computes the eigenvalues of $\mathcal{F}$ .

**<u>Equilibrium (aka, the unconditional mean)</u>.** Suppose a shock has displaced the system to some arbitrary initial position $x_0$. The question is where the system will be in the infinitely distant future. The answer follows from iterating the VAR forward and taking conditional expectations. The same substitution used to derive the Wold representation in that section yields the $h$-step-ahead conditional expectation:
$$ math
\begin{equation}

    \mathbb{E}\!\left[x_{h}\mid x_0\right]
    =\Phi^{h}x_{0}
    \;+\;\sum_{j=0}^{h-1}\Phi^{j}c
    \;+\;\sum_{j=0}^{h-1}\Phi^{j}B\,\mathbb{E}[\varepsilon_{h-j}].
\end{equation}
```
Under stability, $\Phi^{h}\to 0$ as $h\to\infty$, so the initial-condition term vanishes. The geometric series $\sum_{j=0}^{h-1}\Phi^{j}$ converges under stability, so the deterministic component has a finite limit. The last term vanishes because future shocks have zero conditional expectation, $\mathbb{E}[\varepsilon_{h-j}]=0$ for $j=0,\ldots,h-1$. Taking the limit, only the deterministic component survives:
$$

    \lim_{h\to\infty}\mathbb{E}\!\left[x_{h}\mid x_0\right]
    =\sum_{j=0}^{\infty}\Phi^{j}c
    =(I-\Phi)^{-1}c
    \;\equiv\;\mu,
$$
where $\sum_{j=0}^{\infty}\Phi^{j}=(I-\Phi)^{-1}$ is the matrix geometric-series sum, which converges under stability. The limit $\mu=(I-\Phi)^{-1}c$ is the equilibrium of the VAR. Because the initial-condition term $\Phi^{h}x_0$ vanishes, the limiting forecast retains no dependence on the conditioning information $x_0$: it is the same fixed point regardless of where the system started. A conditional expectation that no longer depends on what is conditioned on coincides with the unconditional mean; this is why the equilibrium computed here as a limit of conditional means is also $\mu=\mathbb{E}[x_t]$. The same value follows directly by applying the expectations operator to that section and using $\mathbb{E}[\varepsilon_{t-j}]=0$.

In our simple example, a monetary policy easing that raises output growth above its long-run trend, will do so only temporarily: once the impulse dissipates, the system converges back to $\mu$ (namely, the average growth rate of real GDP over the sample period) at a rate governed by the eigenvalues of $\Phi$.

## The Identification Problem

The key difference between the structural and reduced-form VARs lies in the covariance matrix of their innovations. While the covariance matrix of the structural VAR innovations is diagonal ($\Sigma_{\varepsilon }=I_{2}$), in general the reduced-form innovations are correlated among themselves, so that their covariance is given by a non-diagonal symmetric positive-definite matrix $\Sigma_{u}$ (defined in that section).

As established in Section that section, the covariance matrix of the reduced-form residuals captures the contemporaneous co-movement across variables. Using that section, it can be linked directly to the structural impact matrix $B$:
$$
    \Sigma_{u}=\mathbb{E}\left[ u_{t}u_{t}'\right] =B\mathbb{E}\left[
    \varepsilon_{t}\varepsilon_{t}'\right] B'=BB'
    
$$
This means that there is a mapping between the estimated covariance matrix of the reduced-form residuals ($\Sigma_{u}$) and the unobserved matrix of structural impact coefficients ($B$). The identification problem amounts to finding a $B$ matrix that satisfies $\Sigma_{u}=BB'$.

Unfortunately this is not as easy as it sounds. We can think of (that section) as a system of equations in the $4$ unknown coefficients of the $B$ matrix. That is:
$$
    \left[
    \begin{array}{cc}
        \sigma _{y}^{2} & \sigma _{yr} \\
        \sigma _{yr} & \sigma _{r}^{2}%
    \end{array}%
    \right] =\left[
    \begin{array}{cc}
        b_{11}^{2}+b_{12}^{2} & b_{11}b_{21}+b_{12}b_{22} \\
        b_{11}b_{21}+b_{12}b_{22} & b_{21}^{2}+b_{22}^{2}%
    \end{array}%
            \right],  
$$
which can be rewritten as the following system of equations:
$$
    \left\{
    \begin{array}{l}
        \sigma _{y}^{2}=b_{11}^{2}+b_{12}^{2} \\
        \sigma _{yr}=b_{11}b_{21}+b_{12}b_{22} \\
        \sigma _{yr}=b_{11}b_{21}+b_{12}b_{22} \\
        \sigma _{r}^{2}=b_{21}^{2}+b_{22}^{2}%
    \end{array}%
    \right.   
$$
The problem is that the $\Sigma_{u}$ matrix, given its symmetric nature, leads to only $3$ independent restrictions. In other words, the second and the third equation are identical. This means that we are left with $4$ unknowns (the $b$’s) but only $3$ equations. The system is underidentified, meaning that there are infinitely many combinations of the $b$’s that solve the system of equations implied by (that section).

> \[label=box:rotation\] **The rotation representation of the identification problem.**  The underdetermination of $B$ has a clean geometric structure. Because $\Sigma_u$ is symmetric and positive definite, there exists at least one matrix $B_0$ satisfying $\Sigma_u = B_0 B_0'$; fix any such $B_0$. Then for any $k \times k$ orthogonal matrix $Q$ satisfying $QQ' = I_k$, the matrix $B_0 Q$ is also a valid solution:
> ``` math
> \begin{equation*}
> (B_0 Q)(B_0 Q)' = B_0 \underbrace{QQ'}_{=I_k} B_0' = B_0 B_0' = \Sigma_u.
> \end{equation*}
> ```
> The set of all solutions to $\Sigma_u = BB'$ is therefore the orbit $\{B_0 Q : QQ' = I_k\}$. Every identification scheme amounts to a rule for selecting one particular $Q$.
>
> In the bivariate case ($k=2$), all $2\times 2$ orthogonal matrices with determinant $+1$ are plane rotations:
> ``` math
> \begin{equation*}
> Q(\theta) = \begin{bmatrix} \cos\theta & -\sin\theta \\ \sin\theta & \cos\theta \end{bmatrix}, \quad \theta \in [0,2\pi).
> \end{equation*}
> ```
> The single free parameter $\theta$ is exactly the one degree of freedom left unconstrained by the three equations of $\Sigma_u = BB'$. Each identification scheme imposes one additional restriction that pins down $\theta$. In higher dimensions, the space of orthogonal matrices is more complex, but the principle is the same: there are $k(k-1)/2$ free parameters in $Q$ (an orthogonal matrix has $k^2$ entries constrained by $k(k+1)/2$ orthonormality conditions, leaving $k^2 - k(k+1)/2 = k(k-1)/2$ free parameters), and identification requires $k(k-1)/2$ independent restrictions to pin down a unique solution.
>
> **Geometric intuition.** A rotation $Q(\theta)$ acts rigidly on the plane: it turns every vector counterclockwise by angle $\theta$ without altering its length or the angle between any two vectors. The two columns of $B = B_0 Q(\theta)$ are the contemporaneous impact vectors of the structural shocks — they record how a unit shock to each structural disturbance propagates to the $k$ variables at time $t$. Post-multiplying $B_0$ by $Q(\theta)$ spins these two impact vectors together by $\theta$, keeping them the same length and mutually orthogonal. Because $\Sigma_u = BB'$ depends only on lengths and inner products, the covariance matrix is invariant to $\theta$: any orientation of the impact vectors is consistent with the same reduced-form second moments. The identification problem is therefore geometric: the data pins down the shape of the residual covariance ellipse, but not the directions of the structural axes within it. Identification amounts to anchoring those directions — choosing the angle at which the shock axes sit in the space spanned by the reduced-form residuals.

How to solve a system of $3$ equations in $4$ unknowns? As we shall see in Section [sec:ident](04-identification-in-the-var-toolbox.md), the solution is to impose an additional restriction drawn from economic theory — a fourth equation that, together with the three equations in $\Sigma_u = BB'$, uniquely determines $B$ (or, under set identification, narrows the set of admissible $B$ matrices). The toolbox implements seven identification schemes, each of which selects the rotation matrix $Q$, a $k\times k$ orthogonal matrix satisfying $QQ'=I_k$, in $B = B_0 Q$ according to a different principle (see Box that section):

- *Zero contemporaneous restrictions* (Section that section): selected off-diagonal elements of $B$ set to zero at impact (lower-triangular $B$).

- *Zero long-run restrictions* (Section that section): cumulative impulse response of specified variables constrained to zero at infinite horizon.

- *Sign restrictions* (Section that section): sign of specified impulse responses constrained across a set of horizons.

- *Narrative sign restrictions* (Section that section): sign restrictions augmented by constraints on shock realizations at specific historical dates.

- *External instruments* (Section that section): a proxy variable used to isolate one structural shock via IV projection.

- *Combining sign restrictions and external instruments* (Section that section): one or more shocks point-identified via IV, with the remaining shocks set-identified via sign restrictions applied to the orthogonal complement.

- *Identification with exogenous variables* (Section that section): the instrument enters directly as a contemporaneous regressor, with its estimated coefficient vector serving as one column of $B$.

Each scheme is grounded in different economic assumptions about the nature of the shocks; the choice of identification scheme should be guided by those assumptions rather than statistical convenience.

[^1]: The unit-variance normalization is harmless and involves no loss of generality (provided the diagonal elements of $B$ remain unrestricted). An alternative normalization is to leave the variance of the structural innovations unrestricted, $\varepsilon_{it}\sim \mathcal{N}(0,\sigma_i^2)$, and set the diagonal elements of $B$ equal to $1$.

[^2]: The existence of a (finite-order) VAR representation of the DSGE solution requires the structural shocks to be fundamental for the observables, i.e. recoverable from current and past values of the data; see .
