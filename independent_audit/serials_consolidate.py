"""Consolidates the request-number (serial counter) analysis from reserves_check/ into out/serials_findings.json
(read by the claims registry) and reserves_check/serials_summary.json (the methodology paragraph).
Values are PARSED from the analysis outputs, not typed.
"""
from __future__ import annotations
import json, re, ast
from pathlib import Path
import pandas as pd

HERE = Path(__file__).resolve().parent
RC = HERE / "reserves_check"


def tup(s):
    return [int(x) for x in ast.literal_eval(s)]


def main():
    per = pd.read_csv(RC / "11_period_vs_MJ_press.csv").set_index("period")
    h1 = per.loc["H1 2026 (MJ 4.533)"]; jj = per.loc["Jan-Jul 2026 (press >26.000)"]
    smp = pd.read_csv(RC / "13_inflow_from_sample.csv").set_index("period")
    st = pd.read_csv(RC / "13_stock_estimates.csv")
    st = st[st.defn == "judged (all is_judged)"].set_index("date")
    stock = {d: dict(central=tup(st.loc[d, "stock_lo"])[0], lo=tup(st.loc[d, "stock_lo"])[1], hi=tup(st.loc[d, "stock_lo"])[2],
                     upper_variant=tup(st.loc[d, "stock_hi"])[0]) for d in st.index}
    t14 = (RC / "14_inmatric_lowerbound.out.txt").read_text(encoding="utf-8")
    inm_little = int(re.search(r"Little estimate of pending inmatric.*?:\s*(\d+)", t14).group(1))
    t13 = (RC / "13_stock_estimate.out.txt").read_text(encoding="utf-8")
    m = re.search(r"stage1 \((\d+), (\d+), (\d+)\)\s+stage2 \((\d+), (\d+), (\d+)\)\s+share stage1 ([\d.]+)", t13)
    stages = dict(stage1=int(m.group(1)), stage2=int(m.group(4)), share_stage1=float(m.group(7)))
    t23 = (RC / "23_april27_floor.out.txt").read_text(encoding="utf-8").splitlines()
    floor = {}; cur = None
    for ln in t23:
        mm = re.match(r"^(CERERE265|INMATRIC265|AUTO_AMANARI) - share by working days", ln)
        if mm: cur = mm.group(1)
        if cur and ln.startswith("after (27.04-28.06)") and cur not in floor:
            floor[cur] = float(ln.split()[-4])                  # columns ...0..6 -> working day 3
    t22 = (RC / "22_task2_measures.out.txt").read_text(encoding="utf-8")
    tau = float(re.search(r"Kendall tau= ([\d.]+)", t22).group(1))
    fl = re.search(r"share Respins ([\d.]+)\s+vs all ([\d.]+)\s+share jtype F ([\d.]+)\s+vs all ([\d.]+)", t22)
    wk = [ln.split() for ln in t22.splitlines() if re.match(r"^2026-0[345]-\d\d/2026", ln)]
    p05_before = [float(r[3]) for r in wk if r[0] < "2026-04-27"]; p05_after = [float(r[3]) for r in wk if r[0] >= "2026-04-27"]
    rf = pd.read_csv(RC / "26_refiling_baseline.out.txt", sep=r"\s+", nrows=3, index_col=0).set_index("sol")
    out = dict(
        _meta="Analiza contorului numerelor de cerere (reserves_check/), consolidată. Valorile sunt citite din ieșirile analizei.",
        counter=dict(national_since="2024-07-26", resets_yearly=True, berc_coverage_of_numbers_h1_2026=round(float(h1.coverage), 3),
                     total_numbers_per_wd_jan_jul_2026=int(jj.counter_per_wd), portal_same_counter=True),
        inflow=dict(h1_2026_berc_per_wd=int(h1.berc_per_wd), may_jul=dict(per_wd=int(smp.loc["2026-05-12..2026-07-31", "per_wd"])),
                    aug_oct=dict(per_wd=int(smp.loc["2026-08-01..2026-10-31", "per_wd"]), lo=int(smp.loc["2026-08-01..2026-10-31", "per_wd_lo"]), hi=int(smp.loc["2026-08-01..2026-10-31", "per_wd_hi"])),
                    sep=dict(per_wd=int(smp.loc["2026-09-01..2026-09-30", "per_wd"]), lo=int(smp.loc["2026-09-01..2026-09-30", "per_wd_lo"]), hi=int(smp.loc["2026-09-01..2026-09-30", "per_wd_hi"])),
                    oct=dict(per_wd=int(smp.loc["2026-10-01..2026-10-31", "per_wd"])), nov=dict(per_wd=int(smp.loc["2026-11-01..2026-11-19", "per_wd"])),
                    note="sept.–nov. din eșantion ponderat; exclud înmatriculările în curs (subestimare de circa 400–600/zi)"),
        stock=stock, inmatric_pending_little=inm_little, stages_at_harvest=stages,
        april27=dict(share_at_3_working_days=floor, p05_wait_hours_before=round(sum(p05_before) / len(p05_before), 1),
                     p05_wait_hours_after=round(sum(p05_after) / len(p05_after), 1)),
        order=dict(kendall_tau=tau, fast_rejected=float(fl.group(1)), all_rejected=float(fl.group(2)), fast_pfa=float(fl.group(3)), all_pfa=float(fl.group(4))),
        refiling=dict(after_rejection={k: float(rf.loc["Respins", f"next_within_{k}d"]) for k in (30, 90, 365)},
                      after_admission={k: float(rf.loc["Admis", f"next_within_{k}d"]) for k in (30, 90, 365)}))
    (HERE / "out" / "serials_findings.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    f = lambda x: f"{x:,}".replace(",", ".")
    s6 = stock["2026-11-06"]
    text = ("Fiecare cerere primește la depunere un număr de înregistrare. Am verificat dacă aceste numere vin dintr-un singur contor. "
            "Pe vechea platformă, fiecare oficiu județean avea propriul contor. Din 26 iulie 2024, de la lansarea noului portal, numerele vin dintr-un singur contor național, care pornește de la capăt la 1 ianuarie, crește în ordinea depunerii și este practic fără goluri; portalul folosește același contor ca buletinul. "
            "Contorul numără însă orice înregistrare, inclusiv certificate și informări, nu doar cererile care ajung la registrator: buletinul conține doar circa o cincime din numere. "
            "Am combinat de aceea contorul cu eșantionul din portal, care arată ce fel de cerere stă în spatele fiecărui număr, și cu buletinul, care arată când a fost decisă. "
            f"Așa am putut măsura, din datele noastre, cererile de înregistrare intrate pe zi: {f(out['inflow']['h1_2026_berc_per_wd'])} în prima jumătate a anului 2026 (Ministerul raportează 4.533) și {f(out['inflow']['aug_oct']['per_wd'])} în august–octombrie (Ministerul: 6.931). "
            f"Am putut estima și stocul de cereri nesoluționate: circa {f(round(s6['central'], -3))} la 6 noiembrie, fără înmatriculările încă în curs, față de 204.414 raportate de Minister. "
            f"Cea mai importantă constatare: vârful a venit în septembrie, cu circa {f(out['inflow']['sep']['per_wd'])} de cereri pe zi lucrătoare, iar în octombrie intrările au revenit aproape de ritmul de soluționare (dacă se adaugă înmatriculările încă în curs, pe care eșantionul nu le vede); în noiembrie au coborât sub el, astfel că stocul a început să scadă încet.")
    (RC / "serials_summary.json").write_text(json.dumps(dict(text_ro=text), ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: out[k] for k in ("inflow", "stock", "april27", "order", "refiling")}, ensure_ascii=False)[:1500])


if __name__ == "__main__":
    main()
