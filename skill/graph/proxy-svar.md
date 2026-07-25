---
type: scheme
handbook: "§4.5"
identifies: one shock
call: 'ident="iv", iv=z'
---

# Proxy SVAR / external instruments

An observed instrument `z_t` correlated with the shock of interest and with no
other structural shock. Two-stage: project the first reduced-form residual on
`z`, regress the remaining residuals on the fitted values, scale by the shock
size (Gertler-Karadi footnote 4).

**Identifies only the first shock.** Other columns are returned as zeros — that
is correct reporting, not missing data.

The advantage over [[cholesky-identification]] is that it needs no ordering
assumption among the other variables, and it typically removes the
[[price-puzzle]]. It still requires choosing which variable is instrumented, so
put that variable first.

Check instrument strength — see [[weak-instruments]].

## Relations

- alternative to → [[cholesky-identification]]
- fixes → [[price-puzzle]]
- vulnerable to → [[weak-instruments]]
- combines with signs in → [[sign-plus-iv]]
