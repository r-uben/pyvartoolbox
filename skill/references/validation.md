# What "validated" means here

Be precise about this when reporting results. The claims differ by scheme, and
overstating them would be worse than making none.

## Validated exactly against MATLAB VAR Toolbox 4.0

Reference values were produced by running the upstream toolbox on its own
replication datasets and are committed under `tests/fixtures/`, so CI reproduces
the comparison without a MATLAB licence.

| Replication | Scheme | Agreement |
| --- | --- | --- |
| Stock-Watson (2001) | Cholesky | 1e-10 to 1e-12 |
| Blanchard-Quah (1989) | long-run zero | 1e-10 to 1e-12 |
| Gertler-Karadi (2015) | proxy SVAR | 1e-7 |
| Jordà-Taylor (2025) | local projections, OLS | 1e-9 |
| Jordà-Taylor (2025) | local projections, IV | 1e-8, incl. first-stage F |

Historical decompositions are validated on the first three at the same
tolerances. The Gertler-Karadi tolerance is a conditioning floor, not slack —
see `conventions.md`.

## Validated more weakly, by necessity

Uhlig (2005) and Antolín-Díaz & Rubio-Ramírez (2018) are rejection samplers.
Their acceptance sequence depends on an RNG stream numpy cannot reproduce, so
draw-for-draw agreement is impossible.

Instead the fixtures hold the impact matrices MATLAB **accepted**, and the tests
check that our acceptance predicate accepts every one, that our impulse
responses from those same matrices reproduce MATLAB's to 1e-8, and that both
narrative constraints bind. That validates everything except the random number
generator — but it is **not** equivalent to the rows above. Say so.

## Not fixture-validated at all

Bootstrap bands, posterior draws and rotation sampling consume random streams.
They are tested through distributional properties instead: Haar uniformity of
the rotations, the Wishart mean and variance formulas, that the coefficient draw
reproduces `Σ ⊗ (X'X)⁻¹`, and that posterior bands are strictly wider than
identification-only bands.

## Replications run end to end

All six exercises run from a clean install via `pyvartoolbox-replicate`, and the
test suite asserts each paper's qualitative finding — funds rate up with output
and prices down under a contractionary shock; no permanent output effect from
the demand shock; narrative constraints tightening the set. That catches wiring
errors (wrong column, flipped shock, misaligned instrument) which numerical
agreement with a reference cannot.

## Known divergences from the original methods

1. **Narrative restrictions** use upstream's rejection filter, not the
   importance weighting of Antolín-Díaz & Rubio-Ramírez. Same posterior support,
   different shape. Results will not reproduce the paper's figures.
2. **No bootstrap bias correction.** Neither does upstream.
3. **Lag-order selection is not implemented.** Use `statsmodels`.

## How to phrase it

Good: "point estimates match the reference MATLAB implementation to 1e-10;
sampler-based intervals are reproducible under a fixed seed but not across
implementations."

Not good: "verified" or "identical to MATLAB", unqualified.
