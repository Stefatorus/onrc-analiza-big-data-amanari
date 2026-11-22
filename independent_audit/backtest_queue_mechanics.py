"""Backtest of the queue model on BERC (ground truth), from past origins, against filing cohorts that are (almost) fully decided.

Two tests, both using the SAME first-come-first-served daily recursion as the forecast engine (S_{t+1} = max(0, S_t + A_t − C_t)):
  1. MECHANISM (hindcast with realised inputs): arrivals A_d = finals eventually decided, by filing day; capacity C_t = finals
     decided on day t; initial queue = files filed before the origin and decided on/after it. Predicted wait of the MEDIAN file
     filed on day d is compared with the observed median wait of files filed that day.
  2. FORECAST (only information available at the origin): capacity = mean of the last 12 days with decisions (engine rule),
     arrivals = mean daily arrivals of the 8 weeks before the origin, on working days. Shows how much a forecast misses when
     demand changes (the autumn 2026 wave).
Cohorts evaluated: filing days from the origin to 13.09.2026 (the portal sample shows those weeks fully resolved; C73).
Writes out/backtest_queue_mechanics.json.
"""
from __future__ import annotations
import sys as _sys, pathlib as _pl; _sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[1])); import config  # repo config.py
import json
from pathlib import Path
import numpy as np, pandas as pd

HERE = Path(__file__).resolve().parent
BERC = Path(str(config.BERC_PKL))
STRICT = ["Admis", "Respins", "Renunțat"]
CUTOFF = pd.Timestamp("2026-09-13")
ORIGINS = ["2026-03-02", "2026-06-01", "2026-08-03"]


def main():
    b = pd.read_pickle(BERC)[["cat", "sol", "res", "app"]]
    b = b[b.res.notna() & b.app.notna() & b.sol.isin(STRICT) & b.cat.isin(["CERERE265", "INMATRIC265"])]
    b["W"] = (b.res - b.app).dt.total_seconds() / 86400
    b = b[(b.W >= 0) & (b.W < 400)]
    b["dd"] = b.app.dt.normalize(); b["rd"] = b.res.dt.normalize()
    obs = b.groupby("dd").W.median()
    days = pd.date_range("2025-10-01", "2026-11-20")
    arr = b.groupby("dd").size().reindex(days, fill_value=0).astype(float)
    cap = b.groupby("rd").size().reindex(days, fill_value=0).astype(float)
    res = {}
    for o in ORIGINS:
        O = pd.Timestamp(o)
        S0 = float(((b.dd < O) & (b.rd >= O)).sum())
        horizon = pd.date_range(O, "2026-11-20")
        A = arr.reindex(horizon).to_numpy(); C_real = cap.reindex(horizon).to_numpy()
        # forecast inputs known at the origin
        hist_dec = cap[(cap.index < O) & (cap > 0)]
        c_fore = float(hist_dec.iloc[-12:].mean())
        wd = np.array([d.dayofweek < 5 for d in horizon])
        hist_arr = arr[(arr.index < O) & (arr.index >= O - pd.Timedelta(weeks=8))]
        a_fore = float(hist_arr[hist_arr.index.dayofweek < 5].mean())
        C_fore = np.where(wd, c_fore, 0.0); A_fore = np.where(wd, a_fore, arr[(arr.index < O) & (arr.index >= O - pd.Timedelta(weeks=8))][lambda x: x.index.dayofweek >= 5].mean())

        def predict(A_, C_):
            cumC = np.cumsum(C_)
            cumA_before = np.concatenate([[0.0], np.cumsum(A_)[:-1]])
            out = []
            for i in range(len(horizon)):
                target = S0 + cumA_before[i] + A_[i] / 2.0      # position of the median file filed on day i
                j = int(np.searchsorted(cumC, target, side="left"))
                out.append(float(j - i) if j < len(horizon) else np.nan)
            return np.array(out)

        p_mech = predict(A, C_real)
        p_fore = predict(A_fore, C_fore)
        ev = [(i, d) for i, d in enumerate(horizon) if d <= CUTOFF and d.dayofweek < 5 and d in obs.index and arr.get(d, 0) >= 200]
        o_v = np.array([obs[d] for _, d in ev]); m_v = np.array([p_mech[i] for i, _ in ev]); f_v = np.array([p_fore[i] for i, _ in ev])
        ok_m = ~np.isnan(m_v); ok_f = ~np.isnan(f_v)
        weekly = pd.DataFrame({"zi": [d for _, d in ev], "observat": o_v, "mecanism": m_v, "prognoza": f_v})
        weekly["sapt"] = weekly.zi.dt.to_period("W-SUN").apply(lambda p: str(p.start_time.date()))
        wk = weekly.groupby("sapt")[["observat", "mecanism", "prognoza"]].median().round(1).reset_index()
        res[o] = dict(origin=o, stoc_initial=int(S0), zile_evaluate=int(len(ev)),
                      mecanism=dict(mae=round(float(np.mean(np.abs(m_v[ok_m] - o_v[ok_m]))), 1), bias=round(float(np.mean(m_v[ok_m] - o_v[ok_m])), 1),
                                    corelatie=round(float(np.corrcoef(m_v[ok_m], o_v[ok_m])[0, 1]), 3)),
                      prognoza=dict(capacitate_presupusa=round(c_fore), intrari_presupuse=round(a_fore),
                                    mae=round(float(np.mean(np.abs(f_v[ok_f] - o_v[ok_f]))), 1), bias=round(float(np.mean(f_v[ok_f] - o_v[ok_f])), 1)),
                      saptamanal=json.loads(wk.to_json(orient="records", force_ascii=False)))
        r = res[o]
        print(f"origin {o}: S0={S0:,.0f}  days={len(ev)}  MECHANISM MAE={r['mecanism']['mae']} bias={r['mecanism']['bias']} r={r['mecanism']['corelatie']}  |  FORECAST MAE={r['prognoza']['mae']} bias={r['prognoza']['bias']} (cap {c_fore:,.0f}, arr {a_fore:,.0f})")
    out = dict(_meta="Backtest pe BERC (sursa de referință): (1) mecanismul cozii cu intrări și capacitate reale; (2) prognoza doar cu ce se știa la origine. "
                     "Comparat cu mediana observată a așteptării pe ziua depunerii, pentru cohortele aproape complet decise (până la 13.09.2026). Zile calendaristice.",
               origini=res)
    (HERE / "out" / "backtest_queue_mechanics.json").write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str), encoding="utf-8")


if __name__ == "__main__":
    main()
