---
type: pitfall
severity: high
---

# The price puzzle

Prices *rising* after a contractionary monetary shock — the opposite of theory.

Almost always a symptom of misidentification rather than an economic finding.
The standard diagnosis is that a recursive ordering
([[cholesky-identification]]) fails to capture the central bank's information
set: the policy rate responds to expected inflation the econometrician has not
conditioned on.

Historical fixes: add commodity prices as a proxy for expected inflation; or
abandon the ordering and use [[proxy-svar]], which is the modern answer and the
motivation for high-frequency instruments.

Seeing it should prompt re-examination of the identification, not a footnote.

## Relations

- symptom of → [[cholesky-identification]] misspecification
- resolved by → [[proxy-svar]]
- visible in → the Gertler-Karadi replication comparison
