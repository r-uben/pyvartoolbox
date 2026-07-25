"""Lag-matrix construction: the Y = X B + U layout shared by every estimator.

Mirrors ``VARmakelags.m`` / ``VARmakexy.m`` from the MATLAB VAR Toolbox, with one
deliberate difference: the deterministic block is appended *after* the lags
rather than prepended, so that ``beta[: nvar * nlags]`` is always the
autoregressive part regardless of which deterministic terms are present.
"""

from __future__ import annotations

import numpy as np

# Deterministic specifications, following VARoption.m's `const` field.
DET_NONE = 0
DET_CONST = 1
DET_TREND = 2
DET_TREND2 = 3

_DET_NAMES = {
    DET_NONE: (),
    DET_CONST: ("const",),
    DET_TREND: ("const", "trend"),
    DET_TREND2: ("const", "trend", "trend2"),
}


def make_lags(y: np.ndarray, nlags: int) -> np.ndarray:
    """Stack ``nlags`` lags of ``y`` side by side.

    Returns an ``(nobs - nlags, nvar * nlags)`` array whose row ``t`` holds
    ``[y_{t-1}, y_{t-2}, ..., y_{t-nlags}]``, each block ``nvar`` wide.
    """
    y = np.asarray(y, dtype=float)
    if y.ndim != 2:
        raise ValueError(f"y must be 2-D (nobs, nvar), got shape {y.shape}")
    nobs, nvar = y.shape
    if nlags < 1:
        raise ValueError(f"nlags must be >= 1, got {nlags}")
    if nobs <= nlags:
        raise ValueError(f"need more than nlags={nlags} observations, got {nobs}")

    return np.hstack([y[nlags - k : nobs - k] for k in range(1, nlags + 1)])


def make_xy(
    y: np.ndarray,
    nlags: int,
    det: int = DET_CONST,
    exog: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """Build the regressand ``Y`` and regressor ``X`` of the reduced-form VAR.

    Column order of ``X`` is ``[lags | exog | deterministic]``. Returns
    ``(Y, X, names)`` where ``names`` labels the non-autoregressive columns.
    """
    y = np.asarray(y, dtype=float)
    if det not in _DET_NAMES:
        raise ValueError(f"det must be one of {sorted(_DET_NAMES)}, got {det}")

    nobs = y.shape[0]
    Y = y[nlags:]
    blocks = [make_lags(y, nlags)]
    names: list[str] = []

    if exog is not None:
        exog = np.asarray(exog, dtype=float)
        if exog.ndim == 1:
            exog = exog[:, None]
        if exog.shape[0] != nobs:
            raise ValueError(
                f"exog has {exog.shape[0]} rows, expected {nobs} to align with y"
            )
        blocks.append(exog[nlags:])
        names += [f"exog{i + 1}" for i in range(exog.shape[1])]

    # Trend is indexed on the estimation sample so that it starts at 1, matching
    # the MATLAB toolbox rather than the position within the raw series.
    neff = Y.shape[0]
    trend = np.arange(1, neff + 1, dtype=float)[:, None]
    det_cols = {
        "const": np.ones((neff, 1)),
        "trend": trend,
        "trend2": trend**2,
    }
    for name in _DET_NAMES[det]:
        blocks.append(det_cols[name])
        names.append(name)

    return Y, np.hstack(blocks), names
