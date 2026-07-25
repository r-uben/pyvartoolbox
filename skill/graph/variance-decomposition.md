---
type: object
handbook: "§6.2"
implemented_by: VARmodel.vd
---

# Forecast error variance decomposition

Share of the `h`-step forecast error variance of each variable attributable to
each shock: cumulated squared [[impulse-response]] over total.

Shares sum to one across shocks — **only under a fully identifying scheme**.
Under [[proxy-svar]] one column is meaningful and the rest are returned as zero,
so they do not.

This package returns shares in `[0,1]`; upstream returns percent, and indexes
`(h, shock, variable)` where we use `(h, variable, shock)`.

## Relations

- derived from → [[impulse-response]]
- degenerate under → [[proxy-svar]]
