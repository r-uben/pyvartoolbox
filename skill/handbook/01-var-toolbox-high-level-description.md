---
title: "VAR Toolbox: High-Level Description"
label: "sec:intro"
source: VAR Handbook (Cesa-Bianchi)
type: reformatted-extract
licence: GPL-3.0
---

# VAR Toolbox: High-Level Description

> **Source.** This page is a reformatted extract of the *VAR Handbook* by
> Ambrogio Cesa-Bianchi, from the MATLAB VAR Toolbox (https://github.com/ambropo/VAR-Toolbox). The content is
> his; only the format has changed, so that it can be read in fragments by a
> machine. Redistributed under the GPL-3.0 the original carries. Code
> listings are **MATLAB** and do not apply to `pyvartoolbox` — see
> [conventions](../references/conventions.md) for where the APIs differ.

The VAR Toolbox is a collection of MATLAB routines to perform Vector Autoregressive (VAR) analysis. Since their introduction to macroeconomics by , VAR models have remained one of the most important tools in a macroeconometrician’s toolkit. As put it, VAR models can be used to describe the dynamic relations in macroeconomic and financial data, make forecasts, draw inference about the true (but unobserved) structure of the macroeconomy, and advise policymakers.

This handbook explains the workings of VARs through simple examples. Used alongside a formal textbook, it builds intuition that formal instruction alone rarely provides. The exposition alternates between theoretical derivations and their direct MATLAB implementation, so that every result can be reproduced and inspected. The focus is on the core concepts and most commonly used features, leaving aside more advanced functionality.

The VAR Toolbox is transparent and pedagogical: it exposes every step of the computation so users can follow, modify, and extend each routine. In this regard, it differs from more comprehensive toolboxes, such as the Bayesian BEAR toolbox of and the Empirical Macro toolbox of , which both offer broader coverage and greater computational efficiency, perhaps at the cost of transparency.[^1] In terms of scope, the toolbox covers the most commonly used identification schemes and computes impulse responses, forecast error variance decompositions, and historical decompositions. Estimation is equation-by-equation OLS by default; Bayesian techniques are also available.

The origin of the VAR Toolbox traces back to the early days of my PhD, when I was trying to understand the mechanics of VARs by replicating existing papers in the literature. In my experience, replication is key: a method becomes concrete only when you code it yourself. The VAR Toolbox would not exist if it were not for James LeSage’s [Econometrics Toolbox](https://www.spatial-econometrics.com/), which greatly helped my understanding of VARs and econometrics more generally. The main function for the estimation of reduced-form VARs in the VAR Toolbox is a slightly modified version of LeSage’s original function. Relative to LeSage’s Toolbox, the VAR Toolbox is much narrower in scope, focusing on the estimation and structural identification of VAR models. The toolbox has developed over the years with the help of many users, colleagues, and co-authors who made useful suggestions and spotted typos or bugs. I am grateful to all of you.

*Disclaimer*: All files available in the VAR Toolbox are for educational and research purposes only. I take no responsibility or liability for the use of any source code made available here. While the codes have been tested extensively, and despite every effort to ensure they are error-free, some may still contain bugs. If you find any, please email me at <a href="ambrogio.cesabianchi@gmail.com" class="uri">ambrogio.cesabianchi@gmail.com</a> or open an issue on GitHub at <https://github.com/ambropo/VAR-Toolbox>. Whenever the software is used, I would appreciate a citation to this working paper as acknowledgment.

**<u>Getting started</u>.** No installation is required. Simply fork or download the latest version of the toolbox from <https://github.com/ambropo/VAR-Toolbox> to a folder on your hard drive. The only required step is to add the relevant subfolders to the MATLAB path. The code below adds each subfolder explicitly rather than using . This is safer as it avoids polluting the path with unneeded functions. It is good practice to remove the toolbox from the path at the end of each script to avoid clashes with other functions:

``` matlab
root = fileparts(fileparts(mfilename('fullpath')));

% Add each relevant subfolder explicitly
addpath(fullfile(root, 'VAR'));
addpath(fullfile(root, 'Figure'));
addpath(fullfile(root, 'Stats'));
addpath(fullfile(root, 'Utils'));
addpath(fullfile(root, 'Primer'));
addpath(fullfile(root, 'Auxiliary'));
disp('VAR Toolbox 4.0 path set.');
 .
 .
% Remove the toolbox from the path at the end of the script 
rmpath(genpath(root))
```

The files are grouped into eight categories, each stored in its own subfolder within the root folder (to which all folder references in this handbook are relative):

- : codes for VAR analysis, including estimation, identification, impulse response functions, forecast error variance decompositions, historical decompositions, etc.

- : codes for commonly used descriptive statistics, e.g. moving-window averages or sums, pairwise correlations, etc.

- : utility codes that support the smooth functioning of the toolbox, e.g. functions to vectorize matrices, manage variable naming conventions, or format numerical output.

- : codes borrowed from other public sources. Each m-file contains a reference to the original source.

- : codes for plotting high-quality figures, particularly suited for time series data, e.g. functions to control dates on the horizontal axis, customize legends, or plot charts with shaded error bands.

- : the primer script () that reproduces the worked examples used throughout this handbook, demonstrating VAR estimation, the identification schemes, and local projections.

- : replication scripts for published empirical papers in the VAR literature, each stored in its own subfolder named after the paper.

- : a self-contained empirical exercise accompanying the handbook.

The current version of the toolbox is 4.0, available at <https://github.com/ambropo/VAR-Toolbox>. The VAR Toolbox 4.0 has been tested with MATLAB R2022b on macOS 26 (Apple Silicon, arm64). Older versions of the toolbox are available at <https://sites.google.com/site/ambropo/>.

The remainder of this handbook is organized as follows. Section [sec:overview](02-a-brief-overview-of-var-models.md) provides a concise, software-free introduction to VAR models: the reduced-form and structural representations, the moving-average (Wold) representation, the stability condition, and the identification problem. Section [sec:rfvar_toolbox](03-var-estimation-in-the-var-toolbox.md) turns to estimation in the VAR Toolbox: loading and preparing the data, OLS estimation of the reduced-form VAR, and verification of stability. Section [sec:ident](04-identification-in-the-var-toolbox.md) covers seven identification schemes in detail: zero contemporaneous restrictions, zero long-run restrictions, sign restrictions, narrative sign restrictions, external instruments, combined sign-IV restrictions, and identification with exogenous variables. Section [sec:inference](05-statistical-inference.md) introduces bootstrap and Bayesian inference procedures for quantifying uncertainty around structural impulse responses, variance decompositions, and historical decompositions. Section [sec:dynamic](06-structural-dynamic-analysis.md) develops the three main tools of structural dynamic analysis: impulse response functions, forecast error variance decompositions, and historical decompositions. Section [sec:lp](07-local-projections.md) introduces local projections as an alternative estimator of impulse responses. The Appendix presents six empirical replications that put these methods to work.

[^1]: Other toolboxes covering similar topics include the Econometrics Toolbox of , the Dynare project , the Global VAR Toolbox , and the mixed-frequency state-space toolbox of .
