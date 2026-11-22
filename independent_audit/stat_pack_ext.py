"""Extension of the statistics pack: work effort (Volume 4) and per-county sheets (Volume 5), plus one Excel
workbook with every table of Volumes 2, 4 and 5 for analysts. Writes out/stat_pack_ext.json and
analysis/raport_executiv_2026-11/Date_ONRC_Coada_2026-11.xlsx.

Effort figures are SYSTEM-LEVEL only: no per-person or per-registrator productivity (withdrawn at gate M2;
the public data do not show who worked on what). Timestamps are the decision times recorded in BERC.

Run:  ..\\venv\\Scripts\\python.exe -X utf8 stat_pack_ext.py
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np, pandas as pd
import stat_pack as SPK

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
DELIV = HERE.parent / "analysis" / "raport_executiv_2026-11"
HOLSET = set(SPK.HOL.normalize())
R = {}


def put(name, df, meta):
    R[name] = dict(meta=meta, columns=list(df.columns), rows=json.loads(df.to_json(orient="records", force_ascii=False)))
    print(f"  {name:30} {len(df):>4} rows")


def main():
    b = pd.read_pickle(SPK.BERC)
    b = b[b.res.notna() & b.app.notna()].copy()
    b["d"] = b.res.dt.normalize(); b["W"] = (b.res - b.app).dt.total_seconds() / 86400
    b["strict"] = b.sol.isin(SPK.STRICT); b["broad"] = b.sol.isin(SPK.BROAD); b["aman"] = b.sol.eq("Amânat")
    b["work"] = b.broad | b.aman                     # a decision a registrar had to issue (final or adjournment)
    w = b[(b.d >= "2023-04-01") & b.work].copy()
    w["nonwork_day"] = (w.d.dt.dayofweek >= 5) | w.d.isin(HOLSET)
    w["hour"] = w.res.dt.hour
    w["after_hours"] = (~w.nonwork_day) & ((w.hour >= 16) | (w.hour < 8))

    # ---------------- E1 yearly volume
    rows = []
    for y, g in w.groupby(w.d.dt.year):
        lo = max(pd.Timestamp(f"{y}-01-01"), pd.Timestamp("2023-04-01")); hi = min(pd.Timestamp(f"{y}-12-31"), b.d.max())
        lwd = SPK.legal_wd(lo, hi)
        rows.append(dict(an=int(y), perioada=f"{lo.date()} – {hi.date()}", zile_lucr_legale=lwd, decizii_total=int(len(g)),
                         finale=int(g.broad.sum()), amanari=int(g.aman.sum()), decizii_pe_zi_lucr=round(len(g) / lwd),
                         pondere_amanari_pct=round(100 * g.aman.mean(), 1)))
    put("efort_anual", pd.DataFrame(rows), "Toate deciziile emise (finale largi + amânări), pe an calendaristic; 2023 de la 1 aprilie, 2026 până la ultima decizie.")

    # ---------------- E2 same period each year (1 Oct – 19 Nov, last complete day)
    rows = []
    for y in (2023, 2024, 2025, 2026):
        lo, hi = pd.Timestamp(f"{y}-10-01"), pd.Timestamp(f"{y}-11-19")   # 20.11.2026 is a partial day in the archive
        g = w[(w.d >= lo) & (w.d <= hi)]; lwd = SPK.legal_wd(lo, hi)
        rows.append(dict(an=y, decizii_total=int(len(g)), decizii_pe_zi_lucr=round(len(g) / lwd), finale_pe_zi_lucr=round(g.broad.sum() / lwd),
                         amanari_pe_zi_lucr=round(g.aman.sum() / lwd)))
    e2 = pd.DataFrame(rows); e2["fata_de_2023_pct"] = (100 * (e2.decizii_pe_zi_lucr / e2.decizii_pe_zi_lucr.iloc[0] - 1)).round(1)
    put("efort_aceeasi_perioada", e2, "1 octombrie – 19 noiembrie, fiecare an (20.11.2026 e o zi parțială în arhivă și e exclusă): toate deciziile (finale largi + amânări) pe zi lucrătoare legală.")

    # ---------------- E2b same windows as the MJ inflow figures, every year (seasonality check)
    rows = []
    for y in (2024, 2025, 2026):
        r = {"an": y}
        for key, lo, hi in (("ian_iun", f"{y}-01-01", f"{y}-06-30"), ("aug_oct", f"{y}-08-01", f"{y}-10-31")):
            g = w[(w.d >= lo) & (w.d <= hi)]; lwd = SPK.legal_wd(pd.Timestamp(lo), pd.Timestamp(hi))
            r[f"decizii_pe_zi_{key}"] = round(len(g) / lwd)
        r["aug_oct_fata_de_ian_iun_pct"] = round(100 * (r["decizii_pe_zi_aug_oct"] / r["decizii_pe_zi_ian_iun"] - 1), 1)
        rows.append(r)
    put("efort_sezon_MJ", pd.DataFrame(rows), "Toate deciziile pe zi lucrătoare legală, în aceleași ferestre ca intrările din nota MJ (ian.–iun. vs aug.–oct.), pe ani: scăderea din aug.–oct. e sezonieră.")

    # ---------------- E3 decisions outside the working schedule
    rows = []
    for y, g in w.groupby(w.d.dt.year):
        nw = g[g.nonwork_day]
        rows.append(dict(an=int(y), zile_nelucratoare_cu_decizii=int(nw.d.nunique()), decizii_in_zile_nelucratoare=int(len(nw)),
                         pondere_zile_nelucratoare_pct=round(100 * len(nw) / len(g), 2),
                         pondere_dupa_16_sau_inainte_8_pct=round(100 * g.after_hours.mean(), 1)))
    put("efort_in_afara_programului", pd.DataFrame(rows),
        "Decizii cu marca temporală în weekend / sărbători legale sau, în zile lucrătoare, după 16:00 ori înainte de 8:00. Marca e cea din BERC; nu dovedește ore suplimentare individuale.")
    m26 = w[w.d >= "2026-01-01"]
    mm = m26.groupby(m26.d.dt.to_period("M")).agg(decizii=("work", "size"), in_zile_nelucratoare=("nonwork_day", "sum"),
                                                   dupa_program=("after_hours", "sum")).reset_index()
    mm["luna"] = mm.d.astype(str); mm = mm.drop(columns="d")
    mm["pondere_in_afara_pct"] = (100 * (mm.in_zile_nelucratoare + mm.dupa_program) / mm.decizii).round(1)
    put("efort_in_afara_programului_lunar_2026", mm[["luna", "decizii", "in_zile_nelucratoare", "dupa_program", "pondere_in_afara_pct"]],
        "2026, pe luna deciziei.")
    hr = w[(w.d >= "2026-01-01") & ~w.nonwork_day].hour.value_counts(normalize=True).sort_index()
    put("efort_ora_deciziei_2026", pd.DataFrame({"ora": list(range(24)), "decizii_pct": [round(100 * hr.get(h, 0), 2) for h in range(24)]}),
        "Ponderea deciziilor pe ora mărcii temporale, zile lucrătoare 2026.")

    # ---------------- per county: monthly series 2025-01 .. 2026-11 (decision month)
    c = b[(b.d >= "2025-01-01")].copy(); c["luna"] = c.d.dt.to_period("M").astype(str)
    cs = c[c.strict & (c.W >= 0) & (c.W < 400)]
    med = cs.groupby(["county", "luna"], observed=True).W.median().round(1).rename("mediana")
    n = cs.groupby(["county", "luna"], observed=True).size().rename("finale")
    rej = cs.groupby(["county", "luna"], observed=True).sol.apply(lambda s: round(100 * (s == "Respins").mean(), 1)).rename("respinse_pct")
    am = c.groupby(["county", "luna"], observed=True).aman.mean().mul(100).round(1).rename("amanari_pct")
    cm = pd.concat([n, med, rej, am], axis=1).reset_index().rename(columns={"county": "cod"})
    put("judete_lunar", cm, "Pe oficiu de depunere și luna deciziei: finale stricte, mediana așteptării (zile), % respinse, % amânări din toate deciziile.")
    nat = cs.groupby("luna").W.median().round(1)
    put("national_lunar", nat.reset_index().rename(columns={"W": "mediana"}), "Mediana națională pe luna deciziei, aceeași definiție.")
    # share of national decisions in 2026, and Nov 2026 key figures per county
    s26 = b[(b.d >= "2026-01-01") & b.work]
    share = (100 * s26.groupby("county", observed=True).size() / len(s26)).round(2).rename("pondere_decizii_2026_pct")
    put("judete_pondere_2026", share.reset_index().rename(columns={"county": "cod"}), "Ponderea fiecărui oficiu în toate deciziile din 2026.")
    pt = pd.read_csv(OUT / "per_county_tandem_2026-11-21.csv").rename(columns={"county_mn": "cod"})
    put("judete_portal_etape", pt, "Eșantion myportal pe oficiu: dosare în operare / la registrator (mic pe oficiu: orientativ).")

    (OUT / "stat_pack_ext.json").write_text(json.dumps(R, ensure_ascii=False, indent=1, default=str), encoding="utf-8")

    # ---------------- Excel workbook: every table of volumes 2, 4, 5
    base = json.loads((OUT / "stat_pack.json").read_text(encoding="utf-8"))
    xl = DELIV / "Date_ONRC_Coada_2026-11.xlsx"
    with pd.ExcelWriter(xl, engine="openpyxl") as X:
        readme = [("Fișier", "Date_ONRC_Coada_2026-11.xlsx — toate tabelele volumelor 2, 4 și 5"), ("Autor", "Ștefan-Lucian Deleanu · stefandeleanu.ro"),
                  ("Surse", "BERC (4.077.510 decizii), eșantion myportal, Nota MJ 30.10 și 6.11.2026, model de coadă auditat"),
                  ("Definiții", "W = zile calendaristice de la înregistrare la decizie; finale stricte = admis, respins, renunțat; finale largi = + certificări; zi lucrătoare legală = L–V fără sărbători"),
                  ("Județe", "Ordine alfabetică / cod. NU sunt clasamente: diferențele sunt mici și nu persistă (C75)."),
                  ("Proveniență", "Fiecare foaie are pe primul rând descrierea; cifrele din rapoarte au coduri [Cxx] în claims_registry.csv")]
        pd.DataFrame(readme, columns=["Câmp", "Valoare"]).to_excel(X, sheet_name="CITESTE", index=False)
        for src in (base, R):
            for k, t in src.items():
                if not isinstance(t, dict) or "rows" not in t: continue
                if k in ("lista_verificari_sigure", "judete_portal_etape"): continue   # outdated model / per-office sample too small
                df = pd.DataFrame(t["rows"], columns=t["columns"])
                sheet = k[:31]
                pd.DataFrame([[t["meta"]]]).to_excel(X, sheet_name=sheet, index=False, header=False)
                df.to_excel(X, sheet_name=sheet, index=False, startrow=2)
    print("wrote", xl)


if __name__ == "__main__":
    main()
