# MATLAB shims for fixture generation

`LPmodel.m` calls `zscore` and `norminv`, both of which live in the Statistics
and Machine Learning Toolbox. On a MATLAB installation without that toolbox
licensed, local projections cannot run at all.

These two files supply exact standard definitions so that `make_fixtures.m`
works on a base MATLAB licence:

- `norminv(p) = mu + sigma*sqrt(2)*erfinv(2p-1)` — an identity, using `erfinv`
  from base MATLAB.
- `zscore(x) = (x - mean(x)) / std(x, 0)` — MATLAB's documented default
  (normalisation by `N-1`).

They shadow the toolbox versions only while the generator runs. If you *do* have
the Statistics toolbox, delete the `addpath` line in `make_fixtures.m` and the
fixtures will be identical — that is the point of using exact definitions rather
than approximations.
