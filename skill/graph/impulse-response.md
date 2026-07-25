---
type: object
handbook: "§6.1"
implemented_by: VARmodel.irf
---

# Impulse response function

`Θ_h = Ψ_h B`. In this package `irf[h, i, j]` is the response of variable `i` at
horizon `h` to shock `j`.

Shocks are one standard deviation by default. Horizon `h` gives `h+1` rows,
covering `0..h` — upstream's `nsteps = H` covers `0..H-1`.

## Relations

- requires → [[wold-representation]] and a `B` from [[identification-problem]]
- aggregates into → [[variance-decomposition]]
- band meaning depends on → [[point-vs-set-identification]]
