"""Number linter: every data-number in a report must be backed by a claim ID.

Works on Markdown (.md) and on the final HTML (.html). For each block (paragraph, list item,
table cell, figure caption), every numeric token that is not structural must either appear as
a value in claims_registry.csv (PASS/WARN only) or the block must cite a claim [Cxx]. It also
fails if a block cites a FAIL claim, if a citation is empty («[ ]», or an eid span without a claim ID)
or if it cites an ID that is not in the registry. Exits non-zero and lists offenders.

    ..\\venv\\Scripts\\python.exe -X utf8 lint_numbers.py <report.md|report.html>
"""
from __future__ import annotations
import re, sys, csv, html
from pathlib import Path

_HERE = Path(__file__).resolve().parent
DELIV = _HERE if (_HERE / "claims_registry.csv").exists() else _HERE.parent / "analysis" / "raport_executiv_2026-11"
# dataset descriptors (not findings), documented in Anexa C
DESCRIPTORS = {"4077510", "7469", "1819", "2000", "400", "05"}   # 400 = exclusion threshold (days); 0,5 = median definition   # 2000 = simulation draws of the audited engine (method parameter)


def registry():
    vals, status = set(), {}
    with (DELIV / "claims_registry.csv").open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            status[r["id"]] = r["status"]
            if r["status"] == "FAIL":
                continue
            for field in ("value", "unit", "public_ro", "rezerva_obligatorie"):
                for tok in re.findall(r"\d[\d.,]*", r[field]):
                    vals.add(norm(tok))
    # the registry's own size and status counts are descriptors of the registry, quoted in the verification volume
    from collections import Counter as _C
    cnt = _C(status.values()); vals.update({str(len(status))} | {str(v) for v in cnt.values()})
    return vals, status


def norm(tok: str) -> str:
    t = tok.rstrip(".,")
    return t.replace(".", "").replace(",", "")


def blocks_from(path: Path):
    txt = path.read_text(encoding="utf-8")
    if path.suffix.lower() != ".html":
        out = []
        for i, l in enumerate(txt.splitlines(), 1):
            if re.match(r"#+\s*NU afirma", l):   # negative list quotes withdrawn numbers on purpose
                break
            out.append((i, l))
        return out
    txt = re.sub(r"(?is)<head.*?</head>|<svg.*?</svg>|<style.*?</style>|<code>.*?</code>", " ", txt)
    # data tables of volumes 2-6 (class "dt" / "dt small") carry their own source + SHA-256 line; prose is still linted
    txt = re.sub(r'(?is)<table class="dt(?: small| toc1)?">.*?</table>|<div class="tnote">.*?</div>|<div class="formula">.*?</div>|<ol class="refs" data-lint="skip">.*?</ol>|<span class="tpg">[^<]*</span>', " ", txt)
    txt = re.sub(r'<span class="eid">\[(C\d{2,3})\]</span>', r" [\1] ", txt)
    parts = re.split(r"(?i)</(?:p|li|td|dd|dt|h[1-6]|div)>", txt)
    out = []
    for i, p in enumerate(parts, 1):
        t = html.unescape(re.sub(r"<[^>]+>", " ", p))
        t = re.sub(r"\s+", " ", t).strip()
        if t:
            out.append((i, t))
    return out


def main():
    report = Path(sys.argv[1]) if len(sys.argv) > 1 else DELIV / "executiv.md"
    vals, status = registry()
    offenders, failcites, badcites = [], [], []
    raw = report.read_text(encoding="utf-8")
    for m in re.finditer(r'<span class="eid">(.*?)</span>', raw, re.S):    # every citation span must carry exactly one claim ID
        if not re.fullmatch(r"\s*\[C\d{2,3}\]\s*", m.group(1)):
            badcites.append(("html", "eid span " + repr(m.group(1)[:30]), raw[max(0, m.start() - 70):m.start()].replace("\n", " ")))
    for i, line in blocks_from(report):
        for m in re.finditer(r"\[\s*\]|\[\s*,|,\s*\]", line):                 # empty citation brackets
            badcites.append((i, "empty citation " + repr(m.group(0)), line[max(0, m.start() - 70):m.end()]))
        cites = re.findall(r"\[(C\d{2,3})\]", line)
        for c in cites:
            if status.get(c) == "FAIL":
                failcites.append((i, c, line[:80]))
            elif c not in status:
                badcites.append((i, f"unknown claim {c}", line[:80]))
        scan = re.sub(r"\[C\d{2,3}\]|\bC\d{2,3}\b", " ", line)   # claim IDs (cited or in registry tables)
        scan = re.sub(r"\b\d+/\d{4}\b", " ", scan)            # law / directive numbers
        scan = re.sub(r"(?i)\b(?:art|alin)\.\s*\(?\d+\)?", " ", scan)   # article / paragraph numbers
        scan = re.sub(r"\b\d{1,2}\.\d{1,2}(?:\.\d{4})?\b", " ", scan)   # dates dd.mm(.yyyy)
        scan = re.sub(r"[A-Z_]+265\b|SHA-256", " ", scan)               # category codes, hash name
        scan = re.sub(r"\b(?:19|20)\d{2}\b", " ", scan)        # years
        for m in re.finditer(r"\d[\d.,]*", scan):
            tok = m.group(0).rstrip(".,")
            n = norm(tok)
            if len(n) <= 2 and "," not in tok:                 # ordinals, days, small counts
                continue
            if n in vals or n in DESCRIPTORS:
                continue
            if cites:
                continue
            offenders.append((i, tok, line[:90]))
    ok = True
    if badcites:
        ok = False
        print(f"LINT FAIL — {len(badcites)} empty or unknown citation(s):")
        for i, what, ctx in badcites: print(f"  block {i}: {what} — {ctx}")
    if failcites:
        ok = False
        print(f"LINT FAIL — {len(failcites)} citation(s) of withdrawn (FAIL) claims:")
        for i, c, ctx in failcites: print(f"  block {i}: {c} — {ctx}")
    if offenders:
        ok = False
        print(f"LINT FAIL — {len(offenders)} unsourced number(s) in {report.name}:")
        for i, tok, ctx in offenders: print(f"  block {i}: '{tok}' — {ctx}")
    if not ok:
        sys.exit(1)
    print(f"LINT PASS — every data number in {report.name} is backed by a claim ID or a registry value; no FAIL claim is cited; no empty or unknown citation.")


if __name__ == "__main__":
    main()
