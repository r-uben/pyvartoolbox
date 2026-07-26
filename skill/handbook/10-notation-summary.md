---
title: "Notation Summary"
label: "sec:notation"
source: VAR Handbook (Cesa-Bianchi)
type: reformatted-extract
licence: GPL-3.0
---

# Notation Summary

> **Source.** This page is a reformatted extract of the *VAR Handbook* by
> Ambrogio Cesa-Bianchi, from the MATLAB VAR Toolbox (https://github.com/ambropo/VAR-Toolbox). The content is
> his; only the format has changed, so that it can be read in fragments by a
> machine. Redistributed under the GPL-3.0 the original carries. Code
> listings are **MATLAB** and do not apply to `pyvartoolbox` — see
> [conventions](../references/conventions.md) for where the APIs differ.

The table below lists the main mathematical symbols used in this handbook, their dimensions, the section where each is first defined, and their MATLAB counterpart where applicable. Scalars are dimensionless; all vectors are column vectors unless otherwise noted.

<div class="minipage">

<div class="center">

<div id="tab:notation">

| Symbol | Dimension | First defined | MATLAB |
|:---|:---|:---|:---|
| $k$ | scalar | § that section |  |
| $p$ | scalar | § that section |  |
| $T$ | scalar | § that section |  |
| $t$ | scalar (time index) | § that section | — |
| $h$ | scalar (horizon) | § that section |  |
| $x_t$ | $k\times 1$ | § that section |  |
| $c$ | $k\times 1$ (intercept) | § that section | ($=1$) |
| $\Phi_j$ | $k\times k$ (lag-$j$ coeff.) | § that section |  |
| $\mathcal{F}$ | $kp\times kp$ (companion) | § that section |  |
| $u_t$ | $k\times 1$ (residuals) | § that section |  |
| $\Sigma_u$ | $k\times k$ | § that section |  |
| $B$ | $k\times k$ (impact matrix) | § that section |  |
| $\varepsilon_t$ | $k\times 1$ (struct. shocks) | § that section | — |
| $P$ | $k\times k$ (Cholesky of $\Sigma_u$) | § that section | — |
| $P_\Omega$ | $k\times k$ (Cholesky of $\Omega$) | § that section | — |
| $Q$ | $k\times k$ (rotation) | § that section | — |
| $\Omega$ | $k\times k$ (long-run cov.) | § that section | — |
| $C$ | $k\times k$ (long-run impact) | § that section | — |
| $IR_h = \Theta_h$ | $k\times k$ | § that section |  |
| $z_t$ | scalar or $k_z\times 1$ (external instrument) | § that section, § [sec:lp](07-local-projections.md) |  |
| $\delta$ | $k\times 1$ (exog. coeff.) | § that section | — |
| $s_t$ | scalar (shock, enters directly) | § that section, § [sec:lp](07-local-projections.md) | , |
| $d_t$ | scalar (endog. treatment, LP-IV) | § [sec:lp](07-local-projections.md) |  |
| $H$ | scalar (max LP horizon) | § [sec:lp](07-local-projections.md) |  |
| $\beta_h$ | scalar (LP coefficient at horizon $h$) | § [sec:lp](07-local-projections.md) |  |
| $x_{i,t+h}$ | scalar ($i$-th LP outcome at horizon $h$) | § [sec:lp](07-local-projections.md) |  |
| $w_t$ | $n_w\times 1$ (LP control vector) | § [sec:lp](07-local-projections.md) |  |
| $e_{t+h}$ | scalar (LP regression error) | § [sec:lp](07-local-projections.md) | — |

<span class="smallcaps">Notation Summary</span>

</div>

</div>

<span class="smallcaps">Note.</span> The companion matrix $\mathcal{F}$ is $kp\times kp$: the upper $k$ rows collect $[\Phi_1,\ldots,\Phi_p]$ and the lower $k(p-1)$ rows form the identity-shift block $[I_{k(p-1)},\,0]$ (see Box that section). The impulse response matrix $IR_h = \Theta_h = \Phi^h B$ for a VAR(1); for a general VAR($p$), replace $\Phi^h B$ with $\mathcal{F}^h \mathcal{B}$ where $\mathcal{F}$ is the companion matrix and $\mathcal{B}$ is the impact matrix $B$ padded with zeros to dimension $kp\times k$ (see Box that section). <span id="tab:notation" label="tab:notation"></span>

</div>
