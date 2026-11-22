"""Raportul complet: UN SINGUR document pentru instituții, în formatul paginii din ediția executivă.

Ordinea: copertă → cuprins unic (cu destinatarii fiecărei părți) → sinteza executivă → cum se citește → Părțile 1–8
(fiecare începe cu un antet de parte în capul primei pagini, fără pagini de titlu goale) → Metodologia → Utilizarea AI.
Părțile se construiesc în modul „--book”; numerotarea paginilor e continuă și o tipărește browserul (BOOK_START).
Două treceri: prima măsoară lungimea părților, a doua le construiește cu numerele de pagină finale.

  ..\\..\\venv\\Scripts\\python -X utf8 build_raport_complet.py
"""
import os, re, sys, subprocess
from pathlib import Path
import fitz
import build_raport_institutii as R
import book_style as BS
import ai_annex
import methodology

HERE = Path(__file__).resolve().parent
DELIV = R.DELIV
DD = DELIV / "_dosar"; DD.mkdir(exist_ok=True)
IA = HERE.parent.parent / "independent_audit"
OUT = DELIV / "Raport_ONRC_Coada_2026-11_COMPLET.pdf"
TITLE = "COADA DE LA REGISTRUL COMERȚULUI · RAPORT COMPLET"
PY = sys.executable
FILES = {"vol0": "Raport_ONRC_Coada_2026-11_VOL0_Fise_pe_profil.pdf", "main": "Raport_ONRC_Coada_2026-11.pdf",
         "vol7": "Raport_ONRC_Coada_2026-11_VOL7_Impact_economic_si_bugetar.pdf", "vol2": "Raport_ONRC_Coada_2026-11_VOL2_Anexe_statistice.pdf",
         "vol3": "Raport_ONRC_Coada_2026-11_VOL3_Raport_statistic_avansat.pdf", "vol4": "Raport_ONRC_Coada_2026-11_VOL4_Munca_din_spatele_cozii.pdf",
         "vol5": "Raport_ONRC_Coada_2026-11_VOL5_Fise_pe_judete.pdf", "vol6": "Raport_ONRC_Coada_2026-11_VOL6_Verificare.pdf"}
ORDER = sorted(BS.PARTS, key=lambda k: BS.PARTS[k][0])

EXTRA = """
.toc-plain { max-width: none; }
.toc-plain li.p1 { border-top: .35mm solid var(--ink); border-bottom: .2mm solid var(--rule-2); margin-top: 2.2mm; padding-top: 1.8mm; }
.toc-plain li.p1 .tn { color: var(--accent); font-weight: 600; }
.toc-plain li.l2 { padding: .7mm 0; }
.toc-plain li.l2 b { font-weight: 400; }
.tg { display: inline-block; font: 500 6.2pt/1.5 var(--mono); color: var(--ink-2); border: .2mm solid #b9b4a9; border-radius: .6mm;
      padding: 0 .9mm; margin-left: 1.3mm; vertical-align: .3mm; letter-spacing: .02em; }
.tg.all { color: var(--accent); border-color: var(--accent); }
.legend { font: 400 7.6pt/1.5 var(--sans); color: var(--ink-2); margin: 0 0 3mm; }
.legend .tg { margin: 0 .6mm 0 0; }
@page cx-toc { @top-right { content: "Cuprins"; } }
table.toc1 { width: 100%; border-collapse: collapse; }
table.toc1 td { vertical-align: top; }
table.toc1 .tco { border-left: 2.6mm solid #999; padding: 0 0 0 3.2mm; }
table.toc1 tr.r1 .tco { padding-top: 3.2mm; padding-bottom: 1.4mm; }
table.toc1 tr.r1 + tr.r2 .tco { padding-top: .6mm; }
table.toc1 tr.r2 .tco { padding-top: .5mm; padding-bottom: .5mm; font: 400 9.4pt/1.35 var(--sans); color: var(--ink); }
table.toc1 .tno { display: block; font: 600 7.4pt var(--mono); letter-spacing: .08em; text-transform: uppercase; }
table.toc1 .tti { display: block; font: 600 12.5pt/1.2 var(--sans); color: var(--ink); margin: .6mm 0 .8mm; }
table.toc1 .tuse { display: block; font: 400 8.8pt/1.4 var(--serif); color: var(--ink-2); max-width: 140mm; }
table.toc1 .tuse b { font-weight: 600; color: var(--ink); }
table.toc1 .tcont { display: block; font: 400 7.8pt/1.4 var(--sans); color: var(--ink-3); margin-top: .8mm; }
table.toc1 .tno2 { font: 500 7.6pt var(--mono); color: var(--ink-3); display: inline-block; min-width: 13mm; }
table.toc1 .tuse2 { display: block; font: 400 7.8pt/1.3 var(--serif); color: var(--ink-3); margin-left: 13.5mm; }
table.toc1 .tpg { width: 20mm; text-align: right; font: 600 10pt var(--mono); padding-top: 7mm; white-space: nowrap; }
table.toc1 .tpg2 { width: 20mm; text-align: right; font: 400 8.6pt var(--mono); color: var(--ink-2); padding-top: .8mm; }
@page rf-synth { @top-right { content: "Sinteză executivă"; } }
@page rf-guide { @top-right { content: "Cum se citește raportul"; } }
@page cx-meth { @top-right { content: "Anexă · Metodologia"; } }
@page cx-ai { @top-right { content: "Anexă · Utilizarea AI"; } }
"""


def lab_render(body, name, first_page):
    esc = lambda s: s.replace('"', '\\"')
    css = (R.BASE_CSS + f'\n@page {{ @top-left {{ content: "{esc(TITLE)}"; }} @bottom-left {{ content: "{esc(R.FOOT)}"; }} }}\n'
           + R.EXTRA_CSS + EXTRA + BS.margins_css(first_page))
    h = HERE / f"_complet_{name}.html"; pdf = DD / f"_{name}.pdf"
    h.write_text(f'<!DOCTYPE html><html lang="ro"><head><meta charset="utf-8"><title>Coada de la Registrul Comerțului · raport complet</title>'
                 f'<link rel="stylesheet" href="fonts/fonts.css"><style>{css}</style></head><body>{body}</body></html>', encoding="utf-8")
    R.compile_pdf(h, pdf)
    return fitz.open("pdf", pdf.read_bytes())


def build_part(key, first_page):
    env = dict(os.environ, BOOK_START=str(first_page))
    cmd = [PY, "-X", "utf8", "build_raport_institutii.py", "--book"] if key == "main" else [PY, "-X", "utf8", "build_volume_stat.py", "--book", f"--{key}"]
    assert subprocess.run(cmd, cwd=HERE, env=env, stdout=subprocess.DEVNULL).returncode == 0, key


def load(key):
    return fitz.open("pdf", (DD / FILES[key]).read_bytes())


def headings(key, d):
    """(label, title, page index) for chapters (main) or numbered sections (volumes), found by type size."""
    found = []
    for k in range(len(d)):
        if key == "main":
            lines = [l.strip() for l in d[k].get_text("text").splitlines() if l.strip()]
            for q, l in enumerate(lines):          # chapters may start anywhere on the page
                m = re.match(r"^CAPITOLUL (\d+)$", l) or re.match(r"^ANEXA ([A-E])$", l)
                if m and q + 1 < len(lines):
                    t = lines[q + 1]
                    if q + 2 < len(lines) and re.search(r"\b(și|de|a|la|în|pe|cu)$", t) and lines[q + 2][:1].islower():
                        t += " " + lines[q + 2]
                    found.append((("Cap. " if l.startswith("CAP") else "Anexa ") + m.group(1), t, k))
            continue
        for b in d[k].get_text("dict")["blocks"]:
            for ln in b.get("lines", []):
                txt = "".join(s["text"] for s in ln["spans"]).strip(); size = max((s["size"] for s in ln["spans"]), default=0)
                if 13.5 <= size <= 16.5:
                    m = re.match(r"^(S?\d{1,2})\. (.+)$", txt)
                    if m:
                        found.append((m.group(1), m.group(2)[:90], k))
                    elif txt in ("Rezumat", "Glosar statistic", "Referințe") or txt.startswith("Anexa M"):
                        found.append(("", txt, k))
    out, seen = [], set()
    for lab, t, k in found:                        # first occurrence of each heading only
        if (lab, t) not in seen:
            seen.add((lab, t)); out.append((lab, t, k))
    return out


def tags_html(tags):
    return "".join(f'<span class="tg{" all" if t == "TOȚI" else ""}">{t}</span>' for t in tags)


def cover_html(p_syn=None, p_min=None):
    return f"""
<section class="cover">
  <div class="eyebrow">Raport complet · analiză independentă din date deschise · BERC / ONRC / myportal</div>
  <h1>Coada de la Registrul Comerțului</h1>
  <p class="sub">Diagnosticul, prognoza, costul economic și bugetar și soluțiile, cu datele pe județe, munca personalului, metoda statistică și verificarea fiecărei cifre, într-un singur document</p>
  <div class="threads" aria-hidden="true"><i class="t-e"></i><i class="t-s"></i><i class="t-m"></i><i class="t-p"></i></div>
  <p class="verdict">Registrul Comerțului dă azi mai multe decizii pe zi decât în aceeași perioadă a anilor trecuți. Totuși, un dosar soluționat la jumătatea lui noiembrie a așteptat aproape două luni, iar legea cere o zi lucrătoare.</p>
  <p class="verdict-sub">Sinteza executivă urmează imediat după cuprins{f" (p. {p_syn})" if p_syn else ""}; ce se poate decide în următoarele 30 de zile e în fișa pentru ministru{f" (p. {p_min})" if p_min else ""}. Cuprinsul arată, pentru fiecare parte și capitol, pentru cine e relevant. Fiecare cifră are un cod (de exemplu [C14]) care duce, în registrul afirmațiilor, la sursă, la scriptul care o calculează și la amprenta datelor.</p>
  <dl class="meta">
    <dt>Autor</dt><dd><strong>Ștefan-Lucian Deleanu</strong> · stefandeleanu.ro</dd>
    <dt>Bază empirică</dt><dd>4.077.510 decizii BERC, până la 20.11.2026 · eșantion myportal de 7.469 de numere de cerere sondate · notele Ministerului Justiției din 30.10 și 6.11.2026 · situațiile financiare depuse la Ministerul Finanțelor. Cifrele din presă sunt comparate cu datele noastre, nu le înlocuiesc.</dd>
    <dt>Ediție și dată</dt><dd>Raport complet pentru instituții · 22 noiembrie 2026</dd>
    <dt>Fișiere atașate</dt><dd>Date_ONRC_Coada_2026-11.xlsx (toate tabelele), claims_registry.csv (registrul afirmațiilor), compilația de presă folosită pentru comparație.</dd>
    <dt>Declarație de interes</dt><dd>Autorul a avut o activitate de înființare de societăți, închisă. În 2024, autorul a semnalat public vulnerabilități ale platformei myportal.</dd>
    <dt>Utilizarea AI</dt><dd>{ai_annex.DISCLAIMER}</dd>
  </dl>
</section>"""


DETAIL = {"vol0", "main", "vol7"}          # parts listed chapter by chapter; the analytic parts get one row each
SHEET_USE = {"1": "Ce se poate decide în următoarele 30 de zile", "2": "Unde e blocajul între cele două etape", "3": "Ce trebuie construit și cum se verifică",
             "4": "Metoda, cenzurarea, ce nu se poate măsura", "5": "Termenele legale și ce înseamnă pentru clienți", "6": "Volumul de muncă, prezentat onest",
             "7": "Cât durează acum și cum vă pregătiți", "8": "Costul pentru buget și ce se poate măsura"}
VOL7_USE = {"1": "Cifrele-cheie, într-o pagină", "2": "Ce e măsurat și ce e presupus", "3": "Graficul lunar, 2024–2026", "4": "Scenariile pentru august–noiembrie 2026",
            "5": "Încasări afectate și costul unei zile în plus", "6": "Ce ipoteză cântărește cel mai mult", "7": "Testul de robustețe și comparația cu bugetul OUG",
            "8": "Efectul cauzal al așteptării și veniturile din 2027 încasate mai târziu", "9": "Ce date ar face cifra sigură", "10": "Toate tabelele"}


def chapter_uses():
    f = R.front({})
    return {m.group(1): m.group(3) for m in re.finditer(r'<span class="tn">(Cap\. \d+|Anexa [A-E]|Front)</span><span><b>(.*?)</b><span class="tsub">(.*?)</span>', f)}


AUD = {"MJ": "MJ", "MF": "MF", "ANAF": "ANAF", "ONRC": "ONRC", "GUV": "Guvern", "PARL": "Parlament", "IT": "IT", "SIND": "sindicat",
       "PROF": "juriști, contabili", "STAT": "statisticieni", "PUBLIC": "public", "TOȚI": "toți"}


def toc_html(rows):
    tr = []
    for lvl, tn, title, use, p0, p1, tags, color in rows:
        who = ", ".join(AUD.get(t, t) for t in tags)
        if lvl == 1:
            pages = f"{p0}–{p1}" if p1 > p0 else f"{p0}"
            tr.append(f'<tr class="r1"><td class="tco" style="border-left-color:{color}"><span class="tno" style="color:{color}">{tn}</span>'
                      f'<span class="tti">{title}</span><span class="tuse">{use}{" · <b>Pentru:</b> " + who if who else ""}</span></td>'
                      f'<td class="tpg">{pages}</td></tr>')
        else:
            tr.append(f'<tr class="r2"><td class="tco" style="border-left-color:{color}"><span class="tno2">{tn}</span> {title}'
                      f'{"<span class=tuse2>" + use + (" · " + who if who else "") + "</span>" if use or who else ""}</td><td class="tpg2">{p0}</td></tr>')
    return f"""
<section class="front" style="page: cx-toc;">
  <div class="eyebrow">Structura raportului</div><h2>Cuprins</h2>
  <p class="legend">Primele pagini dau imaginea completă: sinteza executivă, ghidul de lectură și fișele pentru decidenți. Restul se consultă după nevoie. Fiecare parte are o culoare, aceeași cu banda din marginea paginilor ei. MJ = Ministerul Justiției · MF = Ministerul Finanțelor · ONRC = conducerea și oficiile Registrului.</p>
  <table class="dt toc1"><tbody>{"".join(tr)}</tbody></table>
</section>"""


def front_sections():
    """The main report's executive synthesis and reading guide, placed at the front of the complete report."""
    f = R.front({})
    synth = re.search(r'<section class="front front-synth".*?\n</section>', f, re.S).group(0)
    guide = re.search(r'<section class="front front-guide".*?\n</section>', f, re.S).group(0)
    fix = lambda h: BS.book_refs(re.sub(r"\b([Cc])apitolul (\d+)\b", r"\1apitolul \2 din Partea 2", h))
    return fix(synth), fix(guide)


def annex_html():
    return BS.book_refs(f'<section class="chapter" style="page: cx-meth;"><div class="copen"><div class="cnum">Anexă</div><h2>{methodology.TITLE}</h2></div>'
            f'{methodology.body(R.hl)}</section>'
            f'<section class="chapter" style="page: cx-ai;"><div class="copen"><div class="cnum">Anexă</div><h2>{ai_annex.TITLE}</h2></div>'
            f'{ai_annex.body(R.hl)}</section>')


def layout(front_pages, lens, heads, annex_len, ai_k):
    """front_pages = (n_cover_toc, n_synth, n_guide). Returns starts, annex start, total, TOC rows (with page ranges), bookmarks."""
    n_ct, n_syn, n_gd = front_pages
    p = n_ct + n_syn + n_gd + 1; starts = {}
    for key in ORDER:
        starts[key] = p; p += lens[key]
    annex_start = p; total = p + annex_len - 1
    uses = chapter_uses()
    for lab_, title_ in ((lab, t) for k in heads for lab, t, _ in heads[k]):    # no TOC line that repeats its own title
        u = uses.get(lab_, "")
        if ": " in u and u.split(": ", 1)[0].lower() in title_.lower():
            u = u.split(": ", 1)[1]; uses[lab_] = u[:1].upper() + u[1:]
    rows, marks = [], []
    FC = BS.COLORS["front"]
    rows.append((1, "Începeți aici", "Sinteză executivă", "Totul în câteva pagini, inclusiv costul economic și bugetar", n_ct + 1, n_ct + n_syn, ["TOȚI"], FC))
    rows.append((1, "", "Cum se citește raportul", "Marcajele, unitățile și cuvintele folosite des", n_ct + n_syn + 1, n_ct + n_syn + n_gd, ["TOȚI"], FC))
    marks += [(1, "Sinteză executivă", n_ct + 1), (1, "Cum se citește raportul", n_ct + n_syn + 1)]
    for idx, key in enumerate(ORDER):
        no, t, w = BS.PARTS[key]
        end = (starts[ORDER[idx + 1]] if idx + 1 < len(ORDER) else annex_start) - 1
        hs = [(lab, title, starts[key] + k) for lab, title, k in heads[key]]
        marks.append((1, f"Partea {no} · {t}", starts[key])); marks += [(2, f"{lab} · {title}" if lab else title, pg) for lab, title, pg in hs]
        if key in DETAIL:
            rows.append((1, f"Partea {no}", t, w, starts[key], end, BS.TAGS_PART[key], BS.COLORS[key]))
            for n, (lab, title, pg) in enumerate(hs):
                nxt = hs[n + 1][2] if n + 1 < len(hs) else end + 1
                use = uses.get(lab, "") if key == "main" else (SHEET_USE.get(lab, "") if key == "vol0" else VOL7_USE.get(lab, ""))
                rows.append((2, lab, title, use, pg, max(pg, nxt - 1), BS.TAGS_SUB.get(key, {}).get(lab, []), BS.COLORS[key]))
        else:
            secs = "; ".join(f"{lab} {title}".strip() for lab, title, _ in hs)
            rows.append((1, f"Partea {no}", t, f"{w} <span class='tcont'>Conține: {secs}.</span>", starts[key], end, BS.TAGS_PART[key], BS.COLORS[key]))
    AC = BS.COLORS["annex"]
    rows += [(1, "Anexă", methodology.TITLE, "Metoda întreagă, în proză: date, măsuri, model, verificări, riscuri", annex_start, annex_start + ai_k - 1, ["TOȚI"], AC),
             (1, "Anexă", ai_annex.TITLE, "Cum a fost folosit AI-ul, ce a verificat autorul, surse, limite și incertitudini", annex_start + ai_k, total, ["TOȚI"], AC)]
    marks += [(1, f"Anexă · {methodology.TITLE}", annex_start), (1, f"Anexă · {ai_annex.TITLE}", annex_start + ai_k)]
    return starts, annex_start, total, rows, marks


def main():
    REUSE = "--reuse" in sys.argv                       # parts on disk already carry their final page numbers
    for key in ([] if REUSE else ORDER):                # pass 1: lengths and headings
        build_part(key, 1)
    parts = {k: load(k) for k in ORDER}
    lens = {k: len(d) for k, d in parts.items()}; heads = {k: headings(k, d) for k, d in parts.items()}
    annex = lab_render(annex_html(), "anexe", 1)
    ai_k = next(k for k in range(len(annex)) if ai_annex.TITLE in annex[k].get_text("text")[:900])
    synth, guide = front_sections()
    n_ct = 3
    for _ in range(6):
        sg = lab_render(synth + guide, "sinteza", 1)                # measure synthesis + guide lengths
        n_syn = next(k for k in range(len(sg)) if "Cum se citește raportul" in sg[k].get_text("text")[:400])
        fp = (n_ct, n_syn, len(sg) - n_syn)
        starts, annex_start, total, rows, marks = layout(fp, lens, heads, len(annex), ai_k)
        ct = lab_render(cover_html(n_ct + 1, starts["vol0"]) + toc_html(rows), "fata", 1)
        if len(ct) == n_ct:
            break
        n_ct = len(ct)
    sg = lab_render(synth + guide, "sinteza", n_ct + 1)
    assert len(sg) == fp[1] + fp[2]
    for key in ([] if REUSE else ORDER):                # pass 2: final page numbers
        build_part(key, starts[key])
    parts = {k: load(k) for k in ORDER}
    assert {k: len(d) for k, d in parts.items()} == lens, ({k: len(d) for k, d in parts.items()}, lens)
    annex = lab_render(annex_html(), "anexe", annex_start)
    out = fitz.open(); out.insert_pdf(ct); out.insert_pdf(sg)
    for key in ORDER:
        out.insert_pdf(parts[key])
    out.insert_pdf(annex)
    N = len(out); assert N == total, (N, total)
    def band(page, color, width_mm):
        h = color.lstrip("#"); rgb = tuple(int(h[k:k + 2], 16) / 255 for k in (0, 2, 4))
        page.draw_rect(fitz.Rect(0, 0, width_mm * 72 / 25.4, page.rect.height), color=None, fill=rgb, overlay=True)
    spans = [("front", 1, n_ct + fp[1] + fp[2] - 1)] + [(k, starts[k] - 1, starts[k] - 1 + lens[k] - 1) for k in ORDER] + [("annex", annex_start - 1, total - 1)]
    for key, a0, a1 in spans:
        for i in range(max(a0, 1), a1 + 1):
            band(out[i], BS.COLORS[key], 5.5 if (i == a0 and key not in ("front", "annex")) else 2.2)
    for i in range(1, N):                               # every page after the cover prints its own position
        if not re.search(rf"(^|\n){i + 1}\s*(\n|$)", out[i].get_text("text")):
            raise AssertionError(f"page {i + 1}: printed page number missing or wrong")
    out.set_toc([[1, "Copertă", 1], [1, "Cuprins", 2]] + [[lvl, t, pg] for lvl, t, pg in marks])
    for path, desc in ((DELIV / "Date_ONRC_Coada_2026-11.xlsx", "Toate tabelele de date"),
                       (DELIV / "claims_registry.csv", "Registrul afirmațiilor: fiecare cifră, cu sursă, script, amprentă și stare"),
                       (IA / "osint" / "compilatie_presa_2026-11-21.md", "Afirmațiile din presă comparate cu datele noastre (doar despre coadă)")):
        out.embfile_add(path.name, path.read_bytes(), filename=path.name, desc=desc)
    out.set_metadata({"title": "Coada de la Registrul Comerțului — raport complet (noiembrie 2026)", "author": "Ștefan-Lucian Deleanu",
                      "subject": "Analiză independentă din date deschise; realizată cu ajutorul AI (Claude Opus 5.5, Gemini 4 Neon), sub verificarea autorului",
                      "keywords": "ONRC, Registrul Comerțului, BERC, coadă, prognoză, OUG, impact economic"})
    tmp = OUT.with_name(OUT.stem + "_tmp.pdf"); out.save(str(tmp), garbage=3, deflate=True)
    dest = OUT
    try:
        os.replace(tmp, OUT)
    except PermissionError:                              # the previous file is open in a viewer: _nou, then _nou2, _nou3 ...
        for k in range(1, 10):
            dest = OUT.with_name(OUT.stem + ("_nou.pdf" if k == 1 else f"_nou{k}.pdf"))
            try:
                os.replace(tmp, dest); break
            except PermissionError:
                continue
        print(f"NOTE: {OUT.name} is open in another program; saved as {dest.name}")
    import add_pdf_links                                 # internal links: TOC rows, [Cxx] → register row, cross-references, head → TOC
    add_pdf_links.main(str(dest), str(dest))
    for old in ("Dosar_ONRC_Coada_2026-11_COMPLET.pdf",):
        if (DELIV / old).exists(): (DELIV / old).unlink()
    print(f"RAPORT COMPLET: {dest} · {N} pages · front {fp} · parts start {starts} · annex {annex_start} · TOC rows {len(rows)} · bookmarks {len(marks)} · embedded {out.embfile_count()}")


if __name__ == "__main__":
    main()
