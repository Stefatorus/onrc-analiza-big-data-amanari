"""Costul economic și bugetar al întârzierilor, lună de lună (după luna deciziei), ianuarie 2024 – noiembrie 2026.

Aplică exact parametrii celor trei scenarii din analiza de impact (audit_data/cost_inputs.csv) pe zilele de întârziere
MĂSURATE ale dosarelor decise în fiecare lună. Conține doar costul realizat (dosare deja decise); expunerea
condiționată a stocului nu are o lună și se prezintă separat. Verificare: suma pe fereastra 1.08–18.11.2026 trebuie
să fie egală cu partea realizată a contului de impact (aceleași formule, stoc = 0).
Ieșire: out/cost_monthly.json (tabele în formatul stat_pack, citite de raport și de figuri).
"""
import json
from pathlib import Path
import pandas as pd
from cost_check import ledger

HERE = Path(__file__).resolve().parent
AD = HERE.parent / "analysis" / "policy_paper_ro" / "audit_data"
OUT = HERE / "out" / "cost_monthly.json"


def main():
    inp = pd.DataFrame(json.loads((HERE / "out" / "cost_founded.json").read_text(encoding="utf-8"))["inputs_founded"]).set_index("scenario")  # founded scenario
    d = pd.read_pickle("W:/SOLOResearch/analysis_decisions.pkl")[["cat", "app", "res", "sol", "jtype"]]
    d = d[(d.res >= "2024-01-01")].copy()
    d["w"] = (d.res - d.app).dt.total_seconds() / 86400
    d = d[d.w.between(0, 365)]
    d["luna"] = d.res.dt.strftime("%Y-%m")
    last = d.res.max()
    def exposure(x):
        b = x[(x.cat == "INMATRIC265") & (x.jtype == "J") & (x.sol == "Admis")]; c = x[(x.cat == "CERERE265") & (x.sol == "Admis")]
        return dict(approved_new_j=len(b), approved_changes=len(c), postpone_actions=int((x.cat == "AUTO_AMANARI").sum()),
                    observed_new_j_excess_days=float((b.w - 3).clip(lower=0).sum()), observed_changes_excess_days=float((c.w - 3).clip(lower=0).sum()),
                    observed_changes_over_30=int((c.w > 30).sum()))
    realized = {s: r._replace(pending=0) for s, r in zip(inp.index, inp.itertuples(index=False))}
    rows = []
    for m, x in d.groupby("luna"):
        ex = exposure(x); row = dict(luna=m, zile_exces_inmatriculari=round(ex["observed_new_j_excess_days"]),
                                     zile_exces_mentiuni=round(ex["observed_changes_excess_days"]))
        for s in ("prudent", "central", "tensionat"):
            L = ledger(realized[s], ex)
            row[f"economic_{s}_mil"] = L["total"] / 1e6; row[f"buget_{s}_mil"] = L["tax"] / 1e6
            if s == "central":
                row.update({f"canal_{k}_mil": v / 1e6 for k, v in L["channels"].items()})
        rows.append(row)
    win = d[(d.res >= "2026-08-01") & (d.res < "2026-11-19")]
    check = {s: ledger(realized[s], exposure(win))["total"] / 1e6 for s in realized}
    # the window sum by month (Nov cut at 18th) must equal the window ledger
    by_month_win = {s: sum(ledger(realized[s], exposure(x))["total"] for _, x in win.groupby("luna")) / 1e6 for s in realized}
    for s in check:
        assert abs(check[s] - by_month_win[s]) < 1e-6 * max(1, check[s]), (s, check[s], by_month_win[s])
    df = pd.DataFrame(rows)
    yr = df.assign(an=df.luna.str[:4]).groupby("an")[[c for c in df.columns if c.endswith("_mil")]].sum().reset_index()
    meta = ("Cost REALIZAT al dosarelor decise în lună (zile peste 3 zile calendaristice, dosare admise), cu parametrii scenariului fundamentat; "
            f"fără expunerea stocului. Noiembrie 2026 este parțial (până la {last:%d.%m.%Y}). Aceiași parametri pentru toți anii: e o măsură comparabilă a întârzierii exprimate în lei, nu o contabilitate.")
    cols_m = ["luna", "zile_exces_inmatriculari", "zile_exces_mentiuni", "economic_prudent_mil", "economic_central_mil", "economic_tensionat_mil",
              "buget_prudent_mil", "buget_central_mil", "buget_tensionat_mil"]
    out = dict(
        cost_lunar=dict(columns=cols_m, rows=df[cols_m].round(2).to_dict(orient="records"), meta=meta),
        cost_lunar_canale=dict(columns=["luna", "canal_A_mil", "canal_B_mil", "canal_C_mil", "canal_D_mil", "economic_central_mil"],
                               rows=df[["luna", "canal_A_mil", "canal_B_mil", "canal_C_mil", "canal_D_mil", "economic_central_mil"]].round(2).to_dict(orient="records"),
                               meta="Scenariul central, pe canale: A activitate nouă pierdută, B inactivare după expirarea sediului, C alte modificări blocate, D amânări evitabile."),
        cost_anual=dict(columns=["an", "economic_prudent_mil", "economic_central_mil", "economic_tensionat_mil", "buget_prudent_mil", "buget_central_mil", "buget_tensionat_mil"],
                        rows=yr[["an", "economic_prudent_mil", "economic_central_mil", "economic_tensionat_mil", "buget_prudent_mil", "buget_central_mil", "buget_tensionat_mil"]].round(1).to_dict(orient="records"),
                        meta=meta),
        window_realized_mil=check, last_decision=f"{last:%Y-%m-%d %H:%M}",
        peak=dict(df.loc[df.economic_central_mil.idxmax(), ["luna", "economic_central_mil", "buget_central_mil"]]))
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1, default=float), encoding="utf-8")
    print(df[["luna", "economic_central_mil", "buget_central_mil"]].round(1).to_string(index=False))
    print("window realized (mil lei):", {k: round(v, 1) for k, v in check.items()})


if __name__ == "__main__":
    main()
