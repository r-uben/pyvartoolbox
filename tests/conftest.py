import numpy as np
import pytest


def simulate_var(A, c, sigma, nobs, seed=0, burn=500):
    """Draw a sample from a known Gaussian VAR(p). ``A`` is (p, k, k)."""
    rng = np.random.default_rng(seed)
    p, k, _ = A.shape
    chol = np.linalg.cholesky(sigma)
    u = rng.standard_normal((nobs + burn, k)) @ chol.T
    y = np.zeros((nobs + burn, k))
    for t in range(p, nobs + burn):
        y[t] = c + u[t]
        for j in range(p):
            y[t] += A[j] @ y[t - j - 1]
    return y[burn:]


@pytest.fixture
def var1():
    """A stable bivariate VAR(1) with correlated innovations."""
    A = np.array([[[0.5, 0.1], [0.2, 0.4]]])
    c = np.array([0.3, -0.2])
    sigma = np.array([[1.0, 0.4], [0.4, 2.0]])
    return A, c, sigma


@pytest.fixture
def y_var1(var1):
    A, c, sigma = var1
    return simulate_var(A, c, sigma, nobs=4000, seed=7)


@pytest.fixture
def y_small(var1):
    """Short sample: enough to estimate, small enough for a fast bootstrap."""
    A, c, sigma = var1
    return simulate_var(A, c, sigma, nobs=200, seed=11)
