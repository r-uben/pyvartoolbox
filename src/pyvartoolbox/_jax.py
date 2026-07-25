"""JAX backend for the bootstrap loop.

Optional. The numpy path in :mod:`pyvartoolbox.bootstrap` stays the reference
implementation; this module exists only to make ``nboot`` large affordable, by
``vmap``-ing the resample-simulate-reestimate-IRF chain over draws instead of
looping in Python.

Two deliberate design choices:

- **Resample indices are generated in numpy and passed in.** Sharing the draws
  makes the two backends exactly comparable, which is what lets the tests assert
  agreement to 1e-10 rather than merely comparing distributions.
- **float64 is forced at import.** JAX defaults to float32, which silently
  destroys long-horizon impulse responses: the companion recursion compounds the
  error, and long-run restrictions run through an explicit inverse.

Only ``chol`` and ``longrun`` identification are supported here. ``iv`` depends
on instrument sample alignment that is not worth expressing as a traced
computation; :func:`pyvartoolbox.bootstrap.bootstrap_irf` falls back to numpy.
"""

from __future__ import annotations

import numpy as np

JAX_SCHEMES = ("chol", "longrun")


def available() -> bool:
    """True if JAX is importable."""
    try:
        import jax  # noqa: F401
    except ImportError:
        return False
    return True


def _setup():
    import jax

    # Must happen before any array is created, hence at call time rather than
    # relying on the caller.
    jax.config.update("jax_enable_x64", True)
    import jax.numpy as jnp

    return jax, jnp


def bootstrap_draws(
    model,
    horizon: int,
    ident: str,
    indices: np.ndarray | None,
    signs: np.ndarray | None,
) -> tuple[np.ndarray, np.ndarray]:
    """Run the bootstrap replications under JAX.

    Exactly one of ``indices`` (residual resampling) and ``signs`` (wild) is
    given, each ``(nboot, neff)``. Returns ``(irfs, max_eigs)`` as numpy arrays
    of shape ``(nboot, horizon+1, nvar, nshock)`` and ``(nboot,)``; the caller
    applies the stability mask and percentiles.
    """
    if ident not in JAX_SCHEMES:
        raise ValueError(
            f"the JAX backend supports {JAX_SCHEMES}, not {ident!r}; "
            "use backend='numpy'"
        )
    jax, jnp = _setup()

    k, p = model.nvar, model.nlags
    neff = model.neff
    A = jnp.asarray(model.ar_coefs)
    dcoef = jnp.asarray(model.det_coefs)
    extra = jnp.asarray(model.X[:, k * p :])
    y0 = jnp.asarray(model.y[:p])
    resid = jnp.asarray(model.resid)
    dof = neff - model.ncoef if model.dof_adjust else neff

    def simulate(u):
        def step(buf, inputs):
            ut, xt = inputs
            val = ut + jnp.einsum("jab,jb->a", A, buf[::-1])
            val = val + dcoef @ xt
            return jnp.concatenate([buf[1:], val[None]]), val

        _, path = jax.lax.scan(step, y0, (u, extra))
        return jnp.concatenate([y0, path])

    def fit(ys):
        n = ys.shape[0]
        lags = jnp.hstack([ys[p - j : n - j] for j in range(1, p + 1)])
        X = jnp.hstack([lags, extra])
        Y = ys[p:]
        beta = jnp.linalg.lstsq(X, Y, rcond=None)[0]
        r = Y - X @ beta
        sigma = (r.T @ r) / dof
        ar = beta[: k * p].reshape(p, k, k).transpose(0, 2, 1)
        return ar, sigma

    def companion(ar):
        F = jnp.zeros((k * p, k * p))
        F = F.at[:k].set(jnp.hstack(list(ar)))
        if p > 1:
            F = F.at[k:, : k * (p - 1)].set(jnp.eye(k * (p - 1)))
        return F

    def wold(ar):
        psi = [jnp.eye(k)]
        for h in range(1, horizon + 1):
            acc = jnp.zeros((k, k))
            for j in range(1, min(h, p) + 1):
                acc = acc + ar[j - 1] @ psi[h - j]
            psi.append(acc)
        return jnp.stack(psi)

    def impact(ar, sigma):
        if ident == "chol":
            return jnp.linalg.cholesky(sigma)
        lr = jnp.eye(k) - ar.sum(axis=0)
        C1 = jnp.linalg.inv(lr)
        return jnp.linalg.solve(C1, jnp.linalg.cholesky(C1 @ sigma @ C1.T))

    def one(u):
        ar, sigma = fit(simulate(u))
        irf = wold(ar) @ impact(ar, sigma)
        eig = jnp.max(jnp.abs(jnp.linalg.eigvals(companion(ar))))
        return irf, eig

    if indices is not None:
        u_all = jnp.asarray(resid)[jnp.asarray(indices)]
    else:
        u_all = jnp.asarray(resid)[None] * jnp.asarray(signs)[:, :, None]

    irfs, eigs = jax.jit(jax.vmap(one))(u_all)
    return np.asarray(irfs), np.asarray(eigs)
