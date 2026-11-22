"""Inflow x outflow growth grid on the AUDITED forecast engine (audit_forecast.py), unmodified.

Scales the engine's TOTAL inflow (recurring flow + the three expected waves: CAEN, capital, fiscal)
and its TOTAL solving capacity by fixed percentages from the simulation start (19.11.2026), in the
status-quo scenario ("continuitate" == "referinta"). Everything else (2,000 draws, seed, inputs)
is the audited run. Guards:
  * the (0,0) cell must reproduce the audited status quo (30.06.2028: 74/136/214.1; peak 124/165/220);
  * audit_data/ must be byte-identical before and after (prepare_workload rewrites two CSVs).
Waits <= 3 days are the metric floor (empty queue) and are flagged, never reported as "3 days".

Run:  ..\\venv\\Scripts\\python.exe -X utf8 forecast_grid.py   -> out/forecast_grid.json
"""
from __future__ import annotations
import sys, json, hashlib
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
PP = HERE.parent / "analysis" / "policy_paper_ro"
sys.path.insert(0, str(PP))
import audit_forecast as AF  # noqa: E402

IN_STEPS = [-20, -10, 0, 10, 20, 30]      # % change of total inflow
OUT_STEPS = [-10, 0, 10, 20, 30, 40]      # % change of total solving capacity


def tree_hash(d: Path) -> dict:
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(d.glob("*")) if p.is_file()}


def q(v):
    return [float(x) for x in np.percentile(v, [10, 50, 90], method="linear")]


def main():
    before = tree_hash(AF.OUT)
    m = AF.prepare_workload()
    after = tree_hash(AF.OUT)
    changed = [k for k in before if before[k] != after.get(k)]
    assert not changed, f"audit_data changed by prepare_workload: {changed}"

    dates, opening = m["dates"], m["opening"]
    n = len(dates)
    base_in = m["ordinary"] + m["late"] + m["caen"]          # continuitate: no stagger, no automation
    base_cap = m["capacity"]                                  # continuitate: no support, no durable gain
    june = n - 1
    open_h = opening[:n].astype(bool)
    y27 = (dates >= "2027-01-01") & (dates <= "2027-12-31") & open_h
    ref = {"inflow_per_open_day_2027_p50": float(np.median(base_in[:, y27].sum(1) / y27.sum())),
           "capacity_per_open_day_p50": float(np.median(base_cap[:, :n][:, open_h].mean(1)))}

    cells = []
    for di in IN_STEPS:
        for do in OUT_STEPS:
            try:
                stock, cal, _ = AF.simulate(m["initial"], base_in * (1 + di / 100), base_cap * (1 + do / 100), opening)
            except ValueError:
                cells.append(dict(d_in=di, d_out=do, beyond_horizon=True))
                continue
            j = q(cal[:, june]); pk = q(cal.max(axis=1))
            cells.append(dict(d_in=di, d_out=do, beyond_horizon=False,
                              june2028_p10=j[0], june2028_p50=j[1], june2028_p90=j[2],
                              peak_p10=pk[0], peak_p50=pk[1], peak_p90=pk[2],
                              stock_june2028_p50=float(np.median(stock[:, june])),
                              june_p50_at_floor=bool(j[1] <= 3), june_p90_at_floor=bool(j[2] <= 3)))
            if di == 0 and do == 0:
                c = cells[-1]
                assert [round(c["june2028_p10"]), round(c["june2028_p50"]), round(c["june2028_p90"], 1)] == [74, 136, 214.1], c
                assert [round(c["peak_p10"]), round(c["peak_p50"]), round(c["peak_p90"])] == [124, 165, 220], c
            print(f"in {di:+4d}%  out {do:+4d}%  -> June 2028 p50 {cells[-1].get('june2028_p50', float('nan')):6.1f}"
                  f"  p90 {cells[-1].get('june2028_p90', float('nan')):6.1f}  peak p50 {cells[-1].get('peak_p50', float('nan')):6.1f}")
    out = dict(_meta="Grid on audited audit_forecast.py (status quo), 2000 draws, seed 20261121; "
                     "multipliers on TOTAL inflow (recurring + CAEN/capital/fiscal waves) and TOTAL capacity from 19.11.2026. "
                     "Calendar-day wait of a standard file filed on the date. <=3 days = metric floor.",
               start=str(AF.START.date()), horizon=str(AF.HORIZON.date()), draws=AF.N_DRAWS,
               in_steps=IN_STEPS, out_steps=OUT_STEPS, reference=ref, audit_data_unchanged=True, cells=cells)
    (HERE / "out" / "forecast_grid.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("wrote out/forecast_grid.json · reference", ref)


if __name__ == "__main__":
    main()
