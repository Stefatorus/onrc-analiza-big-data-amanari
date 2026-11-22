"""Phase-1: expand manifest_candidates.txt, record size/SHA-256/mtime, and run a privacy & secrets scan.
Read-only on the source tree. Values found are MASKED in the report (only category, file, line, a redacted hint).

  python -X utf8 manifest_scan.py <SOLOResearch root> <manifest_candidates.txt> <out_dir>
"""
import sys, re, json, hashlib, glob, os, csv
from pathlib import Path
ROOT, MAN, OUTD = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
rows = []
for line in MAN.read_text(encoding="utf-8").splitlines():
    if not line.strip() or line.startswith("#"): continue
    cat, pat = [x.strip() for x in line.split("|")[:2]]
    hits = sorted(glob.glob(str(ROOT / pat))) if "*" in pat else [str(ROOT / pat)]
    for h in hits:
        p = Path(h)
        if not p.exists(): rows.append(dict(cat=cat, path=pat, missing=True)); continue
        if p.is_dir() or "__pycache__" in p.parts: continue
        b = p.read_bytes()
        rows.append(dict(cat=cat, path=str(p.relative_to(ROOT)).replace("\\", "/"), bytes=len(b),
                         sha256=hashlib.sha256(b).hexdigest(), mtime=round(p.stat().st_mtime)))
AUTHOR = re.compile(r"(?i)(Ștefan|Stefan)[- ]Lucian Deleanu|Deleanu|stefandeleanu\.ro")
PAT = {
  "secret_kw":  re.compile(r"(?i)\b(bearer\s+[A-Za-z0-9._\-]{12,}|api[_-]?key\s*[:=]|secret\s*[:=]|passw(or)?d\s*[:=]|client_secret|x-api-key)"),
  "jwt":        re.compile(r"eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}"),
  "token_lit":  re.compile(r"(?i)token['\"]?\s*[:=]\s*['\"][A-Za-z0-9._\-]{16,}['\"]"),
  "cookie":     re.compile(r"(?i)\b(set-)?cookie\b|JSESSIONID|XSRF|csrf"),
  "auth_hdr":   re.compile(r"(?i)authorization['\"]?\s*:"),
  "email":      re.compile(r"[\w.+\-]+@[\w\-]+\.[A-Za-z]{2,}"),
  "phone_ro":   re.compile(r"(?<![\d.,])(\+40|0040|0)\s?(7\d{2}|2\d{2}|3\d{2})[\s.\-]?\d{3}[\s.\-]?\d{3}(?![\d.,])"),
  "cnp_like":   re.compile(r"(?<!\d)[1-8]\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{6}(?!\d)"),
  "cui_ro":     re.compile(r"(?i)\bRO\d{6,10}\b|\bcui['\"]?\s*[:=]\s*['\"]?\d{4,10}"),
  "j_number":   re.compile(r"\bJ\d{2}/\d{1,7}/\d{4}\b|\bJ20\d{11}\b|ROONRC\.J\d+"),
  "uuid":       re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", re.I),
  "company":    re.compile(r"\b[A-ZĂÂÎȘȚ][A-ZĂÂÎȘȚ0-9&\-\. ]{2,40}\s(S\.?R\.?L\.?|S\.?A\.?|P\.?F\.?A\.?|SNC|SCS)\b"),
  "user_path":  re.compile(r"(?i)C:[/\x5c]+Users[/\x5c]+|[/\x5c]stefa\b|AppData|(?<![A-Za-z])[TUWS]:[/\x5c]|venv[/\x5c]Scripts"),
  "confidential": re.compile(r"(?i)confiden[tț]ial|nu se trimite|internal only"),
}
NAME = re.compile(r"\b([A-ZĂÂÎȘȚ][a-zăâîșț]{2,}(?:-[A-ZĂÂÎȘȚ][a-zăâîșț]+)?)\s+([A-ZĂÂÎȘȚ][a-zăâîșț]{2,}|[A-ZĂÂÎȘȚ]{3,})\b")
# BERC writes firm and sole-trader names in capitals ("POPESCU ION PFA"): catch runs of 2+ all-caps words too.
CAPS = re.compile(r"\b[A-ZĂÂÎȘȚŞŢ]{3,}(?:\s+[A-ZĂÂÎȘȚŞŢ]{3,})+\b")
CAPS_STOP = set("""ONRC BERC ORCT OUG CAEN MJ PFA SRL SNC IMM ANAF BNR TVA FTE CSV JSON PDF SVG HTML XLSX UTF API URL HTTP GET POST
PASS WARN FAIL TODO NOTE AND THE FOR NOT NULL NAN TRUE FALSE NONE ALL REG LOCKED CERERE INMATRIC AUTO AMANARI CERERE_HJ RAPORT
COADA REGISTRUL COMERȚULUI COMERTULUI SINTEZĂ EXECUTIVĂ PENTRU DECIDENȚI CAPITOLUL ANEXA ANEXĂ PARTEA RAPORT COMPLET VOLUMUL FIFO DID
LEAN SORRY CUI EUID SIRUTA DMS CSRF NOTA ROMÂNIA ROMANIA BUCUREȘTI FINALE TOTAL MEDIANA ZILE NOV OCT SEP AUG IUL IUN MAI APR MAR FEB IAN
STAGE OPERARE SOLUTIONARE ADMIS RESPINS AMÂNAT RENUNȚAT HJ WEB UU AN INS SBS EUR RON LEI MIL ROONRC CEPEJ ECDF KM SE CI MAPE OLS IV""".split())


def mask(s): return s[:3] + "…" + f"({len(s)} ch)"
findings, names = [], {}
for r in rows:
    if r.get("missing"): continue
    p = ROOT / r["path"]
    if p.suffix.lower() in (".woff2", ".woff", ".ttf", ".otf", ".pdf", ".png", ".pkl"): continue
    for i, line in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        for k, rx in PAT.items():
            for m in rx.finditer(line):
                v = m.group(0)
                if k == "email" and AUTHOR.search(v): continue
                findings.append(dict(file=r["path"], line=i, kind=k, hint=mask(v) if k in ("secret_kw","jwt","token_lit","email","phone_ro","cnp_like","cui_ro","j_number","uuid") else v[:60]))
        if True:   # every text file, code included: report prose lives in the .py builders and the registry generator
            for rx in (NAME, CAPS):
                for m in rx.finditer(line):
                    n = m.group(0)
                    if AUTHOR.search(n) or (rx is CAPS and all(w in CAPS_STOP for w in n.split())): continue
                    names.setdefault(n, []).append(f"{r['path']}:{i}")
OUTD.mkdir(parents=True, exist_ok=True)
(OUTD / "manifest_phase1.json").write_text(json.dumps(rows, indent=1), encoding="utf-8")
with open(OUTD / "privacy_findings.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["file", "line", "kind", "hint"]); w.writeheader(); w.writerows(findings)
(OUTD / "name_candidates.json").write_text(json.dumps({k: v[:5] + ([f"+{len(v)-5}"] if len(v) > 5 else []) for k, v in sorted(names.items())}, ensure_ascii=False, indent=1), encoding="utf-8")
from collections import Counter
print("files", sum(1 for r in rows if not r.get("missing")), "missing", [r["path"] for r in rows if r.get("missing")],
      "MB", round(sum(r.get("bytes", 0) for r in rows) / 1e6, 2))
print(Counter((x["kind"]) for x in findings))
print("name candidates:", len(names))
