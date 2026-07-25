---
type: scheme
handbook: "§4.1"
identifies: all shocks
call: 'ident="chol"'
---

# Cholesky (zero contemporaneous restrictions)

`B` is the lower-triangular Cholesky factor of `Σ_u`. Imposes a recursive
ordering: variable 1 is unaffected within the period by every other shock.

**Exactly identifying, which is the danger.** It never fails visibly — a
badly-chosen ordering yields a clean, confident, wrong answer. The usual symptom
in monetary VARs is the [[price-puzzle]].

Ask what ordering is being asserted and why. "It was the column order of the
spreadsheet" is not an identifying assumption.

## Relations

- resolves → [[identification-problem]] by fiat
- symptom of failure → [[price-puzzle]]
- superseded in practice by → [[proxy-svar]] when an instrument exists
- is → [[point-vs-set-identification|point-identified]]
