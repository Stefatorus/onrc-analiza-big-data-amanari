"""pachet_reel.md — 20-30 claims for the 10-minute reel, generated FROM the registry.

Voice/screen wording comes from `public_ro` (PASS) or `public_ro` + `rezerva_obligatorie`
(WARN). FAIL claims are refused. Each entry adds the recommended chart and a one-sentence
'cum am calculat'. Order follows the mechanisms CICERO-REELS asked for.
"""
from __future__ import annotations
import csv
from pathlib import Path

DELIV = Path(__file__).resolve().parent.parent / "analysis" / "raport_executiv_2026-11"
REG = {r["id"]: r for r in csv.DictReader(open(DELIV / "claims_registry.csv", encoding="utf-8"))}

# (id, mechanism, recommended chart, how calculated)
PLAN = [
 ("C23", "Reperul legal", "—  (text pe ecran)", "Am citit art. 105 alin. (1) și art. 109 din Legea 265/2022 în forma consolidată de pe legislatie.just.ro (22.11.2026)."),
 ("C17", "Cum era înainte", "Fig. 3.1 istoric", "Mediana zilelor dintre depunere și decizie, pe toate deciziile finale din apr. 2023–iul. 2024."),
 ("C31", "Cum era înainte", "—", "Ponderea deciziilor date în cel mult o zi lucrătoare, cu calendarul legal românesc."),
 ("C14", "Cât se așteaptă acum", "Fig. 2.1 săptămânal", "Mediana zilelor de așteptare a modificărilor soluționate în săptămâna 16–20 noiembrie."),
 ("C16", "Cât se așteaptă acum", "Fig. 2.1 săptămânal", "Aceeași mediană, calculată săptămână de săptămână din 28 septembrie."),
 ("C15", "Cât se așteaptă acum", "Fig. 2.1 săptămânal", "Mediana pentru înmatriculările soluționate în aceeași săptămână."),
 ("C04", "Cât se așteaptă acum", "Fig. 2.2 pe luna depunerii", "Mediana pe luna depunerii, doar pentru dosarele deja soluționate; septembrie e o limită de jos."),
 ("C11", "Cât se așteaptă acum", "Fig. 2.3 cenzurare", "Am numărat câte dosare din fiecare lună au deja o decizie finală."),
 ("C30", "Producția față de intrări", "Fig. 3.2 aceeași perioadă", "Decizii finale pe zi lucrătoare în fereastra 1 oct.–20 nov., an de an."),
 ("C01", "Producția față de intrări", "Fig. 3.2", "Decizii finale pe zi lucrătoare, 1 oct.–20 nov. 2026, din BERC."),
 ("C47", "Producția față de intrări", "—", "Cifra oficială de intrări din Nota MJ din 6 noiembrie, citată cu sursa."),
 ("C07", "Producția față de intrări", "—", "Decizii finale pe zi lucrătoare în august, raportate la iunie–iulie."),
 ("C32", "Sincronizarea din 27 aprilie", "—", "Ponderea deciziilor în cel mult două zile, pe județe, înainte și după 27 aprilie 2026."),
 ("C28", "Cele două cozi", "Fig. 4.1 drumul dosarului", "Stocul oficial din Nota MJ din 6 noiembrie."),
 ("C29", "Cele două cozi", "Fig. 4.1", "Partea neprelucrată a stocului oficial, din aceeași notă."),
 ("C33", "Cele două cozi (bilanț 30.10→6.11)", "Fig. 4.2 bilanț", "Diferența dintre cele două fotografii oficiale ale MJ, pe fiecare etapă."),
 ("C34", "Cele două cozi", "Fig. 4.2", "Raportul dintre debitul operării și al soluționării în 2–6 noiembrie, pe trei convenții de numărare."),
 ("C36", "Online nu ocolește operarea", "—", "Depuneri în afara programului (doar online) vs. în program, în aceeași zi și același județ."),
 ("C49", "Coada e națională", "Fig. 4.3 județe", "Mediana deciziilor din 1–18 noiembrie, pe oficiul de depunere."),
 ("C38", "Dosare care trec mai repede", "—", "Ponderea deciziilor finale date în cel mult 14 zile, 2–19 noiembrie."),
 ("C03", "Amânările", "Fig. 4.1 / Fig. 6.1", "Număr de amânări pe zi lucrătoare în BERC; definiția din art. 106."),
 ("C21", "Amânările", "Fig. 6.1 structura deciziilor", "Ponderea amânărilor în toate actele, pe perioade."),
 ("C37", "Amânările", "—", "Mediana zilelor până la prima amânare și de la ultima amânare la decizie, noiembrie 2026."),
 ("C40", "Bucla respingere → redepunere", "—", "Firme respinse care depun din nou o cerere de același tip în cel mult un an."),
 ("C41", "Directiva 13g", "—", "Firme noi aprobate din prima în 1–20 noiembrie, peste 10 zile lucrătoare."),
 ("C43", "OUG-ul, pe articole", "Fig. 7.1 model auditat", "Modelul de coadă auditat, rulat pe datele curente; mediană și interval p10–p90."),
 ("C42", "OUG-ul, pe articole", "Fig. 7.1", "Același model, fără măsuri."),
 ("C44", "OUG-ul, pe articole", "Fig. 7.1", "Același model, doar cu Art. III."),
 ("C35", "OUG-ul: limita mutării din operare", "Fig. 7.2 tandem", "Capacitatea sistemului când capacitate de operare e mutată 1:1 la soluționare."),
]

NOT_SAY = [
 "„Dosarele se rezolvă strict în ordinea depunerii” — nu e strict (C38).",
 "„Favoritism” / „sărit coada” — cauza dosarelor rapide e necunoscută.",
 "Productivitate sau plafon „per registrator”, comparații cu o „normă” — retras (C02).",
 "Clasamente de performanță ale județelor sau ale oamenilor.",
 "„Producție record” fără precizare — vârful absolut a fost în feb.–mar. 2025.",
 "Comparații între perioade diferite ale anului (ex. noiembrie 2026 vs media 2025) — retras (C20).",
 "„X firme așteaptă acum” — BERC nu arată cererile nerezolvate.",
 "Probabilități pentru scenarii („0,75% șanse”), „137 → 104 zile”, „P6 atinge 3 zile”, „P5 ≥100 zile”, „P1 0 zile”.",
 "Scenariile neauditate 710k–1,1 mil. și „50 de registratori luați din operare” — retrase (C24–C27).",
 "„Septembrie: 39 de zile” fără „cel puțin” — e cenzurat (C04, C05).",
 "Sfaturi despre ziua sau luna depunerii; cifre despre munca după program.",
 "„Tranziție supercritică”, „legea Kleinrock”, „DEFF 1,26”, „prognoza de 265 de zile”, „prognoza înghețată a nimerit”.",
 "„Stocul e 210.000” ca cifră oficială — cifra oficială este 204.414 (C28); 210k e sindicală (C08).",
]


def main():
    lines = ["# Pachet reel — Coada de la Registrul Comerțului (22.11.2026)", "",
             "Generat din `claims_registry.csv`. Formularea pentru voce și ecran = `public_ro` din registru. "
             "Afirmațiile WARN se spun DOAR împreună cu rezerva. Afirmațiile FAIL sunt refuzate de generator.", "",
             "Credit în reel: „analiză big data pe datele din BERC”. Declarație de interes: „activitate de înființare de societăți, închisă”.", ""]
    used = 0; cur = None
    for cid, mech, chart, how in PLAN:
        r = REG[cid]
        assert r["status"] in ("PASS", "WARN"), f"{cid} is {r['status']} — refused"
        if mech != cur:
            lines += [f"## {mech}", ""]; cur = mech
        voice = r["public_ro"] + ((" " + r["rezerva_obligatorie"]) if r["status"] == "WARN" else "")
        lines += [f"### {cid} · {r['status']} · nivel {r['level']}",
                  f"- **Voce:** {voice}",
                  f"- **Ecran:** {r['value']} {r['unit']}".rstrip(),
                  f"- **Grafic:** {chart}",
                  f"- **Cum am calculat:** {how}",
                  f"- **Sursă / script:** {r['source']} · `{r['script']}`",
                  f"- **Rezervă:** {r['rezerva_obligatorie'] or '—'}", ""]
        used += 1
    lines += ["## NU afirma (actualizat 22.11.2026)", ""] + [f"- {x}" for x in NOT_SAY] + [""]
    (DELIV / "pachet_reel.md").write_text("\n".join(lines), encoding="utf-8")
    st = [REG[c]["status"] for c, *_ in PLAN]
    print(f"wrote pachet_reel.md — {used} claims ({st.count('PASS')} PASS, {st.count('WARN')} WARN), {len(NOT_SAY)} NU-afirma rules")


if __name__ == "__main__":
    main()
