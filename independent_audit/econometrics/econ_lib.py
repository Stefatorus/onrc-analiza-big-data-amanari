"""Mic motor econometric în numpy: OLS / 2SLS cu efecte fixe absorbite (proiecții alternante, MAP),
erori standard robuste la clustere (CR1, convenția Stata/reghdfe), F de prima etapă (Kleibergen-Paap
pentru un singur instrument = t^2 robust), interval Anderson-Rubin robust la instrument slab.

Testat pe date simulate în test_econ_lib.py (acoperire ~95%, comparație cu statsmodels).
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from scipy import stats


def _codes(fe: pd.DataFrame | None, n: int):
    if fe is None or fe.shape[1] == 0:
        return []
    return [pd.factorize(fe[c], sort=False)[0] for c in fe.columns]


def demean(X: np.ndarray, codes, tol=1e-10, maxit=500) -> np.ndarray:
    """Within-transform X by several sets of fixed effects (method of alternating projections)."""
    X = np.array(X, dtype=float, copy=True)
    if X.ndim == 1:
        X = X[:, None]
    if not codes:
        return X - X.mean(0)
    counts = [np.bincount(c).astype(float) for c in codes]
    for _ in range(maxit):
        old = X.copy()
        for c, k in zip(codes, counts):
            sums = np.zeros((k.size, X.shape[1]))
            np.add.at(sums, c, X)
            X -= (sums / k[:, None])[c]
        if np.max(np.abs(X - old)) < tol * (1 + np.max(np.abs(X))):
            break
    return X


def _absorbed_dof(codes, cluster_codes):
    """Levels of absorbed FE, excluding FE sets nested within clusters (reghdfe convention), minus redundancies."""
    k = 0
    for c in codes:
        nested = False
        if cluster_codes is not None:
            # FE nested in cluster if every FE level maps to a single cluster
            pairs = pd.DataFrame({"f": c, "g": cluster_codes}).drop_duplicates()
            nested = pairs.f.duplicated().sum() == 0
        k += 0 if nested else (c.max() + 1) - 1
    return k


def _cluster_vcov(Xh: np.ndarray, u: np.ndarray, bread: np.ndarray, g: np.ndarray, k_total: int):
    n = Xh.shape[0]
    G = g.max() + 1
    scores = np.zeros((G, Xh.shape[1]))
    np.add.at(scores, g, Xh * u[:, None])
    meat = scores.T @ scores
    adj = G / (G - 1) * (n - 1) / max(n - k_total, 1)
    return adj * bread @ meat @ bread, G


def _vc(Xh, u, bread, gs, k_total):
    """One- or two-way cluster-robust vcov (Cameron-Gelbach-Miller). u may be (n,) or (n,m) for joint vcov."""
    if len(gs) == 1:
        V, G = _cluster_vcov_multi(Xh, u, bread, gs[0], k_total)
        return V, G
    g1, g2 = gs
    g12 = pd.factorize(pd.Series(g1).astype(str) + "_" + pd.Series(g2).astype(str))[0]
    V1, G1 = _cluster_vcov_multi(Xh, u, bread, g1, k_total)
    V2, G2 = _cluster_vcov_multi(Xh, u, bread, g2, k_total)
    V3, _ = _cluster_vcov_multi(Xh, u, bread, g12, k_total)
    V = V1 + V2 - V3
    if np.any(np.diag(V) <= 0):   # CGM can be non-PSD: fall back to the larger one-way vcov (conservative)
        V = V1 if np.trace(V1) >= np.trace(V2) else V2
    return V, min(G1, G2)


def _cluster_vcov_multi(Xh, u, bread, g, k_total):
    u = u[:, None] if u.ndim == 1 else u
    n, p = Xh.shape
    m = u.shape[1]
    G = g.max() + 1
    S = np.zeros((G, p * m))
    for k in range(m):
        tmp = np.zeros((G, p))
        np.add.at(tmp, g, Xh * u[:, k:k + 1])
        S[:, k * p:(k + 1) * p] = tmp @ bread          # bread is symmetric
    adj = G / (G - 1) * (n - 1) / max(n - k_total, 1)
    return adj * S.T @ S, G


def fit(y, exog: dict, fe: pd.DataFrame | None, cluster, endog: str | None = None,
        instr: dict | None = None, cluster2=None):
    """y: array, or dict {name: array} of outcomes sharing the design (then returns {name: result} plus
    joint vcov of the `endog`/first coefficient across outcomes in result['_joint']).
    exog: {name: array} included regressors (incl. the endogenous one named `endog`);
    instr: {name: array} excluded instruments (2SLS if given). cluster2: optional second cluster dim."""
    multi = isinstance(y, dict)
    ynames = list(y) if multi else ["y"]
    Y = np.column_stack([np.asarray(y[k] if multi else y, float) for k in ynames])
    names = list(exog)
    X = np.column_stack([np.asarray(exog[k], float) for k in names])
    ok = np.isfinite(Y).all(1) & np.isfinite(X).all(1)
    Z = None
    if instr:
        Z = np.column_stack([np.asarray(instr[k], float) for k in instr])
        ok &= np.isfinite(Z).all(1)
    cl = np.asarray(cluster)
    ok &= pd.notna(cl)
    if cluster2 is not None:
        ok &= pd.notna(np.asarray(cluster2))
    Y, X, cl = Y[ok], X[ok], cl[ok]
    fe_ok = fe.loc[ok] if fe is not None else None
    if Z is not None:
        Z = Z[ok]
    codes = _codes(fe_ok, len(Y))
    g = pd.factorize(cl)[0]
    gs = [g] if cluster2 is None else [g, pd.factorize(np.asarray(cluster2)[ok])[0]]
    Yd = demean(Y, codes)
    Xd = demean(X, codes)
    n = len(Yd)
    kfe = _absorbed_dof(codes, g)
    base = dict(n=int(n), names=names, clusters=int(min(x.max() + 1 for x in gs)),
                two_way=cluster2 is not None)
    if Z is None:
        bread = np.linalg.pinv(Xd.T @ Xd)
        B = bread @ Xd.T @ Yd
        U = Yd - Xd @ B
        Xh = Xd
        base.update(method="OLS")
    else:
        Zd = demean(Z, codes)
        exo_idx = [i for i, k in enumerate(names) if k != endog]
        W = np.column_stack([Zd, Xd[:, exo_idx]])
        j = names.index(endog)
        WtW_inv = np.linalg.pinv(W.T @ W)
        pi = WtW_inv @ W.T @ Xd[:, j]
        v = Xd[:, j] - W @ pi
        Vfs, _ = _vc(W, v, WtW_inv, gs, W.shape[1] + kfe)
        nz = Z.shape[1]
        pz, Vz = pi[:nz], Vfs[:nz, :nz]
        F = float(pz @ np.linalg.solve(Vz, pz) / nz)
        Xh = W @ (WtW_inv @ W.T @ Xd)
        bread = np.linalg.pinv(Xh.T @ Xd)
        B = bread @ Xh.T @ Yd
        U = Yd - Xd @ B
        bread = np.linalg.pinv(Xh.T @ Xh)
        base.update(method="2SLS", first_stage=dict(coef=pz.tolist(), se=np.sqrt(np.diag(Vz)).tolist(),
                                                    F_cluster_robust=F, instruments=list(instr)))
    Vall, G = _vc(Xh, U, bread, gs, Xd.shape[1] + kfe)
    p = Xd.shape[1]
    dfree = G - 1
    tcrit = stats.t.ppf(.975, dfree)
    results = {}
    for m, yn in enumerate(ynames):
        b = B[:, m]
        V = Vall[m * p:(m + 1) * p, m * p:(m + 1) * p]
        se = np.sqrt(np.maximum(np.diag(V), 0))
        r = dict(base)
        r.update(coef=dict(zip(names, b)), se=dict(zip(names, se)),
                 ci95={k: (b[i] - tcrit * se[i], b[i] + tcrit * se[i]) for i, k in enumerate(names)},
                 p={k: float(2 * stats.t.sf(abs(b[i] / se[i]), dfree)) if se[i] > 0 else np.nan
                    for i, k in enumerate(names)},
                 vcov=V, mean_y=float(np.mean(Y[:, m])), sd_y=float(np.std(Y[:, m])), dof=int(dfree))
        if Z is not None:
            r["_ar"] = (Yd[:, m], Xd, j, Zd, exo_idx, gs, kfe)
        results[yn] = r
    if not multi:
        return results["y"]
    key = names.index(endog) if endog else 0
    idx = [m * p + key for m in range(len(ynames))]
    results["_joint"] = dict(outcomes=ynames, term=names[key], coef=B[key, :], vcov=Vall[np.ix_(idx, idx)])
    return results


def ar_pvalue(res, b0):
    """Cluster-robust Anderson-Rubin test of H0: beta = b0 (single endogenous regressor)."""
    yd, Xd, j, Zd, exo_idx, gs, kfe = res["_ar"]
    W = np.column_stack([Zd, Xd[:, exo_idx]])
    WtW_inv = np.linalg.pinv(W.T @ W)
    nz = Zd.shape[1]
    r = yd - b0 * Xd[:, j]
    c = WtW_inv @ W.T @ r
    u = r - W @ c
    V, G = _vc(W, u, WtW_inv, gs, W.shape[1] + kfe)
    stat = float(c[:nz] @ np.linalg.solve(V[:nz, :nz], c[:nz]) / nz)
    return float(stats.f.sf(stat, nz, G - 1))


def anderson_rubin_ci(res, grid):
    """Invert the cluster-robust AR test over a grid of beta0."""
    keep = np.array([ar_pvalue(res, b0) > .05 for b0 in grid])
    if not keep.any():
        return (np.nan, np.nan), "empty"
    inside = np.asarray(grid)[keep]
    shape = "bounded" if (not keep[0] and not keep[-1]) else "unbounded_within_grid"
    if keep.sum() != (np.flatnonzero(keep).max() - np.flatnonzero(keep).min() + 1):
        shape = "disjoint"
    return (float(inside.min()), float(inside.max())), shape


def tidy(res, keys=None, **extra):
    keys = keys or res["names"]
    rows = []
    for k in keys:
        lo, hi = res["ci95"][k]
        rows.append(dict(term=k, coef=res["coef"][k], se=res["se"][k], ci_lo=lo, ci_hi=hi, p=res["p"][k],
                         n=res["n"], clusters=res["clusters"], method=res["method"], mean_y=res["mean_y"],
                         first_stage_F=res.get("first_stage", {}).get("F_cluster_robust", np.nan), **extra))
    return rows
