"""Volumul 2 (Anexe statistice) și Volumul 3 (Raport statistic avansat) — format standard de raport tehnic.

Ambele citesc DOAR independent_audit/out/stat_pack.json (tabele) și claims_registry.csv (cifrele din text, prin ID),
deci nu pot diverge de raportul principal. Tabelele de date poartă sursa și amprenta; cifrele din proză poartă [Cxx].

  ..\\..\\venv\\Scripts\\python -X utf8 build_volume_stat.py --vol2
  ..\\..\\venv\\Scripts\\python -X utf8 build_volume_stat.py --vol3
"""
import csv, json, re, sys, html, hashlib, shutil, subprocess, tempfile
from pathlib import Path
import lab_styles as LS
import ai_annex

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
DELIV = ROOT / "analysis" / "raport_executiv_2026-11"
BOOK = "--book" in sys.argv
NOANNEX = "--no-annex" in sys.argv or BOOK
PART = {"label": "", "key": ""}
IA = ROOT / "independent_audit"
SPF = IA / "out" / "stat_pack.json"
SP = json.loads(SPF.read_text(encoding="utf-8"))
SP_SHA = hashlib.sha256(SPF.read_bytes()).hexdigest()
REG = {r["id"]: r for r in csv.DictReader(open(DELIV / "claims_registry.csv", encoding="utf-8"))}
EDGE = Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
AUTHOR = "Ștefan-Lucian Deleanu · stefandeleanu.ro"


def V(cid):
    r = REG[cid]; assert r["status"] in ("PASS", "WARN"), cid
    return r["value"]


# retracted claims (status FAIL), counted from the registry — never typed
_FAIL_IDS = [k for k, r in REG.items() if r["status"] == "FAIL"]
_NFAIL_TXT = {1: "O afirmație", 2: "Două afirmații", 3: "Trei afirmații", 4: "Patru afirmații", 5: "Cinci afirmații", 6: "Șase afirmații",
              7: "Șapte afirmații", 8: "Opt afirmații", 9: "Nouă afirmații", 10: "Zece afirmații"}.get(len(_FAIL_IDS), f"{len(_FAIL_IDS)} de afirmații")


def E(*ids):
    for i in ids:
        assert REG[i]["status"] in ("PASS", "WARN"), i
    return " " + " ".join(f'<span class="eid">[{i}]</span>' for i in ids)


def hl(t): return f'<mark class="hl">{t}</mark>'
def ro(x, d=0):
    if x is None or (isinstance(x, float) and x != x): return "—"
    s = f"{x:,.{d}f}" if isinstance(x, (int, float)) else str(x)
    return s.replace(",", "X").replace(".", ",").replace("X", ".") if isinstance(x, (int, float)) else s


CSS = r"""
@page { size: A4; margin: 21mm 19mm 22mm 19mm;
  @top-left { content: var(--doc); } }
@page { @top-left { content: "%TITLE%"; font: 500 7pt 'IBM Plex Mono', monospace; color: #6b6f73; letter-spacing: .04em; }
        @top-right { content: "%VOL%"; font: 500 7pt 'IBM Plex Mono', monospace; color: #6b6f73; }
        @bottom-left { content: "%AUTHOR%"; font: 400 7pt 'IBM Plex Sans', sans-serif; color: #6b6f73; }
        @bottom-right { content: counter(page); font: 500 8pt 'IBM Plex Mono', monospace; color: #1b1d1f; } }
@page cover { @top-left { content: none; } @top-right { content: none; } @bottom-left { content: none; } @bottom-right { content: none; } }
:root { --ink: #1b1d1f; --ink2: #4a4f54; --ink3: #8a8f94; --rule: #c9c6bf; --accent: #1d5e5a; --tint: #f5f3ee; }
html { font: 400 10.2pt/1.5 'Source Serif 4', Georgia, serif; color: var(--ink); }
body { margin: 0; }
h1, h2, h3, h4 { font-family: 'IBM Plex Sans', sans-serif; color: var(--ink); break-after: avoid; }
h1.sec { font: 600 15pt/1.2 'IBM Plex Sans'; margin: 0 0 3mm; padding-top: 2mm; border-top: .6mm solid var(--ink); break-before: page; }
h2.sub { font: 600 11pt/1.3 'IBM Plex Sans'; margin: 5mm 0 1.5mm; }
h3.sub3 { font: 600 9.6pt/1.3 'IBM Plex Sans'; margin: 3.5mm 0 1mm; color: var(--accent); }
p { margin: 0 0 2.2mm; text-align: justify; hyphens: auto; }
.eid { font: 500 6.6pt 'IBM Plex Mono'; color: var(--ink3); }
mark.hl { background: #ffe680; color: inherit; padding: .2mm .4mm; box-decoration-break: clone; -webkit-box-decoration-break: clone; }
.cover { page: cover; height: 250mm; display: flex; flex-direction: column; justify-content: space-between; }
.cover .eyebrow { font: 500 8pt 'IBM Plex Mono'; letter-spacing: .08em; text-transform: uppercase; color: var(--accent); }
.cover h1 { font: 700 26pt/1.1 'IBM Plex Sans'; margin: 6mm 0 4mm; }
.cover .sub { font: 400 12.5pt/1.45 'Source Serif 4'; color: var(--ink2); max-width: 150mm; }
.cover dl { display: grid; grid-template-columns: 38mm 1fr; gap: 1.5mm 4mm; font: 400 8.6pt/1.45 'IBM Plex Sans'; border-top: .3mm solid var(--rule); padding-top: 3mm; }
.cover dt { font: 600 7pt 'IBM Plex Mono'; text-transform: uppercase; color: var(--ink2); padding-top: .6mm; }
.cover dd { margin: 0; }
.abstract { background: var(--tint); border-left: 1mm solid var(--accent); padding: 3mm 4mm; margin: 2mm 0 4mm; font: 400 9.4pt/1.5 'Source Serif 4'; }
.abstract .lab, .kw .lab { font: 600 7.2pt 'IBM Plex Mono'; text-transform: uppercase; color: var(--accent); letter-spacing: .05em; display: block; margin-bottom: 1mm; }
.kw { font: 400 8.6pt 'IBM Plex Sans'; margin-bottom: 4mm; }
ul.find { margin: 1mm 0 3mm 4mm; padding: 0; } ul.find li { margin-bottom: 1.4mm; }
.toc { list-style: none; padding: 0; margin: 2mm 0; font: 400 9.4pt/1.45 'IBM Plex Sans'; }
.toc li { display: grid; grid-template-columns: 12mm 1fr 12mm; border-bottom: .2mm solid #e4e1da; padding: 1mm 0; }
.toc li.l2 { grid-template-columns: 20mm 1fr 12mm; font-size: 8.4pt; color: var(--ink2); padding: .5mm 0; }
.toc .n { font: 500 8pt 'IBM Plex Mono'; color: var(--ink3); } .toc .pg { text-align: right; font: 500 8.4pt 'IBM Plex Mono'; }
figure { margin: 3mm 0 4mm; break-inside: avoid; }
figure svg { width: 100%; height: auto; }
figcaption { font: 400 8.2pt/1.45 'IBM Plex Sans'; color: var(--ink2); border-top: .2mm solid var(--rule); padding-top: 1.2mm; }
figcaption b, .tcap b { font: 600 7.6pt 'IBM Plex Mono'; color: var(--ink); text-transform: uppercase; letter-spacing: .04em; margin-right: 1.5mm; }
.tcap { font: 600 9pt/1.35 'IBM Plex Sans'; margin: 4mm 0 1mm; break-after: avoid; }
.tnote { font: 400 7.4pt/1.4 'IBM Plex Sans'; color: var(--ink2); margin: 1mm 0 3.5mm; }
table.dt { width: 100%; table-layout: fixed; border-collapse: collapse; font: 400 7.1pt/1.3 'IBM Plex Sans'; }
table.dt.small { font-size: 6.4pt; }
table.dt th { font: 600 6.3pt/1.25 'IBM Plex Mono'; text-transform: uppercase; color: var(--ink2); text-align: left; vertical-align: bottom;
  border-bottom: .35mm solid var(--ink); padding: .8mm .9mm; overflow-wrap: anywhere; }
table.dt td { border-bottom: .15mm solid #e4e1da; padding: .7mm .9mm; vertical-align: top; overflow-wrap: anywhere; }
table.dt td.num { text-align: right; font-variant-numeric: tabular-nums; }
table.dt tr { break-inside: avoid; }
.issue { border: .25mm solid var(--rule); border-left: 1mm solid var(--accent); padding: 2.5mm 3.5mm; margin: 0 0 3.5mm; break-inside: avoid; }
.issue h3 { font: 600 9.8pt 'IBM Plex Sans'; margin: 0 0 1.5mm; }
.issue dl { display: grid; grid-template-columns: 34mm 1fr; gap: 1mm 3mm; margin: 0; font: 400 8.6pt/1.45 'Source Serif 4'; }
.issue dt { font: 600 6.8pt 'IBM Plex Mono'; text-transform: uppercase; color: var(--ink2); padding-top: .7mm; }
.issue dd { margin: 0; }
.formula { font: 400 9.6pt 'IBM Plex Mono'; background: var(--tint); padding: 2mm 3mm; margin: 1.5mm 0 3mm; }
.gl { width: 100%; border-collapse: collapse; font: 400 8.6pt/1.45 'Source Serif 4'; }
.gl td { border-bottom: .15mm solid #e4e1da; padding: 1mm 1.2mm; vertical-align: top; } .gl td:first-child { width: 42mm; font: 600 8.2pt 'IBM Plex Sans'; }
.refs li { margin-bottom: 1.6mm; font-size: 9pt; }
.note { font: 400 8.2pt/1.45 'IBM Plex Sans'; color: var(--ink2); }
"""


# ------------------------------------------------------------------ table renderer
LABELS = {"luna": "Luna", "zile_lucr_legale": "Zile lucr. legale", "zile_cu_decizii": "Zile cu decizii", "finale_largi": "Finale largi",
          "finale_largi_pe_zi_cu_decizii": "Finale largi / zi cu decizii", "finale_stricte_pe_zi_lucr": "Finale stricte / zi lucr.",
          "amanari_pe_zi_lucr": "Amânări / zi lucr.", "cota_amanari_pct": "Amânări % din decizii", "cota_respinse_pct": "Respinse % din finale",
          "W_p25": "W p25", "W_med": "W mediană", "W_p75": "W p75", "W_p90": "W p90", "cota_le2z_pct": "≤2 zile %",
          "med_CERERE": "Mediană modificări", "med_INMATRIC": "Mediană înmatriculări", "saptamana": "Săptămâna (luni)", "n": "n",
          "p90_CERERE": "p90 modificări", "cota_le14z_pct": "≤14 zile %", "luna_dep": "Luna depunerii", "n_portal": "n portal",
          "rezolvate_pct": "Rezolvate %", "mediana_naiva_doar_rezolvate": "Mediană doar rezolvate", "mediana_KM": "Mediană Kaplan–Meier",
          "S_30z": "S(30 zile)", "perioada": "Perioada", "medie": "Medie", "cota_le1z_pct": "≤24 h %", "cota_peste30z_pct": ">30 zile %",
          "zi": "Ziua", "depuneri_pct": "Depuneri %", "decizii_pct": "Decizii %", "ora": "Ora", "an": "Anul",
          "amanari_anterioare": "Amânări anterioare", "decizii_finale_pct": "Decizii finale %", "code": "Cod", "name": "Oficiul (județul)",
          "region": "Regiunea", "n_nov": "n nov.", "median_nov": "Mediană nov.", "p90_nov": "p90 nov.", "median_y25": "Mediană 2025",
          "rejection_pct_2025": "Respinse % 2025", "rejection_pct_crisis": "Respinse % criză", "postponement_action_pct": "Amânate % criză",
          "formation_gt10_pct": "Înmatric. >10 zile lucr. % aug.–nov.", "parametru": "Parametru", "minim": "Minim", "mod": "Mod", "maxim": "Maxim",
          "scenario": "Scenariu", "period": "Perioada", "p10": "p10", "median": "Mediană", "p90": "p90", "median_saved": "Câștig (aceleași simulări)",
          "median_stock": "Stoc median", "id": "ID", "package": "Pachet", "time_to_effect_days": "Zile până la efect", "wait_jun28_p10": "Iun. 2028 p10",
          "wait_jun28_p50": "Iun. 2028 mediană", "wait_jun28_p90": "Iun. 2028 p90", "days_saved_jun28_med": "Zile câștigate (mediană)",
          "origin": "Origine", "test_start": "Început test", "test_end": "Sfârșit test", "test_workdays": "Zile test", "model": "Regula",
          "predicted_per_day": "Prognozat / zi", "observed_per_day": "Observat / zi", "error_percent": "Abatere %",
          "month": "Luna", "mature_observed_per_day": "Observat matur / zi", "spearman_peak": "ρ Spearman cu vârful",
          "wave_removed": "Val eliminat", "peak_days_saved_p10": "Vârf p10", "peak_days_saved_p50": "Vârf mediană", "peak_days_saved_p90": "Vârf p90",
          "june_days_saved_p10": "Iun. 2028 p10", "june_days_saved_p50": "Iun. 2028 mediană", "june_days_saved_p90": "Iun. 2028 p90",
          "relative_to_november": "Față de noiembrie", "d_in": "Δ intrări %", "d_out": "Δ ieșiri %", "june2028_p10": "Iun. 2028 p10",
          "june2028_p50": "Iun. 2028 mediană", "june2028_p90": "Iun. 2028 p90", "peak_p10": "Vârf p10", "peak_p50": "Vârf mediană",
          "peak_p90": "Vârf p90", "stock_june2028_p50": "Stoc iun. 2028 mediană", "days": "Zile cu decizii", "finals_per_day": "Finale / zi",
          "adjourn_share": "Cota amânărilor", "median_wait": "Mediană", "p90_wait": "p90", "data": "Data", "neprelucrate_operare": "Neprelucrate (operare)",
          "la_registrator": "Prelucrate, la registrator", "total": "Total", "stare": "Stare", "verificare": "Verificare", "detaliu": "Detaliu",
          "indicator": "Indicator", "valoare": "Valoare", "observație": "Observație", "cat": "Categorie", "decizii": "Decizii", "pondere_pct": "Pondere %",
          "p50": "p50", "p99": "p99", "p25": "p25", "p75": "p75", "predicted_per_day_": "Prognozat"}
LABELS.update({"urmarire_min_zile": "Urmărire minimă (zile)", "mediana_KM_IC95_inf": "IC 95% inf.", "mediana_KM_IC95_sup": "IC 95% sup.",
               "la_risc_50z": "La risc 50 z", "la_risc_58z": "La risc 58 z", "la_risc_66z": "La risc 66 z",
               "saptamana_depunerii": "Săptămâna depunerii", "pas": "Pas", "dosare": "Dosare",
               "decizii_pe_zi_ian_iun": "Decizii / zi ian.–iun.", "decizii_pe_zi_aug_oct": "Decizii / zi aug.–oct.", "aug_oct_fata_de_ian_iun_pct": "Aug.–oct. față de ian.–iun. %"})
TEXT_COLS = {"pas", "saptamana_depunerii", "luna", "saptamana", "luna_dep", "perioada", "zi", "code", "name", "region", "parametru", "scenario", "period", "id", "package",
             "origin", "test_start", "test_end", "model", "wave_removed", "data", "stare", "verificare", "detaliu", "indicator", "valoare",
             "observație", "cat"}


def col_decimals(rows, col):
    vals = [r.get(col) for r in rows if isinstance(r.get(col), (int, float)) and not isinstance(r.get(col), bool) and r.get(col) == r.get(col)]
    if not vals or all(float(v).is_integer() for v in vals): return 0
    med = sorted(abs(float(v)) for v in vals)[len(vals) // 2]
    return 3 if med < 1 else 2 if med < 10 else 1


FLOOR = {"on": False}
def fmt(v, col, dec=1):
    if v is None or (isinstance(v, float) and v != v): return "—"
    if col == "valoare" and isinstance(v, str) and v.isdigit(): return ro(int(v))
    if FLOOR["on"] and col in ("p10", "median", "p90") and isinstance(v, (int, float)) and v <= 3: return "≤3"
    if isinstance(v, bool): return "da" if v else "nu"
    if isinstance(v, (int, float)):
        if col in ("an", "ora", "month", "test_workdays"): return str(int(v))
        if col in ("d_in", "d_out"): return f"{int(v):+d}"
        if col.startswith(("june2028", "peak_p", "wait_jun28")) and v <= 3: return "≤3"
        return ro(float(v), dec)
    return html.escape(str(v))


TN = {"n": 0}
REGIME_NAMES = {"platforma_veche_2023_iul2024": "Platforma veche (apr. 2023–iul. 2024)", "colaps_portal_nou_2024": "Lansarea portalului (iul.–nov. 2024)",
                "stabil_2025": "Stabil 2025", "2026_inainte_de_val": "2026, înainte de val (ian.–iul.)", "aug_2026": "August 2026",
                "sep_2026": "Septembrie 2026", "oct_2026": "Octombrie 2026", "nov_1_21_2026": "1–20 noiembrie 2026 (arhiva se încheie pe 20.11)"}
def table(key, title, cols=None, small=False, note=None, tid=None, floor=False):
    t = SP[key]; cols = cols or t["columns"]
    FLOOR["on"] = floor
    if key == "regimuri_LOCKED":
        t = dict(t, rows=[dict(r, perioada=REGIME_NAMES.get(r["perioada"], r["perioada"])) for r in t["rows"]])
    th = "".join(f"<th>{LABELS.get(c, c)}</th>" for c in cols)
    dec = {c: col_decimals(t["rows"], c) for c in cols}
    body = "".join("<tr>" + "".join(f'<td class="{"" if c in TEXT_COLS else "num"}">{fmt(r.get(c), c, dec[c])}</td>' for c in cols) + "</tr>" for r in t["rows"])
    TN["n"] += 1; num = tid or f"Tabelul {TN['n']}"
    src_file = t.get("src") or ("county_rankings.json" if key.startswith("rang_") else ("stat_pack_ext.json" if key.startswith(("efort_", "judete_lunar", "judete_pondere", "national_lunar")) else "stat_pack.json"))
    src = f"Sursă: {src_file} → <code>{key}</code>" + (f" (SHA-256 {SP_SHA[:16]}…)" if src_file == "stat_pack.json" else "") + f". {t['meta']}"
    return (f'<div class="tcap"><b>{num}</b>{title}</div><table class="dt{" small" if small else ""}"><thead><tr>{th}</tr></thead>'
            f'<tbody>{body}</tbody></table><div class="tnote">{src}{" " + note if note else ""}</div>')


FN = {"n": 0}
def fig(svg, caption, ids=(), fdir="figures_statistic"):
    LS.FIG_DIR = str(HERE / fdir)
    FN["n"] += 1
    return (f'<figure>{LS.load_inline_svg(svg, svg.split(".")[0] + "_v")}<figcaption><b>Figura {FN["n"]}</b>{caption}'
            f'{E(*ids) if ids else ""}</figcaption></figure>')


def sec(n, title): return f'<h1 class="sec" id="s{n}">{n}. {title}</h1>'
def sub(n, title): return f'<h2 class="sub">{n} {title}</h2>'
def P(t): return f"<p>{t}</p>"


def issue(title, what, effect, done, fix):
    return (f'<div class="issue"><h3>{title}</h3><dl><dt>Problema</dt><dd>{what}</dd><dt>Efect asupra cifrelor</dt><dd>{effect}</dd>'
            f'<dt>Ce am făcut</dt><dd>{done}</dd><dt>Ce ar rezolva-o</dt><dd>{fix}</dd></dl></div>')


def cover(title, sub_, vol, extra):
    if BOOK:
        return ""
    return f"""<section class="cover"><div><div class="eyebrow">{vol} · Coada de la Registrul Comerțului · noiembrie 2026</div>
<h1>{title}</h1><p class="sub">{sub_}</p></div>
<dl><dt>Autor</dt><dd><strong>Ștefan-Lucian Deleanu</strong> · stefandeleanu.ro</dd>
<dt>Date</dt><dd>BERC, 4.077.510 decizii, până la {SP['_meta']['berc_last_decision']} · eșantion myportal de 7.469 de numere de cerere sondate, fără nume, CNP sau date de contact (dintre care {ro(SP['_meta']['portal_n'])} cereri supuse soluționării, cu date complete, folosite pentru Kaplan–Meier) · Nota MJ 30.10 și 6.11.2026</dd>
<dt>Sursa tabelelor</dt><dd><code>stat_pack.json</code>, SHA-256 <code>{SP_SHA[:32]}…</code></dd>
{extra}
<dt>Declarație de interes</dt><dd>Autorul a avut o activitate de înființare de societăți, închisă. În 2024, autorul a semnalat public vulnerabilități ale platformei myportal.</dd>
<dt>Utilizarea AI</dt><dd>{ai_annex.DISCLAIMER}</dd></dl></section>"""


ANNEX = ("", "A", "Anexă · " + ai_annex.TITLE, "AI")
def toc(items, pg):
    if BOOK:
        return ""
    items = list(items) + ([] if NOANNEX else [ANNEX])
    li = "".join(f'<li class="{lvl}"><span class="n">{n}</span><span>{t}</span><span class="pg">{pg.get(k, "")}</span></li>'
                 for lvl, n, t, k in items)
    return f'<section style="break-before: page;"><h2 class="sub" style="font-size:14pt;margin-top:0">Cuprins</h2><ul class="toc">{li}</ul></section>'


# ================================================================== VOLUME 2
def vol2(pg):
    TN["n"] = 0
    S = [("", "S1", "Calitatea datelor și acoperirea", "S1"), ("", "S2", "Serii lunare 2023–2026", "S2"),
         ("", "S3", "Serie săptămânală 2026", "S3"), ("", "S4", "Distribuții și regimuri", "S4"),
         ("", "S5", "Cohorte pe luna depunerii și cenzurare", "S5"), ("", "S6", "Profiluri temporale și publicare", "S6"),
         ("", "S7", "Amânări", "S7"), ("", "S8", "Oficiile județene (ordine alfabetică)", "S8"), ("", "S9", "Stocuri oficiale", "S9"),
         ("", "S10", "Modelul de prognoză: intrări, scenarii, grilă, validare", "S10"), ("", "S11", "Eșantionul myportal: regula de includere", "S11"),
         ("", "S12", "Amprente și reproducere", "S12")]
    b = cover("Anexe statistice", "Volumul 2 al raportului: toate seriile și tabelele de date folosite, cu definiții explicite, sursă și amprentă, pentru verificare și analiză proprie.",
              "Volumul 2", "<dt>Cum se folosește</dt><dd>Fiecare tabel e generat automat din <code>stat_pack.json</code>. Cifrele din raportul principal au coduri [Cxx]; tabelele de aici sunt datele din spatele lor.</dd>")
    b += toc([("", n, t, k) for _, n, t, k in S], pg)
    b += f'<section style="break-before: page;"><h2 class="sub" style="margin-top:0">Convenții</h2>' + P(
        "<b>W</b> = așteptarea, în zile calendaristice, de la înregistrarea cererii până la decizie. <b>Finale stricte</b> = admis, respins, renunțat. "
        "<b>Finale largi</b> = finale stricte plus certificările (definiția folosită pentru [C01]). <b>Zi lucrătoare legală</b> = luni–vineri, fără sărbătorile legale. "
        "<b>Zi cu decizii</b> = zi în care buletinul conține cel puțin o decizie. <b>Pe data deciziei</b> = dosarele grupate după momentul soluționării; "
        "<b>pe data depunerii</b> = după momentul înregistrării. Valorile «≤3» din tabelele modelului sunt limita metricii (coadă practic goală).") + P(
        "Tabelul de județe din această anexă e în ordine alfabetică; clasamentele (cine e primul, cine e ultimul) sunt în Volumul 5 și în fișierul Excel. Diferențele dintre oficii sunt mici, iar oficiul din date e cel de depunere." + E("C75")) + "</section>"
    b += sec("S1", "Calitatea datelor și acoperirea") + table("calitatea_datelor", "Auditul arhivei BERC") + table("categorii", "Decizii pe categorie de buletin")
    b += sec("S2", "Serii lunare 2023–2026") + table("serie_lunara", "Volume și ritmuri, pe luna deciziei",
        ["luna", "zile_lucr_legale", "zile_cu_decizii", "finale_largi", "finale_largi_pe_zi_cu_decizii", "finale_stricte_pe_zi_lucr", "amanari_pe_zi_lucr", "cota_amanari_pct", "cota_respinse_pct"], small=True)
    b += table("serie_lunara", "Timpi de așteptare, pe luna deciziei (finale stricte)",
        ["luna", "W_p25", "W_med", "W_p75", "W_p90", "cota_le2z_pct", "med_CERERE", "med_INMATRIC"], small=True)
    b += sec("S3", "Serie săptămânală 2026") + table("serie_saptamanala_2026", "Așteptarea dosarelor decise, pe săptămâna deciziei", small=True)
    b += sec("S4", "Distribuții și regimuri") + table("distributii_pe_perioade", "Distribuția așteptării pe perioade (zile calendaristice)", small=True) + \
        table("regimuri_LOCKED", "Regimuri pe data deciziei (sursa unică LOCKED_CONSTANTS)", note="Pe vechea platformă (până în iulie 2024), data depunerii e înregistrată fără oră (miezul nopții): duratele din acea perioadă sunt mai mari cu circa jumătate de zi, iar ponderile „în 24 de ore” nu sunt comparabile cu perioadele următoare.")
    b += sec("S5", "Cohorte pe luna depunerii și cenzurare") + table("cohorte_depunere_BERC", "Așteptarea pe luna depunerii, doar dosare deja decise (BERC)") + \
        table("cohorte_KM_portal", "Kaplan–Meier pe luna depunerii, eșantion myportal", small=True, note="Mediana KM lipsește când sub jumătate din cohortă e rezolvată. IC 95% Greenwood (log-log). «La risc» = dosare încă urmărite la acel număr de zile.") + \
        table("KM_septembrie_pe_saptamani", "Cohorta din septembrie, pe săptămâna depunerii", note="Mediana crește cu săptămâna depunerii: cenzurarea e informativă, deci mediana lunară e o limită de jos.")
    b += sec("S6", "Profiluri temporale și publicare") + table("profil_zile_saptamana_2026", "Depuneri și decizii pe zi a săptămânii, 2026") + \
        table("profil_ore_depunere_2026", "Depuneri pe ora înregistrării, 2026", small=True) + table("intarziere_publicare", "Întârzierea publicării în buletin (zile)")
    b += sec("S7", "Amânări") + table("cicluri_amanare_nov2026", "Câte amânări anterioare au avut deciziile finale din noiembrie 2026")
    b += sec("S8", "Oficiile județene (ordine alfabetică)") + table("judete_alfabetic", "Indicatori pe oficiu de depunere", small=True,
        note="Ordine alfabetică; clasamentele sunt în Volumul 5. «Criză» = august–noiembrie 2026.")
    b += sec("S9", "Stocuri oficiale") + table("stocuri_oficiale_MJ", "Stocurile celor două etape la două date oficiale (nivel C)")
    b += sec("S10", "Modelul de prognoză: intrări, scenarii, grilă, validare") + \
        table("model_ipoteze_intrare", "Ipotezele de intrare ale motorului (distribuții triunghiulare)") + \
        table("model_scenarii_OUG", "Scenariile OUG, toate perioadele", small=True, floor=True, note="„pachet” din această familie = OUG + digitalizare + eșalonare; e diferit de pachetele P0–P5 din tabelul următor, construite cu alte ipoteze.") + \
        table("model_pachete", "Pachete de măsuri, iunie 2028", small=True, floor=True) + \
        table("model_grila_completa", "Grila intrări × ieșiri, completă (36 de celule)", small=True) + \
        table("model_valuri", "Contribuția valurilor de cereri", small=True) + table("model_sensibilitate", "Sensibilitatea vârfului la fiecare ipoteză") + \
        table("model_sezonalitate", "Profilul lunar al cererilor") + table("model_validare_capacitate", "Test pe date nevăzute: ritmul de soluționare", small=True) + \
        table("model_validare_cerere", "Verificarea profilului cererii")
    b += sec("S11", "Eșantionul myportal: regula de includere") + table("portal_flux_includere", "De la recoltare la eșantionul Kaplan–Meier") + P(
        "Diferența mare dintre primele două rânduri vine din dosarele pentru care portalul nu a returnat detaliile. Pentru acestea nu avem nici data depunerii, deci nu putem verifica dacă lipsa detaliilor depinde de luna depunerii sau de stadiul dosarului: e o limită a eșantionului. Dosarele rezolvate fără dată a soluției sunt excluse, nu tratate ca nerezolvate.")
    files = [("BERC analysis_decisions.pkl", SP["_meta"]["berc_sha256"]), ("stat_pack.json", SP_SHA)]
    rows = "".join(f"<tr><td>{a}</td><td><code>{h}</code></td></tr>" for a, h in files)
    b += sec("S12", "Amprente și reproducere") + f'<table class="dt"><thead><tr><th style="width:45mm">Fișier</th><th>SHA-256</th></tr></thead><tbody>{rows}</tbody></table>' + P(
        "Reproducere: <code>independent_audit\\stat_pack.py</code> generează toate tabelele de mai sus; <code>build_volume_stat.py --vol2</code> le așază în acest volum. "
        "Amprentele celorlalte fișiere de intrare sunt în coloana <code>data_sha256</code> din <code>claims_registry.csv</code>.")
    return b, S


# ================================================================== VOLUME 3
def vol3(pg):
    TN["n"] = 0; FN["n"] = 0
    lit, adj, cd = SP["little"], SP["adjourn_link"], SP["county_dispersion"]
    S = [("", "·", "Rezumat", "abs"), ("", "1", "Introducere", "1"), ("", "2", "Date", "2"),
         ("", "3", "Definiții și estimatori", "3"), ("", "4", "Metode", "4"), ("", "5", "Rezultate", "5"),
         ("", "6", "Problemele statistice ale registrului", "6"), ("", "7", "Diagnostice și robustețe", "7"), ("", "8", "Limitări", "8"),
         ("", "9", "Concluzii și date necesare", "9"), ("", "G", "Glosar statistic", "G"), ("", "R", "Referințe", "R"), ("", "M", "Anexa M · Formule", "M")]
    b = cover("Raport statistic avansat", "Metodă, estimatori, diagnostice și problemele statistice ale datelor Registrului Comerțului. Varianta extinsă, tehnică, a raportului «Coada de la Registrul Comerțului».",
              "Volumul 3", "<dt>Pentru cine</dt><dd>Statisticieni, analiști și echipe tehnice din ONRC și Ministerul Justiției care vor să verifice sau să refacă analiza.</dd>")
    b += toc([("", n, t, k) for _, n, t, k in S], pg)

    # ---------------- abstract
    b += '<h1 class="sec" id="sabs">Rezumat</h1>'
    b += f'''<div class="abstract"><span class="lab">Rezumat</span>
Analizăm timpul de soluționare la Registrul Comerțului din două surse independente: arhiva oficială BERC, cu 4.077.510 decizii, și un eșantion din portalul myportal, care arată etapa curentă a dosarelor. Măsurăm așteptarea pe data deciziei și pe data depunerii, corectăm cenzurarea la dreapta cu estimatorul Kaplan–Meier, verificăm consistența cu legea lui Little, descriem eterogenitatea pe oficii și testăm sensibilitatea fiecărei cifre la definiții. Prognoza folosește un motor de coadă verificat, cu 2.000 de variante, o grilă de sensibilitate intrări × ieșiri și un test pe date nevăzute. Fiecare cifră din text are un cod din registrul afirmațiilor.{E("C14", "C73", "C76")}</div>
<div class="kw"><span class="lab">Cuvinte-cheie</span>teoria cozilor · cenzurare la dreapta · Kaplan–Meier · legea lui Little · bootstrap · simulare Monte Carlo · analiză de sensibilitate · calitatea datelor administrative</div>
<h2 class="sub">Constatări principale</h2><ul class="find">
<li>{hl("Așteptarea dosarelor de modificare soluționate în 16–20 noiembrie a fost de " + V("C14") + " zile calendaristice; cifra vine din toate deciziile, nu dintr-un eșantion.")}{E("C14", "C77")} Incertitudinea reală vine din definiții.</li>
<li>{hl("Pentru dosarele depuse în septembrie, mediana Kaplan–Meier e de cel puțin circa 58 de zile, nu 39; cenzurarea e informativă, deci și aceasta e o limită de jos.")}{E("C73", "C04")}</li>
<li>{hl("Aceeași cifră se schimbă vizibil după definiția zilei sau a deciziei finale;")} de exemplu, scăderea din august e de circa 10% sau de circa 8%, după numitor.{E("C07")}</li>
<li>{hl("Diferențele dintre oficii sunt mici, iar ordinea lor din 2025 nu prezice 2026;")} clasamentele arată unde apar diferențele (Volumul 5), nu performanța personalului.{E("C75", "C49")}</li>
<li>{hl("Un calcul de tip Little dă un stoc de același ordin de mărime cu cel oficial, dar mai mic;")} într-o coadă care crește e doar o verificare de ordin de mărime.{E("C76")}</li>
<li>{hl("În model, 10% în plus sau în minus la capacitate mută așteptarea din iunie 2028 cu luni;")} sensibilitatea vine din valurile de cereri presupuse pentru 2027.{E("C63", "C67")}</li>
<li>{hl("Cele mai mari goluri de date sunt stocul zilnic pe etape, momentul trecerii dintre etape și intrările zilnice pe tipuri,")} pe care doar ONRC le are (secțiunea 6).</li></ul>'''

    # ---------------- 1
    b += sec("1", "Introducere")
    b += P("Volumul 1 al raportului explică pentru decidenți de ce crește coada la Registrul Comerțului. Acest volum prezintă metoda completă: cum am construit fiecare cifră, ce estimatori am folosit, ce verificări au trecut și ce probleme statistice ridică datele publice. Volumul 2 conține toate tabelele.")
    b += sub("1.1", "Întrebările analizei") + '<ul class="find"><li>Q1. Cât așteaptă un dosar și cum s-a schimbat așteptarea din 2023 până azi?</li><li>Q2. Cât de mult deformează cenzurarea la dreapta măsurătorile pentru lunile recente?</li><li>Q3. Unde se află blocajul: la operare sau la soluționare?</li><li>Q4. Sunt diferențele dintre oficii reale și persistente?</li><li>Q5. Cât de sensibile sunt cifrele la definiții?</li><li>Q6. Ce se întâmplă până în 2028 și cât de sensibil e rezultatul la vitezele de intrare și ieșire?</li></ul>'
    b += sub("1.2", "Principii") + P("Trei reguli au ghidat analiza. Întâi, fiecare cifră e calculată o singură dată, dintr-un fișier blocat, iar textul o citește prin cod. Apoi, două surse independente se verifică una pe alta. În fine, scenariile sunt date ca intervale, nu ca probabilități, iar afirmațiile care nu rezistă la verificare sunt retrase public, nu ascunse.")

    # ---------------- 2
    b += sec("2", "Date")
    b += sub("2.1", "Buletinul Electronic al Registrului Comerțului (BERC)") + P(
        "BERC publică fiecare decizie a registratorului, cu momentul înregistrării cererii, momentul deciziei, momentul publicării, categoria, oficiul și soluția. "
        "Arhiva noastră conține 4.077.510 înregistrări. Ea nu conține cererile încă nesoluționate, identificatorul firmei sau tipul detaliat al cererii.")
    b += table("categorii", "Decizii pe categorie de buletin")
    b += P("Întârzierea dintre decizie și publicare e mică: mediana în 2026 e de " + V("C78").split(" / ")[0] + " zile, iar p99 de " + V("C78").split(" / ")[1] + " zile." + E("C78") +
           " Deci data deciziei din buletin poate fi folosită ca dată reală a deciziei, fără corecție.")
    b += fig("s10_publicare.svg", "Întârzierea publicării în buletin, pe ani (p50, p90, p99; scară logaritmică).", ["C78"])
    b += sub("2.2", "Eșantionul myportal") + P(
        "Portalul arată, pentru un dosar, etapa curentă: în operare, la registrator sau soluționat. Am extras un eșantion de cereri supuse soluționării, cu județul cunoscut pentru toate, "
        "fără date personale. Eșantionul permite două lucruri pe care BERC nu le permite: împărțirea stocului pe cele două etape și observarea dosarelor încă nerezolvate, deci corectarea cenzurării." + E("C06"))
    b += sub("2.3", "Cifre oficiale") + P("Nota de fundamentare a Ministerului Justiției dă stocurile celor două etape la 30 octombrie și 6 noiembrie 2026 și intrările zilnice medii. Le cităm (nivel C) și nu le recalculăm." + E("C28", "C29", "C47"))
    b += table("stocuri_oficiale_MJ", "Stocuri oficiale pe etape")
    b += sub("2.4", "Auditul calității datelor") + table("calitatea_datelor", "Auditul arhivei BERC")

    # ---------------- 3
    b += sec("3", "Definiții și estimatori")
    b += sub("3.1", "Așteptarea") + P("Pentru fiecare decizie, așteptarea W este diferența dintre momentul deciziei și momentul înregistrării, în zile calendaristice. Excludem valorile negative și pe cele de peste 400 de zile, care provin din dosare istorice.")
    b += sub("3.2", "Baza deciziei și baza depunerii") + P(
        "Pe <b>baza deciziei</b>, grupăm dosarele după momentul soluționării. Măsura e completă imediat, dar răspunde la întrebarea „cât de vechi sunt dosarele terminate acum”. "
        "Pe <b>baza depunerii</b>, grupăm după momentul înregistrării. Măsura răspunde la întrebarea „cât va aștepta cine depune acum”, dar e cenzurată până când toate dosarele lunii sunt soluționate. "
        + hl("Cele două baze dau cifre diferite din motive legitime; un raport trebuie să spună mereu pe care o folosește."))
    b += sub("3.3", "Ce este o decizie finală") + P("<b>Finale stricte</b>: admis, respins, renunțat. <b>Finale largi</b>: plus certificările. Amânările nu sunt decizii finale: ele dau un termen de completare de cel mult 15 zile." + E("C03"))
    b += sub("3.4", "Ce este o zi") + P("Folosim trei numitori: zile calendaristice, zile lucrătoare legale (luni–vineri, fără sărbători) și zile cu decizii (zile în care buletinul are cel puțin o decizie). Ultimul e mai mic în lunile cu zile lucrătoare fără activitate și umflă ritmul zilnic.")
    b += sub("3.5", "Sensibilitatea la definiții") + P(
        "Poarta de verificare independentă a arătat că trei cifre depind vizibil de definiție. Scăderea din august e de circa 10% pe zi lucrătoare legală cu finale stricte, dar de circa 8% pe zi cu decizii cu finale largi." + E("C07") +
        " Ponderea dosarelor rezolvate în cel mult două zile înainte și după 27 aprilie diferă după cum o calculăm pe toate deciziile sau ca mediană a județelor." + E("C32") +
        " Diferența de așteptare a cererilor online depuse în afara programului depinde de fereastra orară aleasă." + E("C36") +
        " " + hl("Registrul păstrează pentru fiecare cifră definiția exactă, iar valorile publicate folosesc definiția verificată independent."))
    b += fig("s08_definitii.svg", "Aceeași mărime, două definiții. Stânga: raportul august / iunie–iulie. Centru și dreapta: ponderea deciziilor în cel mult două zile, înainte și după 27 aprilie 2026.", ["C07", "C32"])

    # ---------------- 4
    b += sec("4", "Metode")
    b += sub("4.1", "Statistici descriptive robuste") + P("Distribuțiile așteptării sunt foarte asimetrice. Folosim mediana și cuantilele (p10, p25, p75, p90, p99), nu media, și arătăm funcția de repartiție empirică (ECDF), care arată toată distribuția deodată.")
    b += sub("4.2", "Recensământ, nu eșantion") + P("BERC conține toate deciziile publicate, deci statisticile descriptive nu au eroare de eșantionare. Am calculat totuși un interval bootstrap iid pentru mediana din 16–20 noiembrie, ca să arătăm că întâmplarea nu poate explica nivelul; intervalul ignoră gruparea pe zile și loturi și nu trebuie citit ca precizie." + E("C77") + " Eșantionul myportal, în schimb, e un eșantion propriu-zis: acolo dăm intervale Greenwood.")
    b += sub("4.3", "Cenzurare la dreapta și estimatorul Kaplan–Meier") + P(
        "Pentru o cohortă de depunere, dosarele încă nerezolvate la data extragerii au un timp de așteptare necunoscut, dar mai mare decât timpul scurs. Dacă le ignorăm, mediana iese prea mică. "
        "Estimatorul Kaplan–Meier folosește și aceste dosare, ca observații cenzurate, și estimează funcția de supraviețuire S(t), proporția dosarelor încă nerezolvate după t zile.")
    b += '<div class="formula">Ŝ(t) = ∏<sub>t<sub>i</sub> ≤ t</sub> (1 − d<sub>i</sub> / n<sub>i</sub>)</div>'
    b += P("Aici d<sub>i</sub> e numărul de dosare rezolvate la momentul t<sub>i</sub>, iar n<sub>i</sub> numărul de dosare încă în așteptare chiar înainte de t<sub>i</sub>. Mediana estimată e primul t la care Ŝ(t) ≤ 0,5; intervalul de încredere folosește formula Greenwood cu transformare log-log. " +
           hl("Ipoteza esențială, cenzurarea independentă, nu ține aici:") + " într-o cohortă lunară, cine a depus mai târziu așteaptă mai mult (coada crește) și e urmărit mai puțin. De aceea raportăm și mediana pe săptămâna depunerii și tratăm mediana lunară ca limită de jos." + E("C73"))
    b += sub("4.4", "Legea lui Little") + P("Într-un sistem stabil, stocul mediu L este egal cu ritmul de ieșire λ înmulțit cu timpul mediu în sistem W: L = λW. Sistemul de azi nu e stabil: coada crește, iar dosarele decise acum sunt mai „tinere” decât cele care așteaptă. O folosim doar ca verificare de ordin de mărime, nu ca estimator al stocului." + E("C76"))
    b += sub("4.5", "Modelul în tandem") + P("Un dosar trece prin două servere în serie: operarea și soluționarea. Capacitatea sistemului e minimul celor două capacități. Am folosit bilanțurile oficiale din 30 octombrie și 6 noiembrie pentru a estima capacitatea fiecărei etape și efectul mutării de personal între ele." + E("C33", "C34", "C35"))
    b += sub("4.6", "Motorul de prognoză") + P(
        "Motorul verificat simulează zilnic stocul: stocul de mâine e stocul de azi plus intrările minus ieșirile, fără să coboare sub zero. Intrările combină fluxul obișnuit, cu profil sezonier, și trei valuri anunțate. "
        "Fiecare ipoteză are o distribuție triunghiulară (minim, mod, maxim), independentă de celelalte. Rulăm 2.000 de variante cu o sămânță fixă și raportăm, pentru fiecare dată, mediana și intervalul p10–p90 al așteptării unui dosar depus atunci." + E("C58", "C60"))
    b += P(hl("Două limite trebuie spuse explicit.") + " Întâi, estimandul: așteptarea unui dosar standard servit în ordinea sosirii; coada reală nu e strict cronologică și include cicluri de amânare, deci prognoza descrie dosarul tipic." + E("C38", "C74") +
           " Apoi, intervalele: lățimea lor vine aproape în întregime din ipotezele despre ritmul de soluționare și fluxul obișnuit de cereri (tabelul ipotezelor din Volumul 2); ele nu sunt probabilități estimate din date, iar corelațiile dintre ipoteze nu sunt modelate. O validare a prognozei de așteptare (nu doar a ritmului) va fi posibilă când cohortele din toamnă vor fi complete.")
    b += sub("4.6.1", "De ce e construit modelul așa") + '<ul class="find">' + "".join(f"<li>{x}</li>" for x in [
        "<b>O coadă zilnică, nu o regresie.</b> Așteptarea depinde de stocul acumulat, nu doar de ritmul de azi. O regresie pe serii istorice nu poate reproduce acumularea; recurența zilnică S<sub>t+1</sub> = max(0, S<sub>t</sub> + A<sub>t</sub> − C<sub>t</sub>) o reproduce exact și are proprietăți demonstrate formal (monotonie, Lean T1a, T1b).",
        "<b>Capacitatea e măsurată, nu ajustată.</b> Într-o versiune anterioară, capacitatea fusese ajustată ca modelul să reproducă stocul, iar cifrele se schimbau de la o rulare la alta. Acum ritmul de soluționare vine direct din deciziile publicate, e blocat într-un fișier unic și e validat pe date nevăzute." + E("C01", "C70"),
        "<b>Simulări, nu o singură prognoză.</b> Mărimea valurilor din 2027 (CAEN, capital, fiscal) nu e cunoscută. În loc să alegem o valoare, dăm fiecărei ipoteze un interval plauzibil și rulăm 2.000 de combinații; rezultatul arată cât de mult contează necunoscutele." + E("C69"),
        "<b>Distribuții triunghiulare.</b> Pentru ipoteze fără istoric (valuri viitoare) avem doar un minim, o valoare probabilă și un maxim; distribuția triunghiulară folosește exact atât, fără să inventeze o formă.",
        "<b>Două etape, tratate separat acolo unde contează.</b> Prognoza folosește o singură coadă, pentru că datele publice nu au momentul trecerii dintre etape; efectul mutării de personal între etape e analizat separat, în modelul în tandem, pe bilanțurile oficiale." + E("C35"),
        "<b>Grilă, nu un singur scenariu.</b> Decidenții nu știu exact câte cereri vor veni sau câtă capacitate vor obține; grila arată rezultatul pentru 36 de combinații, astfel încât fiecare își poate citi propria ipoteză." + E("C63"),
        "<b>Același motor pentru toate scenariile.</b> Prognoza, scenariile OUG, pachetele și grila folosesc același motor și aceleași simulări, iar câștigurile se măsoară pe aceleași simulări. Celula fără schimbări a grilei trebuie să reproducă prognoza; altfel calculul se oprește." + E("C44", "C63")]) + "</ul>"
    b += sub("4.7", "Grila de sensibilitate") + P("Aplicăm multiplicatori ficși tuturor intrărilor și întregii capacități, de la −20% la +30% pentru intrări și de la −10% la +40% pentru ieșiri, și rulăm din nou cele 2.000 de variante pentru fiecare dintre cele 36 de combinații. Celula fără schimbări trebuie să reproducă exact prognoza verificată; altfel calculul se oprește." + E("C63"))
    b += sub("4.8", "Sensibilitate și contrafactuale") + P("Măsurăm cât contează fiecare ipoteză prin corelația de rang Spearman dintre valoarea ei și vârful așteptării, pe cele 2.000 de variante. Pentru fiecare val de cereri calculăm câte zile s-ar evita dacă valul nu ar exista, pe aceleași variante." + E("C68", "C69"))
    b += sub("4.9", "Validare pe date nevăzute") + P("Pentru nouă ferestre succesive din 2026, prognozăm ritmul de soluționare din datele disponibile la începutul ferestrei și îl comparăm cu ritmul observat în următoarele patru săptămâni." + E("C70"))
    b += P("Am testat apoi modelul de coadă întreg, pe BERC, din trei origini din trecut (martie, iunie, august 2026). În modul „mecanism”, modelul primește intrările și capacitatea reale și prezice așteptarea medianei pentru fiecare zi de depunere; " +
           hl("eroarea medie față de mediana observată e de " + V("C96").split(" · ")[0].replace("eroare medie ", "") + ", cu o corelație de " + V("C96").split(" · ")[1].replace("corelație ", "") + ".") + E("C96") +
           " În modul „prognoză”, modelul folosește doar ce se știa la origine; când cererea crește, subestimează așteptarea: " + V("C97") + "." + E("C97") +
           " Concluzia: mecanismul e validat; incertitudinea vine din cerere, de aceea prognoza e dată ca grile și scenarii.")
    b += fig("fi23_backtest.svg", "Test pe trecut, origine 1 iunie 2026: așteptarea observată (BERC), refăcută de model cu intrările reale și prognozată fără informații despre val.", ["C96", "C97"], fdir="figures_institutii")
    b += sub("4.10", "Registrul afirmațiilor") + P("Fiecare cifră publicabilă are un cod, o valoare citită automat din ieșirea scriptului, un nivel (observat, model, preluat), o stare (PASS, WARN, FAIL), amprenta datelor și o rezervă obligatorie. Un verificator automat respinge orice cifră din proză fără cod și orice citare a unei afirmații retrase.")

    # ---------------- 5
    b += sec("5", "Rezultate")
    b += sub("5.1", "Regimuri și distribuții") + P(
        "Din 2023 până azi se disting patru regimuri: platforma veche, cu o mediană de sub două zile; lansarea portalului din 2024, cu circa 12 zile; anul 2025, stabil, cu circa trei zile; și criza din 2026." + E("C17", "C18", "C19") +
        " " + hl("În criză, întreaga distribuție s-a mutat spre dreapta: nu doar câteva dosare întârzie, ci aproape toate.") + E("C14"))
    b += fig("s01_ecdf.svg", "Funcția de repartiție empirică a așteptării, pe perioade (finale stricte, data deciziei). Curba din dreapta arată că în octombrie–noiembrie 2026 circa trei sferturi din dosarele decise au așteptat peste o lună (tabelul următor).", ["C14", "C17"])
    b += table("distributii_pe_perioade", "Cuantilele așteptării pe perioade", small=True, note="„≤24 h” = decizie în cel mult 24 de ore calendaristice de la înregistrare; e diferit de „într-o zi lucrătoare” (C31), care include soluționarea în ziua lucrătoare următoare.")
    b += sub("5.2", "Serii lunare") + P("Seria lunară arată că producția zilnică a rămas ridicată în 2026, în timp ce așteptarea a crescut din august. Amânările au rămas o proporție stabilă din decizii." + E("C30", "C21"))
    b += fig("s02_lunar.svg", "Sus: decizii pe zi după trei definiții. Jos: mediana, intervalul p25–p75 și p90 al așteptării, pe luna deciziei.", ["C01", "C30", "C21"])
    b += sub("5.3", "Evoluția săptămânală în 2026") + P(hl("Mediana așteptării dosarelor de modificare soluționate a crescut în fiecare săptămână din octombrie.") + E("C16") +
           " Înmatriculările au urmat aceeași direcție, la un nivel mai scăzut." + E("C15"))
    b += fig("s09_saptamanal.svg", "Mediana și p90 ale așteptării, pe săptămâna deciziei, 2026.", ["C14", "C15", "C16"])
    b += sub("5.4", "Cenzurarea, corectată") + P(
        "Pe baza depunerii, mediana pentru septembrie calculată doar pe dosarele deja decise este de cel puțin 39 de zile." + E("C04") +
        " Estimatorul Kaplan–Meier, aplicat pe eșantionul myportal, include și dosarele încă nerezolvate. " +
        hl("Rezultatul pentru septembrie: " + V("C73").split("→ ")[1] + ", față de " + V("C73").split(" (")[0] + " zile pe dosarele rezolvate.") + E("C73") +
        " Pe săptămâni, mediana crește de la o săptămână de depunere la alta, iar pentru ultimele două săptămâni ale lunii nu se poate încă estima: cenzurarea e informativă. Pentru octombrie și noiembrie, sub jumătate din cohortă e rezolvată.")
    b += table("KM_septembrie_pe_saptamani", "Cohorta din septembrie, pe săptămâna depunerii (Kaplan–Meier)")
    b += fig("s03_km.svg", "Curbele Kaplan–Meier pe luna depunerii (eșantion myportal). Curba arată ce proporție din dosare e încă nerezolvată după un anumit număr de zile.", ["C73"])
    b += fig("s04_cenzurare.svg", "Mediana pe luna depunerii: doar dosare decise (BERC), doar rezolvate (portal) și corectată Kaplan–Meier (portal). Eticheta de jos arată ce parte din cohortă e rezolvată.", ["C73", "C04"])
    b += sub("5.5", "Coada cu două viteze") + P("Dosarele nu se rezolvă strict în ordinea depunerii. În 2–19 noiembrie, o parte din modificări și din înmatriculări au fost rezolvate în cel mult 14 zile, deși mediana era mult mai mare: " + V("C38") + "." + E("C38") +
           " Datele publice nu arată tipul cererii, deci nu putem spune care dosare trec mai repede.")
    b += sub("5.6", "Eterogenitatea pe oficii") + P(
        "Mediana pe oficiu, pentru deciziile din 1–18 noiembrie, variază între " + V("C49").replace("–", " și ") + " zile." + E("C49") +
        " Coeficientul de variație și corelația de rang dintre 2025 și noiembrie 2026 sunt " + V("C75") + "." + E("C75") + " " +
        hl("Ordinea oficiilor din 2025 nu prezice ordinea din 2026.") + " Asta nu dovedește că diferențele din 2025 erau zgomot: între timp coada a devenit națională, iar medianele nu sunt standardizate pe tipul cererii, deci o parte din dispersie poate fi compoziție.")
    b += fig("s05_judete.svg", "Stânga: distribuția medianelor pe cele 42 de oficii (clasamentul cu nume e în Volumul 5). Dreapta: mediana pe oficiu în 2025 față de noiembrie 2026.", ["C49", "C75"])
    b += sub("5.7", "Profiluri temporale") + P("Depunerile au un profil săptămânal și orar clar; o parte apare în afara programului și în weekend, deci exclusiv online. Cererile online depuse în afara programului nu trec mai repede." + E("C36"))
    b += fig("s06_profiluri.svg", "Stânga: ponderea depunerilor și a deciziilor pe zi a săptămânii, 2026. Dreapta: depunerile pe ora înregistrării.", ["C36"])
    b += sub("5.8", "Amânări") + P(
        "Am legat amânările de deciziile finale ale aceluiași dosar, prin număr și dată de depunere. " + hl("Circa unul din cinci dosare soluționate în noiembrie fusese amânat înainte, aproape întotdeauna o singură dată.") + E("C74") +
        " Ca mediană, dosarele cu o amânare anterioară au așteptat puțin mai mult decât cele fără amânare.")
    b += P("Un dosar amânat în noiembrie a așteptat, până la prima amânare și apoi de la ultima amânare până la decizie, " + V("C37") + " zile." + E("C37"))
    b += fig("s07_amanari.svg", "Deciziile finale din 1–20 noiembrie 2026, după numărul de amânări anterioare ale aceluiași dosar.", ["C74"])
    b += sub("5.9", "Respingeri") + P("Ponderea respingerilor în deciziile finale a crescut de la platforma veche la perioada din august 2026: " + V("C39") + "." + E("C39") + " Cu altă bază, numai modificări și înmatriculări, iar în a doua jumătate a lui 2025, când dosarele se rezolvau în circa o zi și jumătate, respingerile erau aproape la fel de frecvente: " + V("C57") + "." + E("C57") + " " + hl("Creșterea respingerilor nu explică, singură, criza."))
    b += sub("5.10", "Consistența cu legea lui Little") + P(
        "Pentru 2–20 noiembrie, ritmul deciziilor finale înmulțit cu timpul mediu în zile lucrătoare dă un stoc implicat, comparat cu stocul oficial: " + V("C76") + "." + E("C76") +
        " Diferența are două explicații: stocul oficial include dosarele încă la operare, iar coada crește, deci dosarele decise azi sunt mai «tinere» decât cele care așteaptă. Rezultatul confirmă doar ordinul de mărime.")
    b += sub("5.11", "Prognoză și grilă de sensibilitate") + P(
        "Fără măsuri, motorul verificat dă o așteptare de " + V("C59") + " zile la mijlocul lui 2027 și un vârf de " + V("C60") + " zile." + E("C59", "C60") +
        " " + hl("Grila arată că raportul dintre ieșiri și intrări decide coada: ieșiri cu 10% mai mari sau mai mici mută așteptarea din iunie 2028 între " +
                 V("C63").split(" · ")[0].split("→ ")[1] + " și " + V("C63").split(" · ")[1].split("→ ")[1].split(" (")[0] + " zile.") + E("C63", "C64"))
    b += fig("fi15_grila.svg", "Grila intrări × ieșiri pe motorul verificat: așteptarea în iunie 2028, cazul central și cazul nefavorabil (p90).", ["C63", "C64", "C65"], fdir="figures_institutii")

    # ---------------- 6
    b += sec("6", "Problemele statistice ale registrului")
    b += P("Această secțiune descrie ce probleme statistice ridică datele publice ale Registrului, cum afectează ele cifrele și ce ar trebui publicat ca să dispară. " +
           hl("Cele mai multe incertitudini ale analizei nu vin din metode, ci din date care există în sistemele ONRC, dar nu sunt publicate."))
    b += issue("6.1 Stocul nu este publicat zilnic",
               "BERC conține doar deciziile. Numărul de cereri care așteaptă nu apare nicăieri zilnic; avem doar două fotografii oficiale.",
               "Stocul trebuie estimat din fluxuri și din eșantion; prognoza pornește de la o valoare incertă.",
               "Folosim stocul oficial MJ ca ancoră și îl verificăm cu o estimare proprie, din numerele de înregistrare și eșantionul myportal; cele două se potrivesc la circa ±10%." + E("C28", "C100"),
               "Publicarea zilnică a stocului pe etape și pe tipuri de cereri.")
    b += issue("6.2 Momentul trecerii dintre etape lipsește",
               "Nu se știe când un dosar trece de la operare la registrator.",
               "Timpul pe fiecare etapă nu se poate măsura; modelul în tandem se bazează pe bilanțuri săptămânale.",
               "Am estimat capacitățile din bilanțurile oficiale și am raportat mecanismul, nu timpi pe etape." + E("C34"),
               "Un câmp cu data și ora trecerii la registrator, în BERC sau în date deschise.")
    b += issue("6.3 Cenzurarea la dreapta",
               "Pentru lunile recente, doar dosarele rapide au fost deja soluționate.",
               "Medianele pe luna depunerii ies fals mici pentru lunile recente.",
               "Raportăm limite de jos („cel puțin”), folosim baza deciziei pentru prezent și Kaplan–Meier pe eșantion." + E("C04", "C11", "C73"),
               "Publicarea cererilor nesoluționate, cu data depunerii, ar permite estimări complete.")
    b += issue("6.4 „Soluționare” are mai multe sensuri",
               "Unele cifre oficiale numără și amânările ca soluționări.",
               "Comparațiile între surse par contradictorii; ritmurile diferă cu circa o cincime.",
               "Separăm explicit deciziile finale de amânări." + E("C48", "C21"),
               "O definiție publicată a „soluționării” și raportarea separată a amânărilor.")
    b += issue("6.5 Numitorul zilnic",
               "Ritmul pe zi depinde de ce zile se numără: calendaristice, lucrătoare legale sau zile cu decizii.",
               "Aceeași scădere din august apare ca circa 10% sau circa 8%.",
               "Folosim zile lucrătoare legale și spunem mereu numitorul." + E("C07"),
               "Raportări oficiale cu numitorul declarat.")
    b += issue("6.6 Identificatorul firmei e doar în datele brute",
               "Arhiva tabelară nu are identificatorul firmei; datele brute ale buletinului îl au.",
               "Fără el, redepunerile și ciclurile de amânare s-ar putea lega doar aproximativ.",
               "Am folosit datele brute: legarea exactă confirmă legarea prin număr și dată, iar redepunerile au fost măsurate cu baza de comparație." + E("C74", "C103"),
               "Un identificator pseudonimizat al firmei în datele deschise.")
    b += issue("6.7 Tipul cererii nu e publicat",
               "Nu se știe care decizii sunt simple actualizări CAEN și care sunt modificări complexe.",
               "Producția în număr de decizii nu e același lucru cu volumul de muncă.",
               "Am estimat ponderea CAEN dintr-un eșantion de buletine PDF, cu interval de încredere." + E("C50"),
               "Un cod al tipului de cerere pe fiecare decizie.")
    b += issue("6.8 Intrările nu sunt publicate direct",
               "Numărul de cereri depuse zilnic nu apare ca atare în datele deschise.",
               "Fără o măsură proprie, intrările ar trebui preluate din nota MJ.",
               "Le-am măsurat din numerele de înregistrare: contorul e național, crește în ordinea depunerii și e practic fără goluri. Rezultatul reproduce cifrele MJ și arată vârful din septembrie." + E("C98", "C99"),
               "Publicarea zilnică a cererilor înregistrate, pe tipuri și oficii.")
    b += issue("6.9 Județul înseamnă oficiul de depunere",
               "Dosarele se repartizează la nivel național; oficiul din buletin e cel de depunere.",
               "Comparațiile pe județe nu măsoară performanța oficiilor.",
               "Arătăm dispersia, persistența și clasamente pe oficii, cu rezerva că oficiul e cel de depunere și că respingerile depind și de solicitanți." + E("C49", "C75", "C89"),
               "Publicarea oficiului sau a echipei care soluționează efectiv.")
    b += issue("6.10 Ordinea de procesare nu e observabilă",
               "Unele dosare trec mult mai repede decât mediana.",
               "Modelele strict cronologice ar greși; nu putem explica de ce unele dosare trec mai repede.",
               "Raportăm coada cu două viteze, fără a-i atribui o cauză." + E("C38"),
               "Publicarea regulilor de prioritate și a categoriilor tratate prioritar.")
    b += issue("6.11 Schimbări de procedură nedocumentate",
               "Din 27 aprilie 2026, aproape niciun dosar nu mai e rezolvat în două zile, în aproape toate județele.",
               "O rupere de serie fără explicație complică orice comparație înainte–după.",
               "Arătăm schimbarea, fără a o explica." + E("C32"),
               "Un jurnal public al schimbărilor de procedură și de sistem informatic.")
    b += issue("6.12 Calendarul și migrările",
               "Weekendurile, sărbătorile și oprirea tehnică din iulie 2024 creează zile fără decizii.",
               "Ritmurile zilnice și seriile săptămânale au vârfuri false.",
               "Folosim calendarul legal și excludem săptămânile cu oprire tehnică." + E("C18"),
               "Publicarea zilelor de oprire tehnică.")
    b += issue("6.13 Valori atipice",
               "Câmpul soluției are grafii diferite; există timpi negativi și dosare foarte vechi.",
               "Fără curățare, cuantilele și ponderile se deplasează.",
               "Am documentat fiecare excludere în auditul calității datelor (tabelul din secțiunea 2.4).",
               "Un vocabular controlat pentru soluții.")
    b += issue("6.14 Eșantionul portal",
               "Eșantionul myportal nu e un sondaj aleator complet: e construit pe intervale de numere de cerere.",
               "Ponderile pe etape și estimările Kaplan–Meier au o incertitudine de eșantionare.",
               "Ponderăm pe intervale și verificăm eșantionul cu cifrele oficiale; ponderea pe etape se potrivește." + E("C06", "C09"),
               "Același indicator publicat direct de ONRC ar face eșantionul inutil.")

    # ---------------- 7
    b += sec("7", "Diagnostice și robustețe")
    b += sub("7.1", "Ce verificări susțin cifrele publicate") + P("Cifrele publicate trec prin patru verificări: sursa unică blocată (o nouă rulare nu poate schimba cifrele existente), registrul afirmațiilor cu verificatorul automat de cifre, o reimplementare separată a cifrelor de nivel A și demonstrațiile Lean pentru aritmetică și monotonie (Volumul 6). O listă mai veche de verificări, scrisă pentru o versiune anterioară a modelului, nu mai e publicată, pentru că descria alt model.")
    b += sub("7.2", "Reimplementare separată") + P("O sesiune de verificare separată, tot cu un model AI, a recalculat din aceeași arhivă, cu cod propriu și toleranțe declarate dinainte, cifrele de nivel A. Nu e o replicare pe date independente, ci o a doua implementare pe aceleași date. Cincisprezece cifre au fost confirmate. Pentru patru, recalculul a dat valori diferite din cauza definițiilor; am adoptat definiția verificată și am publicat schimbarea, iar cifra cea mai sensibilă la definiție a trecut pe WARN." + E("C07", "C32", "C36", "C41"))
    b += sub("7.3", "Afirmații retrase") + P(_NFAIL_TXT + " din versiunile anterioare au fost retrase: un calcul al productivității pe registrator, o clasificare a oficiilor după etapa blocată, o afirmație despre ordinea strict cronologică, scenarii neverificate și o comparație între perioade diferite ale anului. Ele rămân în registru cu starea FAIL, fără valori, ca să se vadă ce s-a corectat.")
    b += sub("7.4", "Ce ar putea schimba concluziile") + P("Concluziile despre prezent, pe baza deciziei, sunt robuste: se sprijină pe toate deciziile publicate. Cele despre cohortele recente, pe baza depunerii, stau pe câteva sute de dosare din portal și au aceeași cenzurare în ambele surse." + E("C09", "C73") +
        " Concluziile despre viitor depind de valurile de cereri anunțate și de ipotezele despre ritmul de soluționare; testul pe date nevăzute validează ritmul pe patru săptămâni, nu prognoza pe 2028." + E("C70"))

    # ---------------- 8
    b += sec("8", "Limitări")
    b += '<ul class="find"><li>Datele publice nu conțin stocul zilnic, momentul trecerii dintre etape, tipul cererii și identificatorul firmei (secțiunea 6).</li><li>Intrările zilnice și stocul sunt estimate din numerele de înregistrare și din eșantion, cu o marjă de circa ±10%.</li><li>Eșantionul myportal e mic pentru lunile recente; estimările Kaplan–Meier pentru septembrie sunt la marginea datelor.</li><li>Modelul presupune că ritmul de soluționare și valurile de cereri urmează distribuțiile declarate; o schimbare de politică ar invalida prognoza.</li><li>Grila presupune schimbări imediate ale capacității; în realitate, capacitatea nouă vine cu întârziere.</li></ul>'

    # ---------------- 9
    b += sec("9", "Concluzii și date necesare")
    b += P(hl("Criza din 2026 nu e o criză de producție, ci un dezechilibru între intrări și capacitate, într-un sistem cu două etape aproape la limită.") + E("C30", "C34", "C67") +
           " Măsurătorile despre prezent sunt solide, iar incertitudinea lor vine din definiții, nu din eșantion. Prognoza arată că mici diferențe de capacitate au efecte mari, deci deciziile de capacitate trebuie luate devreme și dimensionate cu marjă.")
    b += P("Pentru ca analiza să treacă de la estimări la măsurători, ONRC ar trebui să publice:")
    b += '<ul class="find"><li>stocul zilnic pe etape (operare, registrator) și pe tipuri de cereri;</li><li>data și ora trecerii fiecărui dosar la registrator;</li><li>cererile înregistrate zilnic, pe tipuri și oficii;</li><li>un cod al tipului de cerere și un identificator pseudonimizat al firmei pe fiecare decizie;</li><li>personalul activ pe fiecare etapă, pe săptămână;</li><li>un jurnal al schimbărilor de procedură și al opririlor tehnice.</li></ul>'

    # ---------------- glossary, refs, formulas
    gl = [("Așteptare (W)", "Zilele calendaristice dintre înregistrarea cererii și decizie."), ("Bază a deciziei / a depunerii", "Gruparea dosarelor după momentul soluționării, respectiv al înregistrării."),
          ("Bootstrap", "Metodă de estimare a incertitudinii prin reeșantionare repetată cu înlocuire din datele observate."),
          ("Cenzurare la dreapta", "Situația în care pentru unele unități știm doar că evenimentul nu s-a produs până la data observării."),
          ("Coeficient de variație (CV)", "Abaterea standard împărțită la medie; măsoară dispersia relativă."), ("Cohortă", "Grup de dosare depuse în aceeași perioadă."),
          ("Contrafactual", "Calcul al rezultatului într-o situație ipotetică, de exemplu fără un val de cereri."),
          ("Corelație de rang Spearman (ρ)", "Corelația dintre rangurile a două variabile; între −1 și 1."), ("Cuantilă (p10, p90 etc.)", "Valoarea sub care se află procentul indicat din observații."),
          ("Distribuție triunghiulară", "Distribuție definită de un minim, o valoare cea mai probabilă (mod) și un maxim."),
          ("ECDF", "Funcția de repartiție empirică: pentru fiecare x, proporția observațiilor cel mult egale cu x."),
          ("Eșantion", "Subset de dosare observate în detaliu; aici, extras din portalul myportal."),
          ("Finale stricte / largi", "Admis, respins, renunțat / plus certificările."), ("Funcție de supraviețuire S(t)", "Proporția unităților la care evenimentul nu s-a produs până la momentul t."),
          ("Grilă de sensibilitate", "Rezultatele modelului pentru combinații sistematice de ipoteze."), ("Interval de încredere 95%", "Interval care, la repetarea procedurii, ar conține valoarea reală în 95% din cazuri."),
          ("Kaplan–Meier", "Estimator neparametric al funcției de supraviețuire în prezența cenzurării."), ("Legea lui Little", "L = λW: stocul mediu este ritmul de ieșire înmulțit cu timpul mediu în sistem, într-un sistem stabil."),
          ("Limita metricii («≤3»)", "Sub circa trei zile coada e practic goală, iar metrica nu mai distinge valori mai mici."),
          ("Mediană", "Valoarea din mijloc a distribuției."), ("Model în tandem", "Două etape de servire în serie; capacitatea sistemului e minimul celor două."),
          ("Monte Carlo", "Simulare repetată cu valori aleatoare ale ipotezelor, pentru a obține distribuția rezultatelor."),
          ("Nivel A / B / C", "Observat direct / model sau scenariu / cifră preluată dintr-o sursă."), ("PASS / WARN / FAIL", "Starea unei afirmații: verificată / publicabilă doar cu rezervă / retrasă."),
          ("Ponderare", "Corecția contribuției unităților unui eșantion, ca să reprezinte populația."), ("Regim", "Perioadă cu comportament stabil al sistemului."),
          ("Sămânță (seed)", "Valoare inițială a generatorului aleator; asigură reproductibilitatea simulărilor."),
          ("Sezonalitate", "Variația regulată a cererilor de la o lună la alta."), ("Staționar", "Sistem ale cărui caracteristici statistice nu se schimbă în timp."),
          ("Test pe date nevăzute", "Prognoză făcută doar cu datele disponibile la un moment dat, comparată apoi cu realitatea."),
          ("Zi lucrătoare legală", "Luni–vineri, fără sărbătorile legale."), ("Zi cu decizii", "Zi în care buletinul conține cel puțin o decizie.")]
    b += '<h1 class="sec" id="sG">Glosar statistic</h1><table class="gl"><tbody>' + "".join(f"<tr><td>{a}</td><td>{c}</td></tr>" for a, c in gl) + "</tbody></table>"
    refs = ["Efron, B. (1979). Bootstrap methods: another look at the jackknife. <i>The Annals of Statistics</i>, 7(1), 1–26.",
            "Kaplan, E. L., Meier, P. (1958). Nonparametric estimation from incomplete observations. <i>Journal of the American Statistical Association</i>, 53(282), 457–481.",
            "Little, J. D. C. (1961). A proof for the queuing formula L = λW. <i>Operations Research</i>, 9(3), 383–387.",
            "Spearman, C. (1904). The proof and measurement of association between two things. <i>American Journal of Psychology</i>, 15(1), 72–101.",
            "Legea nr. 265/2022 privind registrul comerțului, art. 105, 106, 109 (forma consolidată, legislatie.just.ro, citită la 22.11.2026).",
            "Directiva (UE) 2017/1132, art. 13g alin. (7), privind termenele de constituire online.",
            "Ministerul Justiției, Nota de fundamentare la proiectul de OUG privind activitatea de înregistrare în registrul comerțului (noiembrie 2026).",
            "Buletinul Electronic al Registrului Comerțului (BERC), arhiva deciziilor, aprilie 2023 – noiembrie 2026."]
    b += '<h1 class="sec" id="sR">Referințe</h1><ol class="refs" data-lint="skip">' + "".join(f"<li>{r}</li>" for r in refs) + "</ol>"
    b += '<h1 class="sec" id="sM">Anexa M · Formule</h1>'
    for t, f in [("Așteptarea", "W = t<sub>decizie</sub> − t<sub>înregistrare</sub> (zile calendaristice); se exclud W &lt; 0 și W ≥ 400"),
                 ("Ritm pe zi lucrătoare legală", "λ = N<sub>finale</sub> / Z<sub>lucrătoare legale</sub>"),
                 ("Kaplan–Meier", "Ŝ(t) = ∏<sub>t<sub>i</sub> ≤ t</sub> (1 − d<sub>i</sub>/n<sub>i</sub>); mediana = min{t : Ŝ(t) ≤ 0,5}"),
                 ("Legea lui Little", "L = λ · W̄ (W̄ în zile lucrătoare)"),
                 ("Coada zilnică", "S<sub>t+1</sub> = max(0, S<sub>t</sub> + A<sub>t</sub> − C<sub>t</sub>)"),
                 ("Grila", "A′<sub>t</sub> = (1 + δ<sub>in</sub>) A<sub>t</sub>;  C′<sub>t</sub> = (1 + δ<sub>out</sub>) C<sub>t</sub>"),
                 ("Bootstrap", "IC<sub>95%</sub> = [q<sub>2,5%</sub>, q<sub>97,5%</sub>] ale medianelor din B = 2.000 de reeșantionări"),
                 ("Coeficient de variație", "CV = s / x̄")]:
        b += f"<p><b>{t}.</b></p><div class=\"formula\">{f}</div>"
    return b, S


# ================================================================== BUILD
def book_refs(html_):
    import book_style
    return book_style.book_refs(html_)


BOOK_PARTS = {"vol0": "Partea 1 · Fișe pe profil", "vol2": "Partea 3 · Anexe statistice", "vol3": "Partea 4 · Raport statistic avansat", "vol4": "Partea 5 · Munca din spatele cozii", "vol5": "Partea 6 · Fișe pe județe", "vol6": "Partea 7 · Verificare și încredere"}


def page_html(body, title, vol):
    if BOOK:
        import book_style
        title, vol, body = "COADA DE LA REGISTRUL COMERȚULUI · RAPORT COMPLET", PART["label"] or vol, book_refs(book_style.banner(PART["key"]) + body)
    css = CSS.replace("%TITLE%", title).replace("%VOL%", vol).replace("%AUTHOR%", "Analiză independentă din date deschise · " + AUTHOR)
    if BOOK:
        import book_style
        css += book_style.LAB_BOXES + book_style.margins_css() + ("" if PART["key"] == "vol0" else book_style.FLOW_CSS)
    return f'<!DOCTYPE html><html lang="ro"><head><meta charset="utf-8"><title>{title} · {vol}</title><link rel="stylesheet" href="fonts/fonts.css"><style>{css}</style></head><body>{body}</body></html>'


def compile_pdf(h, pdf):
    if pdf.exists(): pdf.unlink()
    prof = tempfile.mkdtemp(prefix="onrc-inst-edge-")
    try:
        for _try in range(3):
            try:
                subprocess.run([str(EDGE), "--headless=new", "--no-sandbox", "--disable-gpu", "--no-first-run", "--disable-extensions",
                        "--no-pdf-header-footer", f"--user-data-dir={prof}", f"--print-to-pdf={pdf}", h.as_uri()],
                       stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=300)
                break
            except subprocess.TimeoutExpired:
                print('Edge timeout, retrying', _try + 1)
        assert pdf.exists()
    finally:
        shutil.rmtree(prof, ignore_errors=True)


def find_pages(pdf, S):
    import fitz
    d = fitz.open(str(pdf)); pg = {}
    for i in range(2, len(d)):
        lines = [l.strip() for l in d[i].get_text("text").splitlines()]
        for _, n, t, k in S:
            targets = (f"{n}. {t}"[:40],) if (n[0].isdigit() or n.startswith("S") or n == "A") else (t[:40],)
            if k not in pg and any(l.startswith(tg) for l in lines for tg in targets):
                pg[k] = str(i + 1)
    n = len(d); d.close(); return pg, n


def guard(pdf, start):
    """Edge shrinks EVERY element when something overflows: check the section headings (15 pt) and body text."""
    import fitz, collections
    d = fitz.open(str(pdf)); big = 0; sizes = collections.Counter()
    for p in d[start:]:
        for blk in p.get_text("dict")["blocks"]:
            for ln in blk.get("lines", []):
                for sp in ln["spans"]:
                    big = max(big, sp["size"]); sizes[round(sp["size"], 1)] += len(sp["text"])
    d.close()
    print(f"largest heading: {big:.1f} pt · dominant text: {sizes.most_common(1)[0][0]} pt")
    assert big >= 14.5, f"shrunk to fit (headings {big:.1f} pt)"


def build(which):
    import book_style
    PART["key"] = which
    PART["label"] = f"Partea {book_style.PARTS[which][0]} · {book_style.PARTS[which][1]}" if which in book_style.PARTS else ""
    if which == "vol7":
        import impact_economic as IE
        title, vol, fn, stem = IE.VOL
    elif which in ("vol0", "vol4", "vol5", "vol6"):
        import volumes_extra as VX
        title, vol, fn, stem = VX.VOLS[which]
    elif which == "vol2":
        title, vol, fn, stem = "COADA DE LA REGISTRUL COMERȚULUI · ANEXE STATISTICE", "Volumul 2", vol2, "Raport_ONRC_Coada_2026-11_VOL2_Anexe_statistice"
    else:
        title, vol, fn, stem = "COADA DE LA REGISTRUL COMERȚULUI · RAPORT STATISTIC AVANSAT", "Volumul 3", vol3, "Raport_ONRC_Coada_2026-11_VOL3_Raport_statistic_avansat"
    if NOANNEX:
        (DELIV / "_dosar").mkdir(exist_ok=True)
        h = HERE / f"{stem}_dosar.html"; pdf = DELIV / "_dosar" / f"{stem}.pdf"
    else:
        h = HERE / f"{stem}.html"; pdf = DELIV / f"{stem}.pdf"
    def full(pg_):
        body_, S_ = fn(pg_)
        if NOANNEX:
            return body_, list(S_)
        body_ += sec("A", "Anexă · " + ai_annex.TITLE) + ai_annex.body(hl)
        return body_, list(S_) + [ANNEX]
    body, S = full({}); h.write_text(page_html(body, title, vol), encoding="utf-8"); compile_pdf(h, pdf)
    pg, n = find_pages(pdf, S)
    body, S = full(pg); h.write_text(page_html(body, title, vol), encoding="utf-8"); compile_pdf(h, pdf)
    pg2, n2 = find_pages(pdf, S)
    print(f"{vol}: {pdf} · {n2} pages · TOC {pg2}")
    miss = [k for *_, k in S if k not in pg2]
    if miss: print("WARNING missing TOC entries:", miss)
    guard(pdf, 3)


if __name__ == "__main__":
    for w in [a.lstrip("-") for a in sys.argv[1:] if a not in ("--no-annex", "--book")] or ["vol3"]:
        build(w)
