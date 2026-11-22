"""Scenariul fundamentat al impactului economic și bugetar.

Aceleași formule ca analiza inițială (cost_check.ledger), dar parametrii care au o bază în date sau în surse oficiale
sunt citiți din out/cost_evidence.json:
  - vânzări pe zi ale unei firme noi = (ponderea firmelor cu activitate) × (vânzări pe zi), bilanțuri MF;
  - ponderea valorii adăugate = Eurostat (economia de afaceri; micro-întreprinderi) și rezultatul brut al firmelor noi;
  - cota fiscală efectivă = impozit direct măsurat + contribuții la salariul minim pe angajații măsurați + TVA pe VA;
  - ponderea dosarelor de sediu = textul buletinelor PDF (dosare peste 30 de zile);
  - ponderea modificărilor cu impact economic separat = plafonul măsurat din buletinele PDF;
  - ponderea amânărilor evitabile la depunere (canalul D) = motivele amânărilor din buletinele PDF (out/delay_reasons.json).
Parametrii fără bază rămân ipoteze declarate (partea pierdută definitiv, costul pe zi al unei modificări blocate,
canalul B și costul unei amânări în canalul D). Plus: podeaua măsurată (doar date și dobânzi oficiale) și testul de substituție, refăcut.
Ieșire: out/cost_founded.json.
"""
import json
from pathlib import Path
import pandas as pd
from cost_check import ledger

HERE = Path(__file__).resolve().parent
AD = HERE.parent / "analysis" / "policy_paper_ro" / "audit_data"
EV = {x["id"]: x for x in json.loads((HERE / "out" / "cost_evidence.json").read_text(encoding="utf-8"))["findings"]}
DR = {x["id"]: x for x in json.loads((HERE / "out" / "delay_reasons.json").read_text(encoding="utf-8"))["findings"]}
OUT = HERE / "out" / "cost_founded.json"


def ev(k):
    return EV[k]["value"] if "value" in EV[k] else EV[k].get("values")


def founded_inputs():
    inp = pd.read_csv(AD / "cost_inputs.csv").set_index("scenario")
    c25 = ev("T3.cohort2025_fy2025")
    active = c25["positive_turnover_n"] / c25["onrc_n"]                       # share of registered firms reporting turnover
    fm = pd.read_csv(AD / "formation_turnover.csv").set_index(["cohort_year", "financial_year"]).loc[(2025, 2025)]
    mean_d = float(fm.mean_daily_at_least_180d_capped_p99)                      # capped mean per day, firms with >=180 days
    med_d = float(EV["T3.cohort2025_fy2025"]["value"]["daily_turnover_median"])
    tax = ev("T3.composite_tax_share")
    micro = ev("T4.a.va_share_micro_0_9")
    seat_docs = ev("T1.wait_over_30.office_docs"); seat_all = ev("T1.wait_over_30.seat_related")
    c_low = ev("T1.seat_excl_blocking_strict_excl_capital_with_caen")["excess_day_share"]
    c_high = ev("T1.seat_excl_blocking_strict")["excess_day_share"]
    f = inp.copy()
    src = {}
    f.loc[:, "net_turnover_per_day"] = [round(active * med_d), round(active * mean_d), 540]
    src["net_turnover_per_day"] = (f"bilanțuri MF, cohorta 2025: {active:.1%} din firmele noi raportează vânzări; × mediana / media plafonată pe zi; tensionat: recomandarea din evidență", "măsurat")
    f.loc[:, "value_added_share"] = [ev("T4.a.va_share_BS_exclO_S94"), micro["B-S_excl_O_S94"], 0.38]
    src["value_added_share"] = ("Eurostat SBS 2024: economia de afaceri / micro-întreprinderi; tensionat: rezultatul brut al firmelor noi", "sursă oficială")
    f.loc[:, "tax_share"] = [tax["total_low"], round((tax["total_low"] + tax["total_high"]) / 2, 3), tax["total_high"]]
    src["tax_share"] = ("impozit direct măsurat (bilanțuri) + contribuții la salariul minim 2026 pe angajații măsurați + TVA pe valoarea adăugată", "măsurat + legal")
    f.loc[:, "seat_share"] = [seat_docs, round((seat_docs + seat_all) / 2, 4), seat_all]
    src["seat_share"] = ("buletine BERC PDF, oct.–nov. 2026, dosare peste 30 de zile: documente de sediu / documente + schimbare de sediu", "măsurat")
    f.loc[:, "disjoint_blocked_changes_share"] = [c_low, round((c_low + c_high) / 2, 4), c_high]
    src["disjoint_blocked_changes_share"] = ("buletine BERC PDF: plafon (modificări care pot bloca activitatea, fără sediu), ponderat pe zile în exces", "plafon măsurat")
    for k in ("pending", "pending_new_j_share", "pending_new_excess_days", "pending_changes_excess_days"):
        src[k] = ("stoc MJ (central); zile rămase din prognoză", "sursă oficială + model")
    for k in ("lost_turnover_fraction", "inactivation_increment", "seat_private_cost", "seat_fiscal_cost", "blocked_change_cost",
              "blocked_change_tax_share", "preventable_post_share", "private_cost_per_post", "admin_cost_per_post"):
        src[k] = ("fără bază în date publice", "ipoteză")
    src["blocked_change_cost"] = (f"fără bază; ca ordin de mărime, {ev('T2.model_C_vs_turnover')['central']['pct_of_median_firm']:.1f}% din vânzările zilnice ale firmei mediane cu modificări", "ipoteză (verificată ca ordin de mărime)")
    # channel D: share of postponements avoidable at filing, MEASURED from the postponement reasons in the bulletin PDFs
    # (delay_reasons/07_results.py). A postponement is avoided only if ALL its reasons are avoidable (strict share);
    # "at least one avoidable reason" is only an upper bound. prudent = lower 95% CI of the strict share,
    # central = strict share, stressed = upper bound (at least one avoidable reason)
    dr_s, dr_s_lo, dr_a = (DR["DR.avoidable.strict"]["value"], DR["DR.avoidable.strict"]["ci95"][0],
                           DR["DR.avoidable.any"]["value"])
    f.loc[:, "preventable_post_share"] = [dr_s_lo, dr_s, dr_a]
    src["preventable_post_share"] = ("buletine BERC PDF, motivele amânărilor, 19.10–18.11.2026: toate motivele evitabile la depunere (limita inferioară IC95% / valoarea punctuală) / plafon: cel puțin un motiv evitabil", "măsurat")
    return inp, f, src


def main():
    inp, f, src = founded_inputs()
    ex = pd.read_csv(AD / "cost_observed_exposure.csv", index_col=0)["value"].to_dict()
    res = {}
    for name, tab in (("initial", inp), ("fundamentat", f)):
        res[name] = {}
        for s, r in tab.iterrows():
            L = ledger(r, ex)
            res[name][s] = dict(total=L["total"], tax=L["tax"], daily_econ=L["daily_econ"], daily_tax=L["daily_tax"],
                                channels=L["channels"], channels_share={k: v / L["total"] for k, v in L["channels"].items()},
                                d_admin=ex["postpone_actions"] * r.preventable_post_share * r.admin_cost_per_post)
    # substitution: part of the lost activity is made up by other firms (A on value added, C discounted)
    regimes = [(0, 0), (.5, .25), (.75, .5), (.9, .75), (1, 1)]
    sub = []
    for a, c in regimes:
        row = dict(regim=f"{int(a * 100)}% din A, {int(c * 100)}% din C")
        for s in ("prudent", "central", "tensionat"):
            ch = res["fundamentat"][s]["channels"]
            row[f"{s}_mil"] = (ch["A"] * (1 - a) + ch["B"] + ch["C"] * (1 - c) + ch["D"] + res["fundamentat"][s]["d_admin"]) / 1e6
        sub.append(row)
    # parameter table with the source / status of each value
    params = []
    for c in f.columns:
        params.append(dict(parametru=c, initial=[float(inp.loc[s, c]) for s in inp.index], fundamentat=[float(f.loc[s, c]) for s in f.index],
                           sursa=src.get(c, ("", ""))[0], stare=src.get(c, ("", ""))[1]))
    # one-at-a-time sensitivity around the founded central scenario
    cen = f.loc["central"]; base = ledger(cen, ex)["total"]; sens = []
    sens = []
    for c in f.columns:
        r1 = cen.copy(); r1[c] = f.loc["prudent", c]; r2 = cen.copy(); r2[c] = f.loc["tensionat", c]
        sens.append(dict(parameter=c, low=ledger(r1, ex)["total"] - base, high=ledger(r2, ex)["total"] - base, stare=src.get(c, ("", ""))[1]))
    sens = sorted(sens, key=lambda x: -(x["high"] - x["low"]))
    fl = ev("T5.floor_headline")
    n_found = sum(1 for p in params if p["stare"] not in ("ipoteză", "ipoteză (verificată ca ordin de mărime)"))
    out = dict(_meta="Scenariul fundamentat: aceleași formule, parametrii cu bază în date citiți din cost_evidence.json.",
               scenarios=res, substitution=sub, params=params, n_params=len(params), n_founded=n_found,
               floor=fl, sensitivity=sens, inputs_founded=f.reset_index().to_dict(orient="records"))
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1, default=float), encoding="utf-8")
    for name in res:
        print(name, {s: (round(v["total"] / 1e6, 1), round(v["tax"] / 1e6, 1), round(v["daily_econ"] / 1e6, 2)) for s, v in res[name].items()})
    print("C share founded central", round(res["fundamentat"]["central"]["channels_share"]["C"] * 100, 1), "% · founded params", n_found, "/", len(params))
    print("substitution", [(r["regim"], round(r["central_mil"], 1), round(r["prudent_mil"], 1)) for r in sub])
    print("floor", fl)


if __name__ == "__main__":
    main()
