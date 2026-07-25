"""Posterior draws of the VAR coefficients (port of ``VARdrawpost.m``).

Flat (Jeffreys) prior, so the posterior is Normal-inverse-Wishart centred on the
OLS estimates:

    sigma^-1 ~ Wishart(sigma_hat^-1 / nobs, nobs)
    vec(B) | sigma ~ N(vec(B_hat), sigma (X'X)^-1)

Used to combine parameter uncertainty with the identification uncertainty of
set-identified schemes. Without this, sign-restriction bands describe only the
spread of the identified set at fixed coefficients.
"""

from __future__ import annotations

import copy

import numpy as np


def wishart(scale: np.ndarray, df: int, rng: np.random.Generator) -> np.ndarray:
    """Draw from a Wishart distribution with mean ``df * scale``.

    Bartlett decomposition: numpy has no Wishart sampler, and building one from
    ``df`` multivariate normal draws costs ``O(df n^2)`` where this costs
    ``O(n^3)`` — a real difference when ``df`` is the sample size.
    """
    n = scale.shape[0]
    if df < n:
        raise ValueError(
            f"Wishart degrees of freedom ({df}) must be at least the dimension "
            f"({n}) for the draw to be non-singular"
        )
    L = np.linalg.cholesky(scale)
    A = np.zeros((n, n))
    # Diagonal: sqrt of chi-square with declining degrees of freedom.
    A[np.diag_indices(n)] = np.sqrt(rng.chisquare(df - np.arange(n)))
    tril = np.tril_indices(n, -1)
    A[tril] = rng.standard_normal(len(tril[0]))
    LA = L @ A
    return LA @ LA.T


def draw_posterior(model, rng: np.random.Generator):
    """Return a copy of ``model`` with coefficients and covariance redrawn.

    The returned object behaves like the fitted model — ``ar_coefs``,
    ``companion()``, ``wold()``, ``irf()`` all work — but represents one draw
    from the posterior rather than the point estimate.
    """
    X = model.X
    nobs = model.neff
    k, nvar = model.beta.shape

    sigma_draw = np.linalg.inv(
        wishart(np.linalg.inv(model.sigma) / nobs, nobs, rng)
    )

    # vec(beta) ~ N(vec(beta_hat), sigma ⊗ (X'X)^-1). Sampling as
    # beta_hat + Lx Z Ls' gives exactly that covariance without ever forming the
    # (k*nvar)^2 Kronecker matrix.
    XtXi = np.linalg.inv(X.T @ X)
    Lx = np.linalg.cholesky((XtXi + XtXi.T) / 2)
    Ls = np.linalg.cholesky((sigma_draw + sigma_draw.T) / 2)
    Z = rng.standard_normal((k, nvar))
    beta_draw = model.beta + Lx @ Z @ Ls.T

    drawn = copy.copy(model)
    drawn.beta = beta_draw
    drawn.sigma = sigma_draw
    drawn.resid = model.Y - X @ beta_draw
    return drawn
