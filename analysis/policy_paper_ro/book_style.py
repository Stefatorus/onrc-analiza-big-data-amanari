"""Page format and structure of the complete report.

- Page chrome: the executive edition's Lab margin boxes everywhere, symmetric margins (parts are merged at arbitrary
  page parity) and a page counter that starts at the part's page in the complete report (BOOK_START).
- Structure: part numbers, banners at the top of each part (no near-empty title pages), the mapping of the
  standalone volume numbers to parts, and who each part is for (labels in the single table of contents).
"""
import os
import re

INK, INK3 = "#1b1d1f", "#6b7178"

# edition of the whole document set: change it here only
VERSION = "1.0.2"
VERSION_DATE = "23.11.2026"
VERSION_DATE_LONG = "23 noiembrie 2026"
# the number is wrapped in <code> so the number linter treats it as structural, not as a data figure
VERSION_HTML = f'<span class="ver">versiunea <code>{VERSION}</code></span>'
VERSION_FOOT = f"v{VERSION}"
VERSION_CSS = ".ver code { font: inherit; color: inherit; background: none; padding: 0; border: 0; }"
VERSION_NOTE = (f'<span class="ver">Versiunea <code>{VERSION}</code></span> ({VERSION_DATE}): precizări după a doua rundă de verificare '
                "(formulări, intervale, termen); valorile din registrul afirmațiilor sunt neschimbate. "
                f'<span class="ver">Versiunea <code>1.0.1</code></span> ({VERSION_DATE}): corecturi după revizuirea critică '
                "(formulări, coerența cifrelor, încadrarea riscului bugetar); s-au corectat doar câteva rotunjiri și formulări din text.")

# builder key -> (part no, title, description); order = order in the complete report
PARTS = {
    "vol0": (1, "Fișe pe profil", "O pagină pentru fiecare cititor: ce trebuie să știe, ce poate face și unde găsește detaliile. Se pot tăia și distribui separat."),
    "main": (2, "Raportul principal", "Diagnosticul, prognoza, grila de risc, proiectul de OUG, soluțiile, încrederea în cifre, sursele noastre și sursele publice."),
    "vol7": (3, "Impactul economic și bugetar", "Cât costă întârzierile economia și bugetul, lună de lună: ce se măsoară, ce se presupune, cât de sigure sunt cifrele."),
    "vol2": (4, "Anexe statistice", "Toate tabelele, cu definiții, sursă și amprentă."),
    "vol3": (5, "Raport statistic avansat", "Metoda, estimatorii, testul modelului pe trecut și problemele statistice ale datelor."),
    "vol4": (6, "Munca din spatele cozii", "Volumul de muncă la nivel de sistem, prezentat onest."),
    "vol5": (7, "Fișe pe județe", "Clasamente care arată unde sunt problemele, serii lunare și indicatori pe oficii."),
    "vol6": (8, "Verificare și încredere", "Registrul afirmațiilor, recalculul independent, demonstrațiile Lean, revizuirea pe profiluri."),
}
# colour code of the parts (left band on every page of the part, part header, table of contents)
COLORS = {"front": "#1b1d1f", "vol0": "#1d5e5a", "main": "#1f3b5c", "vol7": "#a0700b", "vol2": "#5b4a8a",
          "vol3": "#2f6f95", "vol4": "#a8322d", "vol5": "#3f6b2f", "vol6": "#4a5560", "annex": "#8a8f96"}
VOL_TO_KEY = {"0": "vol0", "1": "main", "2": "vol2", "3": "vol3", "4": "vol4", "5": "vol5", "6": "vol6", "7": "vol7"}

# who each part / chapter is for (labels in the table of contents)
LEGEND = [("MJ", "Ministerul Justiției"), ("MF", "Ministerul Finanțelor"), ("ANAF", "ANAF"), ("ONRC", "conducerea și oficiile Registrului"),
          ("GUV", "Guvernul (decizia pe OUG)"), ("PARL", "Parlamentul"), ("IT", "echipa tehnică"), ("SIND", "personal și sindicat"),
          ("PROF", "juriști, notari, contabili"), ("STAT", "statisticieni, INS, analiști"), ("PUBLIC", "antreprenori și public"), ("TOȚI", "toți cititorii")]
TAGS_PART = {"vol0": ["TOȚI"], "main": ["MJ", "GUV", "ONRC", "MF"], "vol7": ["MF", "ANAF", "MJ", "GUV"], "vol2": ["STAT", "ONRC"],
             "vol3": ["STAT"], "vol4": ["SIND", "ONRC", "MF"], "vol5": ["ONRC", "MJ"], "vol6": ["STAT", "TOȚI"]}
TAGS_SUB = {
    "vol0": {"1": ["MJ", "GUV"], "2": ["ONRC"], "3": ["IT"], "4": ["STAT"], "5": ["PROF"], "6": ["SIND"], "7": ["PUBLIC"], "8": ["MF", "ANAF"], "9": ["TOȚI"]},
    "main": {"Cap. 1": ["MJ", "PARL"], "Cap. 2": ["ONRC", "MJ"], "Cap. 3": ["ONRC", "MJ"], "Cap. 4": ["ONRC"], "Cap. 5": ["ONRC", "MJ"],
             "Cap. 6": ["ONRC", "PROF", "IT"], "Cap. 7": ["MJ", "MF", "GUV"], "Cap. 8": ["MJ", "MF"], "Cap. 9": ["MJ", "GUV", "MF", "PARL"],
             "Cap. 10": ["MJ", "ONRC", "IT", "GUV"], "Cap. 11": ["STAT"], "Cap. 12": ["MJ", "TOȚI"], "Anexa A": ["TOȚI"], "Anexa B": ["STAT"], "Anexa C": ["STAT"]},
    "vol7": {"1": ["MF", "MJ", "GUV"], "2": ["MF", "STAT"], "3": ["MF", "ANAF"], "4": ["MF", "MJ"], "5": ["MF", "ANAF"], "6": ["STAT", "MF"], "7": ["MF", "GUV"], "8": ["MF", "STAT"], "9": ["MF", "ANAF", "ONRC"]},
}


def book_refs(html_):
    """In the complete report the volumes are parts: Volumul N -> Partea M."""
    # the executive synthesis opens the complete report (it is not inside Part 2) and there is no separate executive edition
    html_ = re.sub(r"Volumul 1, sinteza \(p\. \d+\), ", "sinteza executivă de la începutul raportului; Volumul 1, ", html_)
    html_ = re.sub(r"Volumul 1, sinteza și ", "sinteza executivă; Volumul 1, ", html_)
    html_ = html_.replace("; ediția executivă.", ".")
    html_ = re.sub(r"\bacest volum\b(?! de)", "această parte", html_)
    html_ = re.sub(r"Volumul ([0-7])", lambda m: f"Partea {PARTS[VOL_TO_KEY[m.group(1)]][0]}", html_)
    html_ = re.sub(r"(?<![\w>])[Aa]nexa B\b", "registrul afirmațiilor (Partea 8)", html_)
    return re.sub(r"(?<![\w>])[Aa]nexa C\b", "Partea 8 („Cum reproduceți”)", html_)


def banner(key):
    no, title, what = PARTS[key]
    c = COLORS[key]
    return (f'<div class="part-banner{" compact" if key == "vol0" else ""}" style="border-top-color:{c}">'
            f'<div class="pb-no" style="color:{c}">Partea {no}</div><div class="pb-t">{title}</div>'
            f'<div class="pb-w">{what}</div></div>')


BANNER_CSS = """
.part-banner { border-top: 1.2mm solid #1b1d1f; padding: 3mm 0 3.5mm; margin: 0 0 6mm; border-bottom: .3mm solid #d9d5cc; }
.part-banner .pb-no { font: 500 7.6pt 'IBM Plex Mono', monospace; letter-spacing: .08em; text-transform: uppercase; color: #1d5e5a; }
.part-banner .pb-t { font: 600 20pt/1.15 'IBM Plex Sans', sans-serif; color: #1b1d1f; margin: 1.2mm 0 1.6mm; }
.part-banner .pb-w { font: 400 10pt/1.45 'Source Serif 4', serif; color: #464b52; max-width: 150mm; }
.part-banner + h1.sec, .part-banner + section, .part-banner + * { break-before: auto !important; }
.part-banner.compact { border-top-width: .8mm; padding: 1.6mm 0 1.8mm; margin: 0 0 3.5mm; }
.part-banner.compact .pb-t { font-size: 12pt; display: inline; margin: 0 0 0 2mm; }
.part-banner.compact .pb-no { display: inline; }
.part-banner.compact .pb-w { display: none; }
"""


def start():
    return int(os.environ.get("BOOK_START", "1"))


def margins_css(first_page=None):
    n = start() if first_page is None else first_page
    return f"""
@page {{ margin: 24mm 22mm 24mm 22mm; }}
@page :left {{ margin-left: 22mm; margin-right: 22mm; }}
@page :right {{ margin-left: 22mm; margin-right: 22mm; }}
@page :first {{ counter-increment: page {n}; }}
""" + BANNER_CSS


# the Lab margin boxes (lab_styles.py), for builders that do not use BASE_CSS
LAB_BOXES = f"""
@page {{
  @top-left {{ font: 500 7.2pt/1 'IBM Plex Sans', sans-serif; letter-spacing: .06em; text-transform: uppercase; color: {INK3}; vertical-align: bottom; padding-bottom: 5mm; }}
  @top-right {{ font: 400 7.2pt/1 'IBM Plex Sans', sans-serif; letter-spacing: 0; text-transform: none; color: {INK3}; vertical-align: bottom; padding-bottom: 5mm; }}
  @bottom-left {{ font: 400 7.2pt/1 'IBM Plex Sans', sans-serif; color: {INK3}; vertical-align: top; padding-top: 5mm; }}
  @bottom-right {{ content: counter(page); font: 500 8.5pt/1 'IBM Plex Mono', monospace; color: {INK}; vertical-align: top; padding-top: 5mm; }}
}}
"""

# analytic parts: short sections flow on instead of each starting a new page (the profile sheets keep one page each)
FLOW_CSS = """
h1.sec { break-before: auto; margin-top: 9mm; }
h1.sec, h2.sub, .tcap { break-after: avoid; }
"""
