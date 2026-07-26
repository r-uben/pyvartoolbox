---
title: "Data Sources"
label: "sec:data"
source: VAR Handbook (Cesa-Bianchi)
type: reformatted-extract
licence: GPL-3.0
---

# Data Sources

> **Source.** This page is a reformatted extract of the *VAR Handbook* by
> Ambrogio Cesa-Bianchi, from the MATLAB VAR Toolbox (https://github.com/ambropo/VAR-Toolbox). The content is
> his; only the format has changed, so that it can be read in fragments by a
> machine. Redistributed under the GPL-3.0 the original carries. Code
> listings are **MATLAB** and do not apply to `pyvartoolbox` — see
> [conventions](../references/conventions.md) for where the APIs differ.

The spreadsheet , located in , contains the two US time series used in the main text at quarterly frequency. The sample period is 1989:Q1 to 2019:Q4 ($T=124$ observations). All series are downloaded from FRED (Federal Reserve Bank of St. Louis).

- **Real GDP** (`gdp`): Real Gross Domestic Product, seasonally adjusted annual rate (GDPC1). Source: Bureau of Economic Analysis.

- **1-year Treasury Bill Yield** (`i1yr`): Market Yield on US Treasury Securities at 1-Year Constant Maturity (GS1). Source: Board of Governors of the Federal Reserve System.

The baseline VAR example in the main text uses two transformed series: the log-difference of US real GDP (scaled by 100, denoted $y_t$) and the level of the 1-year Treasury Bill yield (denoted $r_t$).

The replication applications in Section [sec:applications](11-applications-and-replications.md) use separate datasets not covered here. These have been downloaded from the replication folders available online for each original paper and are stored in alongside the corresponding replication scripts. Each script () identifies the data source at the top of the file.
