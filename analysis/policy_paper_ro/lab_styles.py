"""Sistem de design si componente HTML pentru raportul de politici publice ONRC
(1:1 dupa T:\\Annulment-report: Source Serif 4 + IBM Plex Sans + IBM Plex Mono,
grila 34mm + 6mm + 126mm = 166mm, paleta monocroma + accent unic #1d5e5a).
"""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
FIG_DIR = os.path.join(HERE, "figures_lab")

REPORT_TITLE_UPPER = "CRIZA REGISTRULUI COMERȚULUI (ONRC · 2026–2028)"
FOOTER_NOTICE = "Analiză independentă din date deschise · Ștefan-Lucian Deleanu · stefandeleanu.ro"

PAGE_GROUPS = [
    ("front", "Cuprins"),
    ("guide", "Cum se citește raportul"),
    ("synth", "Sinteză executivă"),
    ("ch-01", "Cap. 1 · Povestea blocajului (2023–2026)"),
    ("ch-02", "Cap. 2 · Intrări, soluționări și stoc"),
    ("ch-03", "Cap. 3 · Legea națională și infringement UE"),
    ("ch-04", "Cap. 4 · Registratori, amânări și portal"),
    ("ch-05", "Cap. 5 · Recensământ și valuri 2026–2028"),
    ("ch-06", "Cap. 6 · Contabilitatea costurilor"),
    ("ch-07", "Cap. 7 · Scenarii și plan de salvare"),
    ("annex-a", "Anexa A · Metodologie și justificări"),
    ("annex-b", "Anexa B · Ipoteze și sensibilitate"),
    ("annex-c", "Anexa C · Limite, județe și reproductibilitate"),
    ("annex-d", "Anexa D · Registrul surselor și legislației"),
    ("annex-e", "Anexa E · Audit, backtesting și muncă-echivalentă"),
]


def build_running_head_css() -> str:
    esc = lambda s: s.replace("\\", "\\\\").replace('"', '\\"')
    lines = [
        f'@page {{ @top-left {{ content: "{esc(REPORT_TITLE_UPPER)}"; }} '
        f'@bottom-left {{ content: "{esc(FOOTER_NOTICE)}"; }} }}'
    ]
    for page_name, head in PAGE_GROUPS:
        extra = " margin: 23mm 17mm 22mm 17mm;" if page_name in ("annex-b", "annex-e") else ""
        lines.append(f'@page {page_name} {{{extra} @top-right {{ content: "{esc(head)}"; }} }}')
    return "\n".join(lines)


BASE_CSS = r"""
:root {
  --ink: #1b1d1f;
  --ink-2: #464b52;
  --ink-3: #6b7178;
  --rule: #bdbab2;
  --rule-2: #e3e0d8;
  --tint: #f1efe9;
  --accent: #1d5e5a;
  --hl: #ffe680;
  --hl-rule: #7a6200;
  --paper: #ffffff;
  --s1: 1mm; --s2: 2mm; --s3: 3mm; --s4: 4mm; --s6: 6mm; --s8: 8mm;
  --mcol: 34mm;
  --gap: 6mm;
  --serif: "Source Serif 4", Georgia, "Times New Roman", serif;
  --sans: "IBM Plex Sans", "Segoe UI", Arial, sans-serif;
  --mono: "IBM Plex Mono", Consolas, monospace;
}

/* ---------- Page setup (A4, running heads in Chromium >= 131) ---------- */
@page {
  size: A4;
  margin: 24mm 20mm 24mm 24mm;
  @top-left {
    font: 500 7.2pt/1 var(--sans);
    letter-spacing: .06em;
    text-transform: uppercase;
    color: var(--ink-3);
    vertical-align: bottom;
    padding-bottom: 5mm;
  }
  @top-right {
    font: 400 7.2pt/1 var(--sans);
    color: var(--ink-3);
    vertical-align: bottom;
    padding-bottom: 5mm;
  }
  @bottom-left {
    font: 400 7.2pt/1 var(--sans);
    color: var(--ink-3);
    vertical-align: top;
    padding-top: 5mm;
  }
  @bottom-right {
    content: counter(page);
    font: 500 8.5pt/1 var(--mono);
    color: var(--ink);
    vertical-align: top;
    padding-top: 5mm;
  }
}
@page :left  { margin-left: 20mm; margin-right: 24mm; }
@page :right { margin-left: 24mm; margin-right: 20mm; }
@page cover  {
  margin: 0;
  @top-left { content: none; }
  @top-right { content: none; }
  @bottom-left { content: none; }
  @bottom-right { content: none; }
}

/* ---------- Base typography ---------- */
* { box-sizing: border-box; }
html {
  font: 400 10.3pt/1.52 var(--serif);
  color: var(--ink);
  background: #fff;
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
}
body {
  margin: 0;
  hyphens: auto;
  font-variant-numeric: oldstyle-nums;
  orphans: 3;
  widows: 3;
}
p { margin: 0 0 .68em; text-align: left; }
a { color: inherit; text-decoration: none; }
h1, h2, h3, h4 {
  font-family: var(--sans);
  color: var(--ink);
  line-height: 1.2;
  margin: 0;
  break-after: avoid;
}
h2 { font-size: 20pt; font-weight: 600; letter-spacing: -.01em; }
h3 { font-size: 11.5pt; font-weight: 600; margin: 1.5em 0 .5em; }
h4 { font-size: 8.8pt; font-weight: 600; letter-spacing: .05em; text-transform: uppercase; color: var(--ink-2); margin: 1.4em 0 .4em; }
.num, .tm, .eid { font-family: var(--mono); font-variant-numeric: lining-nums tabular-nums; }
.eyebrow, .kicker, .alab, .cnum {
  font: 500 7.8pt/1.2 var(--mono);
  letter-spacing: .08em;
  text-transform: uppercase;
  color: var(--ink-3);
  margin: 0 0 3mm;
}
.note { font: 400 8.5pt/1.45 var(--sans); color: var(--ink-2); max-width: 152mm; }
.small-sans { font: 400 8.5pt/1.45 var(--sans); color: var(--ink-2); }

/* ---------- Cover ---------- */
.cover {
  page: cover;
  break-after: page;
  height: 297mm;
  padding: 36mm 26mm 22mm 30mm;
  position: relative;
  border-left: 7mm solid var(--ink);
}
.cover h1 {
  font: 600 35pt/1.06 var(--sans);
  letter-spacing: -.022em;
  margin: 6mm 0 7mm;
  max-width: 138mm;
}
.cover .sub {
  font: 400 13.5pt/1.42 var(--serif);
  max-width: 132mm;
  color: var(--ink-2);
}
.cover .threads { display: flex; gap: 3mm; margin: 13mm 0 9mm; }
.threads i { display: block; width: 28mm; height: 0; border-top: 1mm solid var(--ink); }
.threads .t-s { border-top: .6mm solid var(--ink); margin-top: .2mm; }
.threads .t-m { border-top: .6mm dashed var(--ink); margin-top: .2mm; }
.threads .t-p { border-top: .6mm dotted var(--ink-3); margin-top: .2mm; }
.cover .verdict {
  font: 500 13.5pt/1.4 var(--sans);
  max-width: 130mm;
  border-top: .35mm solid var(--ink);
  padding-top: 4.5mm;
  color: var(--ink);
}
.cover .verdict-sub {
  font: 400 10pt/1.5 var(--serif);
  max-width: 128mm;
  color: var(--ink-2);
  margin-top: 4mm;
}
.cover .meta {
  position: absolute;
  left: 30mm; right: 26mm; bottom: 22mm;
  display: grid;
  grid-template-columns: 30mm 1fr;
  gap: 1.6mm 4mm;
  font: 400 8.5pt/1.42 var(--sans);
  margin: 0;
  border-top: .2mm solid var(--rule);
  padding-top: 4mm;
}
.meta dt {
  font: 500 7.2pt/1.6 var(--mono);
  text-transform: uppercase;
  letter-spacing: .04em;
  color: var(--ink-3);
}
.meta dd { margin: 0; color: var(--ink); }
.meta dd strong { font-weight: 600; }

/* ---------- Front matter ---------- */
.front { break-before: page; }
.front-toc { page: front; }
.front-guide { page: guide; }
.front-synth { page: synth; }
.front > p, .front > ul.key, .front > ol { max-width: 152mm; }
.front .lead { font: 400 13.5pt/1.45 var(--serif); margin: 2mm 0 5.5mm; max-width: 146mm; color: var(--ink); }
.toc { list-style: none; padding: 0; margin: 3mm 0 4mm; font: 400 9.4pt/1.36 var(--sans); }
.toc li {
  display: grid;
  grid-template-columns: 26mm 1fr 10mm;
  gap: 2.5mm;
  padding: 1.25mm 0;
  border-bottom: .2mm solid var(--rule-2);
  align-items: baseline;
}
.toc .toc-part {
  display: block;
  font: 600 7.2pt/1.2 var(--mono);
  letter-spacing: .08em;
  text-transform: uppercase;
  color: var(--ink-3);
  border-bottom: .35mm solid var(--ink);
  padding: 3mm 0 1mm;
  margin-top: 1mm;
}
.toc .tn { font: 500 7.5pt var(--mono); color: var(--ink-3); text-transform: uppercase; }
.toc .tt { color: var(--ink); font-weight: 500; }
.toc .tsub { display: block; font: 400 7.8pt/1.28 var(--serif); color: var(--ink-2); margin-top: .3mm; }
.toc .tpg { font: 500 8.2pt var(--mono); color: var(--ink); text-align: right; font-variant-numeric: lining-nums tabular-nums; }

.key { list-style: none; padding: 0; margin: 1.5mm 0 3.5mm; }
.kitem {
  display: grid;
  grid-template-columns: 28mm 1fr;
  gap: 3.5mm;
  align-items: baseline;
  padding: 1.45mm 0;
  border-bottom: .2mm solid var(--rule-2);
  font: 400 8.9pt/1.38 var(--sans);
}
.front-guide h3 { margin: 1.05em 0 .35em; }
.front-guide .paths { margin: 2.5mm 0 4mm; }
.kitem > .badge { justify-self: start; }

/* ---------- Epistemic / Evidence badges (greyscale-safe) ---------- */
.badge {
  display: inline-block;
  font: 600 7pt/1 var(--mono);
  letter-spacing: .03em;
  padding: .9mm 1.5mm;
  border: .42mm solid var(--ink);
  border-radius: 0;
  color: var(--ink);
  background: #fff;
  white-space: nowrap;
  vertical-align: baseline;
}
.badge.c-E { background: var(--ink); color: #fff; }
.badge.c-S { border-style: solid; }
.badge.c-M { border-style: dashed; }
.badge.c-P {
  border-style: dotted;
  color: var(--ink-2);
  font-style: italic;
  background: repeating-linear-gradient(135deg, #fff 0 1.1mm, #e2e0d8 1.1mm 1.5mm);
}
.badge.inline { font-size: 6.2pt; padding: .55mm 1mm; margin: 0 .4mm; vertical-align: .1em; }
.bn { font: 400 7.4pt/1 var(--sans); margin-left: 1.2mm; color: var(--ink-2); }

/* ---------- Skim patterns (S1-S9) ---------- */
.lab {
  font: 600 6.8pt/1.3 var(--mono);
  letter-spacing: .08em;
  text-transform: uppercase;
  color: var(--ink);
  margin: 0;
}
.p5 {
  display: inline-block;
  font: 600 6.2pt/1 var(--mono);
  letter-spacing: .04em;
  text-transform: uppercase;
  color: var(--ink);
  border: .25mm solid var(--ink);
  border-radius: 3mm;
  padding: .65mm 1.5mm .55mm;
  margin-left: 1mm;
  vertical-align: .2mm;
  white-space: nowrap;
  font-style: normal;
}

/* S1 Takeaway line */
.takeaway {
  display: grid;
  grid-template-columns: var(--mcol) 1fr;
  gap: var(--gap);
  margin: 0 0 4.5mm;
  break-inside: avoid;
  break-after: avoid;
}
.takeaway .lab { padding-top: 1mm; }
.takeaway p {
  font: 600 10.2pt/1.4 var(--sans);
  margin: 0;
  padding: .6mm 0 .6mm 3mm;
  border-left: .9mm solid var(--ink);
  hyphens: manual;
}
.takeaway .p5, .kf .p5 { margin-left: 0; margin-top: 1.2mm; display: inline-block; }

/* S2 Highlighted key sentence */
mark.hl {
  background: var(--hl);
  color: inherit;
  padding: .08em 0;
  text-decoration: underline;
  text-decoration-color: var(--hl-rule);
  text-decoration-thickness: .3mm;
  text-underline-offset: .22em;
  -webkit-box-decoration-break: clone;
  box-decoration-break: clone;
}
.keyflag {
  font: 600 6.3pt/1.25 var(--mono);
  letter-spacing: .08em;
  text-transform: uppercase;
  color: var(--ink);
  border-left: .9mm solid var(--hl-rule);
  padding: .6mm 0 .6mm 1.6mm;
  margin-top: .8mm;
}

/* S3 Key-finding box */
.kf {
  display: grid;
  grid-template-columns: var(--mcol) 1fr;
  gap: var(--gap);
  margin: 5mm 0 5.5mm;
  break-inside: avoid;
}
.kf .lab { padding-top: 2.5mm; }
.kfb {
  border-top: .7mm solid var(--ink);
  border-bottom: .2mm solid var(--ink);
  padding: 2.6mm 0 2.2mm;
}
.kfb p { font: 500 10.6pt/1.42 var(--sans); margin: 0 0 2mm; hyphens: manual; }
.kfb .kfc { font: 400 7.4pt/1.35 var(--sans); color: var(--ink-2); margin: 0; }
.kfc .badge { margin-right: 1.5mm; }

/* S4 In-brief opener */
.inbrief {
  display: grid;
  grid-template-columns: 1fr 56mm;
  gap: 0;
  margin: 0 0 6mm;
  border: .2mm solid var(--ink);
  border-top-width: .7mm;
  break-inside: avoid;
}
.ibm { padding: 3.2mm 4mm; }
.ibs { padding: 3.2mm 4mm; border-left: .2mm solid var(--ink); background: var(--tint); }
.inbrief ul { margin: 2mm 0 0; padding-left: 4.2mm; font: 400 9.4pt/1.44 var(--sans); }
.inbrief li { margin-bottom: 1.3mm; }
.ibn { font: 400 8.6pt/1.3 var(--sans); margin: 2mm 0 2mm; color: var(--ink); }
.ibn .num { font: 600 17pt/1.05 var(--sans); display: block; margin-bottom: .6mm; color: var(--ink); }
.ibc { margin: 2mm 0 2mm; font: 500 7.8pt var(--mono); }
.ibd { font: 400 7.4pt/1.42 var(--sans); color: var(--ink-2); margin: 1.5mm 0 0; }

/* S5 Lead-in & S6 Margin note */
.prose {
  display: grid;
  grid-template-columns: var(--mcol) 1fr;
  gap: var(--gap);
  margin: 0 0 .68em;
}
.prose.keep-together { break-inside: avoid; padding-top: .5mm; }
.prose.keep-together .bcol { break-inside: avoid; }
.prose p { margin: 0; }
.prose .mcol { min-width: 0; }
.prose .bcol { min-width: 0; }
.leadin { font: 600 9.6pt var(--sans); color: var(--ink); }
.mnote {
  font: 400 7.3pt/1.42 var(--sans);
  color: var(--ink-2);
  border-top: .2mm solid var(--ink-3);
  padding-top: 1.1mm;
  margin-top: .8mm;
  hyphens: manual;
  break-inside: avoid;
}
.mnote b {
  display: block;
  font: 600 6.3pt/1.3 var(--mono);
  letter-spacing: .08em;
  text-transform: uppercase;
  color: var(--ink);
  margin-bottom: .6mm;
}

/* S7 Assessment strip */
.strip3 {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 5mm;
  margin: 5.5mm 0 6mm;
  break-inside: avoid;
}
.s3 { padding-top: 2.5mm; font: 400 8.3pt/1.42 var(--sans); background-repeat: no-repeat; background-position: 0 0; }
.s3-est { background-image: linear-gradient(var(--ink), var(--ink)); background-size: 100% 1mm; }
.s3-mod { background-image: linear-gradient(var(--ink), var(--ink)); background-size: 100% .3mm; }
.s3-opn { background-image: linear-gradient(90deg, var(--ink) 0 42%, transparent 42% 58%, var(--ink) 58% 100%); background-size: 100% .3mm; }
.s3h { font: 600 8.8pt/1.2 var(--sans); margin: 0 0 .8mm; }
.s3d { font: 400 7.3pt/1.35 var(--sans); color: var(--ink-2); margin: 0 0 1.8mm; min-height: 11mm; }
.s3 ul { margin: 0; padding-left: 3.8mm; }
.s3 li { margin-bottom: 1.2mm; }

/* S8 Pull figures */
.pulls {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 4.5mm;
  margin: 5mm 0 6mm;
  break-inside: avoid;
}
.pulls.cols-3 { grid-template-columns: repeat(3, 1fr); }
.pull { border-top: .35mm solid var(--ink); padding-top: 2mm; }
.pn {
  font: 600 19.5pt/1.05 var(--sans);
  font-variant-numeric: lining-nums tabular-nums;
  letter-spacing: -.015em;
  margin: 0 0 1.4mm;
  white-space: nowrap;
  color: var(--ink);
}
.pn.accent { color: var(--accent); }
.pl { font: 500 8.2pt/1.32 var(--sans); margin: 0 0 1.2mm; color: var(--ink); }
.ps { font: 400 6.9pt/1.35 var(--sans); color: var(--ink-3); margin: 0; }

/* Reading paths */
.paths { display: grid; grid-template-columns: 1fr 1fr; gap: 6mm; margin: 3mm 0 6mm; }
.path { border-top: .7mm solid var(--ink); padding-top: 2.2mm; font: 400 9pt/1.48 var(--sans); }
.path + .path { border-top-width: .25mm; }
.path p { margin: 1.5mm 0 0; }

/* ---------- Chapters ---------- */
.chapter { break-before: page; overflow-wrap: anywhere; }
.copen {
  padding: 5mm 0 5mm;
  margin-bottom: 5.5mm;
  border-bottom: .35mm solid var(--ink);
  break-after: avoid;
}
.copen h2 { font-size: 27pt; line-height: 1.1; margin: 2mm 0 3mm; letter-spacing: -.018em; }
.cdek { font: 500 11.4pt/1.44 var(--serif); max-width: 138mm; margin: 0; color: var(--ink); }
.cmeta { font: 400 7.8pt/1.4 var(--mono); color: var(--ink-3); margin: 2.5mm 0 0; }
.sec-head { break-inside: avoid; break-after: avoid; }
.sec-head h3 { margin-left: calc(var(--mcol) + var(--gap)); margin-top: 1.35em; margin-bottom: .45em; break-inside: avoid; break-after: avoid; }
.cols > h3 { margin-left: calc(var(--mcol) + var(--gap)); margin-top: 1.35em; margin-bottom: .45em; break-inside: avoid; break-after: avoid; }
.cols > h4 { margin-left: calc(var(--mcol) + var(--gap)); }
.cols > ul.body-list, .cols > ol.body-list {
  margin: 0 0 .75em calc(var(--mcol) + var(--gap));
  padding-left: 4.8mm;
}
.cols > ul.body-list li, .cols > ol.body-list li { margin-bottom: .38em; }

/* Quotation boxes */
.qpair {
  margin: 3.5mm 0 5mm calc(var(--mcol) + var(--gap));
  padding: 3mm 3.6mm;
  background: var(--tint);
  border-left: .6mm solid var(--ink);
  break-inside: avoid;
}
.qpair .ql {
  font: 600 6.5pt/1.2 var(--mono);
  letter-spacing: .07em;
  text-transform: uppercase;
  color: var(--ink-3);
  margin-bottom: 1.4mm;
}
.qpair blockquote {
  margin: 0;
  font: italic 400 9.4pt/1.46 var(--serif);
  color: var(--ink);
  hyphens: manual;
}
.qpair blockquote p { margin: 0 0 .45em; }
.qpair blockquote p:last-child { margin-bottom: 0; }
.qpair .qsrc {
  margin: 2mm 0 0;
  font: 400 7.4pt/1.35 var(--sans);
  color: var(--ink-3);
}

/* Open question & Counter-case */
.oq {
  display: grid;
  grid-template-columns: var(--mcol) 1fr;
  gap: var(--gap);
  margin: 4.5mm 0 5mm;
  break-inside: avoid;
}
.oq .lab { padding-top: 1mm; border-left: none; padding-left: 0; }
.oq > div:last-child {
  border-left: .3mm dashed var(--ink-2);
  padding-left: 3.2mm;
  font: 400 9.2pt/1.48 var(--sans);
  color: var(--ink);
}
.oq.cc > div:last-child {
  border-left: .9mm solid var(--ink);
  font: 400 9.8pt/1.5 var(--serif);
}
.oq p { margin: 0 0 1.8mm; }
.oq p:last-child { margin-bottom: 0; }

/* ---------- Figures (Full 166mm measure) ---------- */
figure.chart {
  margin: 5.5mm 0 6mm;
  border-top: .5mm solid var(--ink);
  padding-top: 2.2mm;
  break-inside: avoid;
}
.fnum {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font: 500 7.3pt/1.2 var(--mono);
  letter-spacing: .06em;
  text-transform: uppercase;
  color: var(--ink-3);
  margin: 0 0 1.2mm;
}
.ftitle {
  font: 600 10.8pt/1.3 var(--sans);
  color: var(--ink);
  margin: 0 0 2mm;
  max-width: 158mm;
  hyphens: manual;
}
figure .fig { width: 100%; height: auto; display: block; margin: 1.5mm 0 1.5mm; }
.falt, .fsrc {
  font: 400 7.5pt/1.45 var(--sans);
  color: var(--ink-2);
  margin: 1.3mm 0 0;
  hyphens: manual;
}
.falt b, .fsrc b { font-weight: 600; color: var(--ink); }
.fsrc { color: var(--ink-3); }

/* ---------- Tables (Academic / Book style) ---------- */
.tbl-wrap {
  margin: 4.5mm 0 5.5mm;
  break-inside: avoid;
}
.tbl-wrap.allow-break { break-inside: auto; }
.tbl-head {
  font: 600 8.8pt/1.3 var(--sans);
  color: var(--ink);
  margin: 0 0 1.5mm;
  break-after: avoid;
}
.tbl-head .tnum {
  font: 500 7.3pt var(--mono);
  letter-spacing: .06em;
  text-transform: uppercase;
  color: var(--ink-3);
  margin-right: 2mm;
}
table {
  border-collapse: collapse;
  width: 100%;
  font: 400 7.9pt/1.38 var(--sans);
  font-variant-numeric: lining-nums tabular-nums;
}
th, td {
  text-align: left;
  vertical-align: top;
  padding: 1.5mm 1.8mm;
  border-bottom: .2mm solid var(--rule);
}
thead { display: table-header-group; }
thead th {
  font: 600 6.6pt/1.25 var(--sans);
  text-transform: uppercase;
  letter-spacing: .04em;
  border-top: .5mm solid var(--ink);
  border-bottom: .45mm solid var(--ink);
  color: var(--ink-2);
  background: #fff;
  hyphens: none;
}
tbody tr { break-inside: avoid; }
tbody tr.em-row td, tbody tr.em-row th { background: var(--tint); font-weight: 600; }
tbody tr.total-row td { border-top: .45mm solid var(--ink); border-bottom: .6mm solid var(--ink); font-weight: 600; background: var(--tint); }
td.r, th.r { text-align: right; }
td.m { font-family: var(--mono); font-size: 7.2pt; hyphens: none; }
td.nw, th.nw { white-space: nowrap; }
.tcap {
  margin: 1.6mm 0 0;
  font: 400 7.3pt/1.4 var(--sans);
  color: var(--ink-3);
}

/* ---------- Annexes ---------- */
.annex { break-before: page; }
.annex-b table { font-size: 7.45pt; line-height: 1.32; }
.annex-b th, .annex-b td { padding: 1.1mm 1.5mm; }
.annex-b .aopen { margin-bottom: 3.5mm; padding-bottom: 2.5mm; }
.annex-d .aopen { margin-bottom: 3.5mm; padding-bottom: 2.5mm; }
.aopen {
  margin-bottom: 5mm;
  padding-bottom: 3.5mm;
  border-bottom: .35mm solid var(--ink);
  break-after: avoid;
}
.aopen h2 { font-size: 20pt; margin: 1.5mm 0 2mm; }
.aopen .adek { font: 400 10.5pt/1.44 var(--serif); color: var(--ink-2); max-width: 148mm; margin: 0; }
.method-block {
  margin: 0 0 4.5mm;
  padding-top: 2.5mm;
  border-top: .2mm solid var(--rule);
  break-inside: avoid;
}
.method-block h3 { margin: 0 0 1.5mm; font-size: 10.4pt; }
.method-grid {
  display: grid;
  grid-template-columns: 32mm 1fr;
  gap: 1.2mm 4mm;
  font: 400 8.5pt/1.45 var(--sans);
  margin-top: 1.5mm;
}
.method-grid dt {
  font: 600 6.8pt/1.55 var(--mono);
  text-transform: uppercase;
  letter-spacing: .05em;
  color: var(--ink-3);
}
.method-grid dd { margin: 0; color: var(--ink); }
.eq {
  font: 400 8.2pt/1.4 var(--mono);
  background: var(--tint);
  padding: 1.6mm 2.5mm;
  margin: 1.5mm 0;
  border-left: .45mm solid var(--ink-3);
  color: var(--ink);
}

/* Source register (Annex D) */
.register { list-style: none; padding: 0; margin: 0; font: 400 7.65pt/1.36 var(--sans); }
.register li {
  display: grid;
  grid-template-columns: 9.5mm 1fr;
  gap: 1.8mm;
  padding: 1.05mm 0;
  border-bottom: .2mm solid var(--rule-2);
  break-inside: avoid;
}
.register .rn { font: 500 7.6pt var(--mono); color: var(--ink-2); }
.register .tier {
  font: 500 6.8pt var(--mono);
  color: var(--ink-3);
  margin-left: 1.8mm;
  white-space: nowrap;
}

/* Action roadmap table */
.stage-tag {
  font: 600 6.8pt/1.2 var(--mono);
  text-transform: uppercase;
  letter-spacing: .04em;
  color: var(--accent);
  display: block;
  margin-bottom: .6mm;
}
"""


def badge(code: str, label: str = "", inline: bool = False) -> str:
    cls = f"badge c-{code}" + (" inline" if inline else "")
    extra = f'<span class="bn">{label}</span>' if label else ""
    return f'<span class="{cls}">{code}</span>{extra}'


def hl(text: str) -> str:
    return f'<mark class="hl">{text}</mark>'


def takeaway(text: str) -> str:
    return (
        '<div class="takeaway">'
        '<div class="lab">Ideea principală<br><span class="p5">5 min</span></div>'
        f'<p>{text}</p>'
        '</div>'
    )


def sec_head(title: str, takeaway_text: str) -> str:
    return f'<div class="sec-head"><h3>{title}</h3>{takeaway(takeaway_text)}</div>'


def prose(body_html: str, margin_title: str = "", margin_html: str = "", key_flag: bool = False) -> str:
    m_parts = []
    if key_flag:
        m_parts.append('<div class="keyflag">Propoziție-cheie</div>')
    if margin_html:
        m_parts.append(f'<div class="mnote"><b>{margin_title}</b>{margin_html}</div>')
    mcol = "".join(m_parts)
    keep = " keep-together" if (margin_html or key_flag) else ""
    return f'<div class="prose{keep}"><div class="mcol">{mcol}</div><div class="bcol"><p>{body_html}</p></div></div>'


def key_finding(num: str, text: str, code: str, code_label: str, basis: str) -> str:
    return (
        '<div class="kf">'
        f'<div class="lab">Constatare cheie {num}<br><span class="p5">5 min</span></div>'
        '<div class="kfb">'
        f'<p>{text}</p>'
        f'<p class="kfc">{badge(code, code_label)} · {basis}</p>'
        '</div>'
        '</div>'
    )


def in_brief(bullets: list, stat_num: str, stat_label: str, badge_line: str, detail: str) -> str:
    li_html = "".join(f"<li>{b}</li>" for b in bullets)
    return (
        '<div class="inbrief">'
        '<div class="ibm">'
        '<div class="lab">Pe scurt <span class="p5">5 min</span></div>'
        f'<ul>{li_html}</ul>'
        '</div>'
        '<div class="ibs">'
        '<div class="lab">Datele capitolului</div>'
        f'<div class="ibn"><span class="num">{stat_num}</span>{stat_label}</div>'
        f'<div class="ibc">{badge_line}</div>'
        f'<p class="ibd">{detail}</p>'
        '</div>'
        '</div>'
    )


def pulls(items: list, cols: int = 4) -> str:
    cls = "pulls" if cols == 4 else f"pulls cols-{cols}"
    cards = []
    for num, label, src, accent in items:
        pcls = "pn accent" if accent else "pn"
        cards.append(
            f'<div class="pull"><div class="{pcls}">{num}</div>'
            f'<div class="pl">{label}</div><div class="ps">{src}</div></div>'
        )
    return f'<div class="{cls}">{"".join(cards)}</div>'


def quote_box(label: str, paragraphs: list, src: str) -> str:
    ps = "".join(f"<p>{p}</p>" for p in paragraphs)
    return (
        '<div class="qpair">'
        f'<div class="ql">{label}</div>'
        f'<blockquote>{ps}</blockquote>'
        f'<div class="qsrc">{src}</div>'
        '</div>'
    )


def counter_case(paragraphs: list) -> str:
    ps = "".join(f"<p>{p}</p>" for p in paragraphs)
    return (
        '<div class="oq cc">'
        '<div class="lab">Argumentul contrar</div>'
        f'<div>{ps}</div>'
        '</div>'
    )


def open_question(text: str) -> str:
    return (
        '<div class="oq">'
        '<div class="lab">Întrebare deschisă</div>'
        f'<div><p>{text}</p></div>'
        '</div>'
    )


def load_inline_svg(filename: str, prefix: str) -> str:
    path = os.path.join(FIG_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        svg = f.read()
    # Namespace all internal SVG IDs so multiple inline SVGs never collide
    ids = set(re.findall(r'\bid="([^"]+)"', svg))
    for old_id in sorted(ids, key=len, reverse=True):
        new_id = f"{prefix}_{old_id}"
        svg = svg.replace(f'id="{old_id}"', f'id="{new_id}"')
        svg = svg.replace(f'url(#{old_id})', f'url(#{new_id})')
        svg = svg.replace(f'href="#{old_id}"', f'href="#{new_id}"')
    return svg


def figure_svg(fnum: str, tag: str, title: str, svg_file: str, prefix: str,
               in_words: str, note: str, source: str) -> str:
    svg_code = load_inline_svg(svg_file, prefix)
    return (
        '<figure class="chart">'
        f'<div class="fnum"><span>{fnum}</span><span>{tag}</span></div>'
        f'<div class="ftitle">{title}</div>'
        f'{svg_code}'
        f'<p class="falt"><b>În cuvinte.</b> {in_words}</p>'
        f'<p class="falt"><b>Notă.</b> {note}</p>'
        f'<p class="fsrc"><b>Sursă.</b> {source}</p>'
        '</figure>'
    )
