"""County (office) rankings for Volume 5 and the main report. Light: reads only the audited county table
(atlas_rerun county_indicators.csv) and stat_pack_ext.json (monthly medians per office) — no archive load.

Rankings show WHERE differences appear, to help locate problems. The office in BERC is the office of FILING,
so a ranking is not a performance score of the staff there; registrars are never ranked (no personal data).

Writes out/county_rankings.json and adds one sheet per ranking to Date_ONRC_Coada_2026-11.xlsx.
"""
from __future__ import annotations
import json
from pathlib import Path
import pandas as pd

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
XL = HERE.parent / "analysis" / "raport_executiv_2026-11" / "Date_ONRC_Coada_2026-11.xlsx"


def main():
    ct = pd.read_csv(OUT / "atlas_rerun" / "audit_data" / "county_indicators.csv", encoding="utf-8-sig")
    X = json.loads((OUT / "stat_pack_ext.json").read_text(encoding="utf-8"))
    cm = pd.DataFrame(X["judete_lunar"]["rows"]); nat = pd.DataFrame(X["national_lunar"]["rows"]).set_index("luna").mediana
    share = pd.DataFrame(X["judete_pondere_2026"]["rows"]).set_index("cod").pondere_decizii_2026_pct
    names = ct.set_index("code").name
    R = {}

    def ranked(df, col, asc=False):
        d = df.sort_values(col, ascending=asc).reset_index(drop=True); d.insert(0, "loc", range(1, len(d) + 1)); return d

    base = ct[["code", "name", "region", "n_nov", "median_nov", "p90_nov", "median_y25", "rejection_pct_crisis",
               "postponement_action_pct", "formation_gt10_pct"]].copy()
    base["schimbare_fata_de_2025_zile"] = (base.median_nov - base.median_y25).round(1)
    base["pondere_decizii_2026_pct"] = base.code.map(share)

    # local-problem index: months before the national wave (Jan 2025 – Jul 2026)
    pre = cm[(cm.luna >= "2025-01") & (cm.luna <= "2026-07")].copy()
    pre["exces"] = pre.mediana - pre.luna.map(nat)
    g = pre.groupby("cod")
    loc = pd.DataFrame({"exces_mediu_zile": g.exces.mean().round(2), "exces_maxim_zile": g.exces.max().round(1),
                        "luna_excesului_maxim": g.apply(lambda x: x.loc[x.exces.idxmax(), "luna"]),
                        "luni_peste_national_cu_5_zile": g.apply(lambda x: int((x.exces > 5).sum()))}).reset_index().rename(columns={"cod": "code"})
    loc["name"] = loc.code.map(names)

    tables = {
        "rang_asteptare_nov": (ranked(base, "median_nov")[["loc", "code", "name", "median_nov", "p90_nov", "n_nov"]],
                               "Mediana așteptării deciziilor din 1–18 noiembrie 2026, de la cea mai lungă la cea mai scurtă."),
        "rang_probleme_locale_2025_2026": (ranked(loc, "exces_mediu_zile")[["loc", "code", "name", "exces_mediu_zile", "exces_maxim_zile", "luna_excesului_maxim", "luni_peste_national_cu_5_zile"]],
                                           "Ianuarie 2025 – iulie 2026, înainte de valul național: cât a stat oficiul peste mediana națională, lună de lună (zile). Arată unde au fost probleme locale."),
        "rang_respingeri": (ranked(base, "rejection_pct_crisis")[["loc", "code", "name", "rejection_pct_crisis", "n_nov"]],
                            "Ponderea respingerilor în deciziile finale, august–noiembrie 2026."),
        "rang_amanari": (ranked(base, "postponement_action_pct")[["loc", "code", "name", "postponement_action_pct"]],
                         "Ponderea dosarelor amânate, august–noiembrie 2026."),
        "rang_inmatriculari_peste_10_zile": (ranked(base, "formation_gt10_pct")[["loc", "code", "name", "formation_gt10_pct"]],
                                             "Înmatriculări admise fără amânare care au depășit 10 zile lucrătoare, august–noiembrie 2026."),
        "rang_schimbare_fata_de_2025": (ranked(base, "schimbare_fata_de_2025_zile")[["loc", "code", "name", "median_y25", "median_nov", "schimbare_fata_de_2025_zile"]],
                                        "Cu câte zile a crescut mediana față de anul stabil 2025."),
        "rang_volum_2026": (ranked(base, "pondere_decizii_2026_pct")[["loc", "code", "name", "pondere_decizii_2026_pct"]],
                            "Ponderea oficiului în toate deciziile din 2026."),
    }
    for k, (df, meta) in tables.items():
        R[k] = dict(meta=meta, columns=list(df.columns), rows=json.loads(df.to_json(orient="records", force_ascii=False)))
    (OUT / "county_rankings.json").write_text(json.dumps(R, ensure_ascii=False, indent=1), encoding="utf-8")

    with pd.ExcelWriter(XL, engine="openpyxl", mode="a", if_sheet_exists="replace") as W:
        for k, (df, meta) in tables.items():
            pd.DataFrame([[meta + " Oficiul = oficiul de depunere; clasamentul arată unde apar diferențele, nu performanța personalului."]]).to_excel(W, sheet_name=k[:31], index=False, header=False)
            df.to_excel(W, sheet_name=k[:31], index=False, startrow=2)
    top = R["rang_probleme_locale_2025_2026"]["rows"][:5]
    print("wrote county_rankings.json; local-problem top 5:", [(r["name"], r["exces_mediu_zile"], r["luna_excesului_maxim"]) for r in top])
    print("longest Nov:", [(r["name"], r["median_nov"]) for r in R["rang_asteptare_nov"]["rows"][:3]],
          "· highest rejections:", [(r["name"], r["rejection_pct_crisis"]) for r in R["rang_respingeri"]["rows"][:3]])


if __name__ == "__main__":
    main()
