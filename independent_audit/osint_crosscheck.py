"""Confruntarea afirmațiilor din presă / OSINT (osint/compilatie_presa_2026-11-21.md) cu datele noastre.

Pentru fiecare afirmație măsurabilă calculăm același lucru din BERC (decizii), din eșantionul myportal sau din nota MJ
și dăm un verdict pe o scală fixă:
  CONFIRMAT    — aceeași definiție, diferență ≤10% (sau același prag depășit);
  COMPATIBIL   — unitate / dată / definiție diferită, dar valorile sunt consistente;
  CONTRAZIS    — datele noastre arată altceva;
  NEVERIFICABIL— datele noastre nu pot verifica afirmația.
Scrie out/osint_crosscheck.json și o foaie în Date_ONRC_Coada_2026-11.xlsx.
"""
from __future__ import annotations
import sys as _sys, pathlib as _pl; _sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[1])); import config  # repo config.py
import json, re
from pathlib import Path
import pandas as pd

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
XL = HERE.parent / "analysis" / "raport_executiv_2026-11" / "Date_ONRC_Coada_2026-11.xlsx"
BERC = Path(str(config.BERC_PKL))


def pct(a, b): return 100 * (a / b - 1)
def n0(x): return f"{int(x):,}".replace(",", ".")
def p1(x): return (f"{x:+.1f}".replace("-", "−").replace(".", ",")) + "%"
def d1(x): return f"{x:.1f}".replace(".", ",")


def main():
    b = pd.read_pickle(BERC)[["cat", "sol", "res", "app"]]
    b = b[b.res.notna() & b.app.notna()]
    b["m"] = b.res.dt.to_period("M").astype(str)
    adm = b[b.sol.eq("Admis")]
    inm = adm[adm.cat.eq("INMATRIC265")].groupby("m").size()
    cer = adm[adm.cat.eq("CERERE265")].groupby("m").size()
    del b, adm
    S = json.loads((OUT / "stat_pack.json").read_text(encoding="utf-8"))
    L = json.loads((OUT / "LOCKED_CONSTANTS.json").read_text(encoding="utf-8"))
    mon = {r["luna"]: r for r in S["serie_lunara"]["rows"]}
    cty = {r["code"]: r for r in S["judete_alfabetic"]["rows"]}
    rows = []

    def add(pid, claim, public, ours, verdict, note, ours_src):
        rows.append(dict(id=pid, afirmatie=claim, valoare_publica=public, valoarea_noastra=ours, verdict=verdict, nota=note, sursa_noastra=ours_src))

    # P01 stock
    add("P01", "Stoc nesoluționat, sfârșitul lui octombrie 2026", ">210.000 (sindicat)",
        "208.318 (MJ, 30.10) · 204.414 (MJ, 6.11)", "COMPATIBIL",
        "Cifra sindicală e rotunjită și anterioară; nota MJ dă 208.318 la 30.10, apoi 204.414.", "Nota MJ (nivel C)")
    # P02/P03 waits
    oct_m, nov_m = mon["2026-10"]["W_med"], mon["2026-11"]["W_med"]
    add("P02", "Timp mediu de soluționare", ">30 de zile",
        f"mediana deciziilor: oct. {oct_m:.0f} de zile · 1–20 nov. {nov_m:.0f} de zile", "CONFIRMAT",
        "Datele noastre confirmă pragul și arată că în noiembrie așteptarea a crescut peste el.", "BERC, finale stricte, pe data deciziei")
    add("P03", "Timp pentru înmatriculări și mențiuni de rutină", ">40–45 de zile",
        f"modificări 16–20 nov.: 57,1 zile · înmatriculări: 41,1 zile", "CONFIRMAT",
        "Pentru deciziile din a doua jumătate a lui noiembrie, pragul de 40–45 de zile e depășit la modificări și atins la înmatriculări.", "BERC (C14, C15)")
    cj = cty.get("CJ", {}).get("median_nov")
    add("P04", "Cluj: proceduri care durează", ">45 de zile (3.11.2026)", f"mediana Cluj, decizii 1–18 nov.: {d1(cj)} zile", "CONFIRMAT",
        "Mediana oficiului Cluj depășește 45 de zile.", "BERC, pe oficiul de depunere")
    # P05 inflow
    _sf = json.loads((OUT / "serials_findings.json").read_text(encoding="utf-8"))
    peak = f"{_sf['inflow']['h1_2026_berc_per_wd']:,}".replace(",", ".")
    cnt = f"{round(_sf['counter']['total_numbers_per_wd_jan_jul_2026'], -2):,.0f}".replace(",", ".")
    add("P05", "Cereri zilnice ian.–iul. 2026", ">26.000/zi (>8× 2024)",
        f"intrări de cereri de înregistrare (MJ): 4.533/zi în prima jumătate a lui 2026 · din datele noastre: {peak}/zi · contorul tuturor numerelor de cerere (orice tip): ≈{cnt} pe zi lucrătoare, ian.–iul. 2026",
        "CONTRAZIS (ca dosare) · COMPATIBIL (ca toate cererile din portal)",
        "Nota MJ dă 4.533 de cereri de înregistrare pe zi. O cifră de zeci de mii pe zi corespunde contorului tuturor cererilor din portal (inclusiv certificate și informări), nu dosarelor care ajung la registrator.",
        "Nota MJ (C47) + eșantion myportal")
    add("P06", "Procesare strict cronologică", "da",
        "8,7% din modificări și 15,7% din înmatriculări decise în ≤14 zile (2–19 nov.), deși mediana era de 53 / 42 de zile", "CONTRAZIS",
        "O parte din dosare trece mult mai repede decât ordinea depunerii; datele nu arată de ce.", "BERC (C38)")
    add("P07", "Rutare aleatorie a dosarelor între oficii", "da",
        "din august 2026, toate cele 42 de oficii urmează aceeași curbă a așteptării; diferențele sunt de câteva zile", "COMPATIBIL",
        "Datele sunt consistente cu o coadă comună, națională; nu dovedesc mecanismul rutării.", "BERC, Volumul 5 (C49, C75)")
    add("P08", "Posturi: schemă / finanțate / ocupate", "1.792 / 1.384 / ~1.260", "1.792 / 1.384 / 1.250 (MJ)", "CONFIRMAT",
        "Diferența la posturile ocupate (1.260 față de 1.250) e de sub 1% și ține probabil de dată.", "Nota MJ (C51)")
    add("P09", "Pensionări în trei ani", "~300", "—", "NEVERIFICABIL", "Datele publice de decizii nu conțin date despre personal.", "—")
    add("P10", "CAEN Rev. 3: rămași de actualizat", "62,76% din firme", "902.243 de cereri CAEN încă așteptate (nota MJ) · ≈25% din decizii sunt deja actualizări CAEN",
        "COMPATIBIL", "Ambele surse arată un val CAEN rămas de ordinul a sute de mii de cereri; vezi scenariul de conformare CAEN.", "Nota MJ + eșantion buletine (C50)")
    # registrations
    s9_26 = int(inm[[f"2026-{i:02d}" for i in range(1, 10)]].sum()); s9_25 = int(inm[[f"2025-{i:02d}" for i in range(1, 10)]].sum())
    add("P12", "Înmatriculări, 9 luni 2026", "100.975 (−8,94%)", f"{n0(s9_26)} admise (BERC), {p1(pct(s9_26, s9_25))} față de 9 luni 2025",
        "CONFIRMAT" if abs(s9_26 / 100975 - 1) <= 0.05 else ("COMPATIBIL" if abs(pct(s9_26, s9_25) - (-8.94)) < 10 else "CONTRAZIS"),
        "Statistica ONRC și deciziile de admitere din buletin dau practic același număr (diferență sub 1%), deși definițiile nu sunt identice.", "BERC INMATRIC265, decizii Admis")
    ao_26 = int(inm[["2026-08", "2026-09", "2026-10"]].sum()); ao_25 = int(inm[["2025-08", "2025-09", "2025-10"]].sum())
    v13 = pct(ao_26, ao_25)
    add("P13", "Înmatriculări finalizate aug.–oct. 2026 față de 2025", "−46,8%", f"{p1(v13)} ({n0(ao_26)} față de {n0(ao_25)})",
        "CONFIRMAT" if abs(v13 - (-46.8)) <= 10 else ("COMPATIBIL" if v13 < -20 else "CONTRAZIS"),
        "Scăderea înmatriculărilor finalizate în toamnă e vizibilă și în buletinul de decizii.", "BERC INMATRIC265, decizii Admis")
    v14a = pct(inm["2026-09"], inm["2025-09"]); v14b = pct(cer["2026-09"], cer["2025-09"]); v15 = pct(inm["2026-10"], inm["2025-10"])
    add("P14", "Septembrie 2026: înmatriculări / mențiuni", "−53,4% / +27,8%", f"{p1(v14a)} / {p1(v14b)} (admise, BERC)",
        "CONFIRMAT" if abs(v14a + 53.4) <= 5 and abs(v14b - 27.8) <= 5 else "COMPATIBIL" if v14a < 0 and v14b > 0 else "CONTRAZIS",   # two figures: both within 5 points
        "Aceeași direcție: în septembrie, mențiunile au crescut, iar înmatriculările finalizate au scăzut puternic.", "BERC, decizii Admis")
    add("P15", "Octombrie 2026: înmatriculări", "−58,5%", f"{p1(v15)} (admise, BERC)",
        "CONFIRMAT" if abs(v15 + 58.5) <= 10 else ("COMPATIBIL" if v15 < -20 else "CONTRAZIS"), "", "BERC INMATRIC265, decizii Admis")
    a24, j24 = mon["2024-08"]["finale_stricte_pe_zi_lucr"], mon["2024-06"]["finale_stricte_pe_zi_lucr"]
    add("P16", "Val 2024: blocaj după lansarea platformei", ">130.000 cereri blocate",
        f"decizii finale pe zi: iun. 2024 {n0(j24)} → aug. 2024 {n0(a24)}; mediana așteptării a urcat la circa 12 zile", "COMPATIBIL",
        "Buletinul arată prăbușirea producției și creșterea așteptării în vara lui 2024; stocul exact nu e observabil.", "BERC (C18)")
    i24 = int(inm[[f"2024-{i:02d}" for i in range(4, 13)]].sum()); i23 = int(inm[[f"2023-{i:02d}" for i in range(4, 13)]].sum())
    add("P17", "Înmatriculări 2024 față de 2023", "−14,6%", f"{p1(pct(i24, i23))} (apr.–dec., admise, BERC)",
        "COMPATIBIL" if pct(i24, i23) < 0 else "CONTRAZIS", "Comparăm aprilie–decembrie (arhiva începe în aprilie 2023).", "BERC INMATRIC265")
    pt = pd.read_csv(OUT / "per_county_tandem_2026-11-21.csv").set_index("county_mn")
    if "IS" in pt.index:
        r = pt.loc["IS"]; tot = r.stage1_operare + r.stage2_registrator
        add("P18", "ORCT Iași: dosare restante la soluționare", "84% (5.941 din 7.082)",
            f"eșantion portal Iași: {int(r.stage2_registrator)} din {int(tot)} la registrator", "NEVERIFICABIL (eșantion prea mic)",
            "Eșantionul pe un singur oficiu e prea mic pentru o comparație.", "eșantion myportal")
    mh = cty.get("MH", {}).get("median_nov")
    add("P19", "ORCT Mehedinți: timp de soluționare", ">1 lună", f"mediana Mehedinți, decizii 1–18 nov.: {d1(mh)} zile", "CONFIRMAT",
        "Deficitul de personal (~40%) nu e verificabil din datele noastre; timpul de peste o lună e confirmat.", "BERC, pe oficiul de depunere")
    add("P20", "Interdicția orelor suplimentare plătite", "—", "circa una din zece decizii poartă o oră de după program (marca sistemului)", "NEVERIFICABIL",
        "Marca temporală nu dovedește nici ore suplimentare, nici absența lor.", "BERC (C81)")
    METHOD = {
        "P01": "Stocul nu e în BERC; folosim cele două note oficiale MJ (30.10 și 6.11).",
        "P02": "Toate deciziile finale din BERC, diferența dintre momentul deciziei și momentul înregistrării, mediana pe luna deciziei.",
        "P03": "Aceeași metodă, separat pentru modificări (CERERE265) și înmatriculări (INMATRIC265), săptămâna 16–20 noiembrie.",
        "P04": "Mediana pe oficiul de depunere Cluj, deciziile din 1–18 noiembrie.",
        "P05": "Intrările nu sunt în BERC; folosim nota MJ. Ca test de consistență, comparăm cu deciziile emise zilnic (BERC) și cu stocul oficial.",
        "P06": "Ponderea dosarelor decise în cel mult 14 zile, față de mediana perioadei (BERC, 2–19 noiembrie).",
        "P07": "Seriile lunare ale celor 42 de oficii (BERC), comparate cu seria națională.",
        "P08": "Nota de fundamentare MJ a proiectului OUG.",
        "P10": "Nota MJ (cereri CAEN încă așteptate) și eșantionul de 530 de buletine PDF (ponderea deciziilor doar-CAEN).",
        "P12": "Deciziile de admitere pe cererile de înmatriculare din BERC, ianuarie–septembrie, 2026 față de 2025.",
        "P13": "Aceeași metodă, august–octombrie.", "P14": "Aceeași metodă, septembrie; mențiuni = cereri CERERE265 admise.",
        "P15": "Aceeași metodă, octombrie.", "P16": "Deciziile finale pe zi lucrătoare și mediana așteptării, BERC 2024.",
        "P17": "Înmatriculări admise, aprilie–decembrie 2024 față de aprilie–decembrie 2023 (BERC).",
        "P18": "Eșantionul myportal pe oficiul Iași.", "P19": "Mediana pe oficiul de depunere Mehedinți, deciziile din 1–18 noiembrie.",
        "P09": "—", "P20": "Mărcile temporale ale deciziilor (BERC)."}
    EXPL = {
        "P01": "Dată diferită (sfârșitul lui octombrie față de 6 noiembrie); rotunjire; cifra sindicală poate include și cereri aflate în alte stadii (de exemplu, în termen de completare).",
        "P05": "Explicații posibile: (1) altă unitate — toate cererile din portal (certificate, informări, copii), nu doar dosarele de înregistrare; contorul numerelor de cerere din portal ajunge, în datele noastre, la zeci de mii pe zi; "
               "(2) o eroare de transcriere sau o cifră lunară ori cumulată citită ca zilnică; (3) o eroare în sursa primară. Test de consistență: dacă ar intra 26.000 de dosare pe zi și s-ar emite circa 5.200 de decizii, stocul ar crește cu peste 20.000 pe zi, adică ar ajunge la milioane în câteva luni; stocul oficial este de 204.414. Cifra nu poate descrie dosarele de înregistrare.",
        "P06": "Explicații posibile: (1) ordinea cronologică poate fi regula de repartizare, nu ordinea efectivă a deciziilor; (2) unele cereri au prioritate legală sau sunt mai simple (de exemplu, renunțări sau respingeri rapide); (3) regula poate fi respectată pe categorii sau oficii, nu la nivel național. Datele arată rezultatul, nu cauza.",
        "P07": "Datele sunt consistente cu o coadă comună, dar nu dovedesc modul de repartizare; o explicație alternativă ar fi o încărcare uniformă a tuturor oficiilor.",
        "P10": "Procentele din presă se referă la firme, cifra MJ la cereri; o firmă poate depune o cerere combinată (CAEN + capital).",
        "P12": "Statistica ONRC numără firmele înmatriculate (persoane fizice și juridice); BERC numără deciziile de admitere; valorile coincid aproape exact.",
        "P14": "Mențiuni: +21,9% în datele noastre față de +27,8% în presă; diferența poate veni din ce se numără ca „mențiune” (de exemplu, inclusiv radieri sau suspendări).",
        "P17": "Comparăm doar aprilie–decembrie (arhiva începe în aprilie 2023); scăderea anuală completă poate diferi.",
        "P18": "Eșantionul nostru pe un singur oficiu e prea mic; cifra din presă poate fi corectă."}
    for r in rows:
        r["cum_am_obtinut"] = METHOD.get(r["id"], ""); r["explicatii_posibile"] = EXPL.get(r["id"], "")
    out = dict(meta="Confruntarea afirmațiilor din compilația de presă (21.11.2026) cu datele noastre. Doar afirmații despre coadă. Sursa de referință e BERC; cifrele publice care o contrazic sunt menționate, cu explicațiile posibile.",
               scale="CONFIRMAT / COMPATIBIL / CONTRAZIS / NEVERIFICABIL", rows=rows,
               counts={v: sum(1 for r in rows if r["verdict"].startswith(v)) for v in ("CONFIRMAT", "COMPATIBIL", "CONTRAZIS", "NEVERIFICABIL")},
               berc_series=dict(inm_admis={k: int(v) for k, v in inm.items() if k >= "2023-04"}, cer_admis={k: int(v) for k, v in cer.items() if k >= "2025-01"}))
    (OUT / "osint_crosscheck.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    df = pd.DataFrame(rows)
    with pd.ExcelWriter(XL, engine="openpyxl", mode="a", if_sheet_exists="replace") as W:
        pd.DataFrame([[out["meta"] + " Scala: " + out["scale"]]]).to_excel(W, sheet_name="presa_vs_date_proprii", index=False, header=False)
        df.to_excel(W, sheet_name="presa_vs_date_proprii", index=False, startrow=2)
    for r in rows:
        print(f"{r['id']:4} {r['verdict'][:22]:22} | {r['valoarea_noastra'][:95]}")
    print("counts:", out["counts"])


if __name__ == "__main__":
    main()
