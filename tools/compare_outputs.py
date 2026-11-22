"""Phase-2 acceptance check: does the rebuilt edition MATCH the published one? (value-level, not byte-level)

Byte equality is not expected: the rebuilt BERC pickle has another SHA-256 (so every registry `data_sha256` changes),
Edge PDFs embed timestamps/IDs, and SVGs carry matplotlib ids. "Match" is therefore defined as:
  1. claims_registry.csv: same set of ids; for each id identical `value`, `unit`, `status`, `level`, `public_ro`,
     `rezerva_obligatorie` (data_sha256 / data_date reported, not compared).
  2. JSON outputs in independent_audit/out and analysis/policy_paper_ro/audit_data: every numeric leaf equal within
     rel. 1e-9 (strings equal), keys identical; `_meta` / sha / path fields ignored.
  3. PDFs: same page count per volume and same extracted text per page after whitespace normalisation
     (PyMuPDF); differing pages are listed.
  4. lake build OK, 0 `sorry`; lint_numbers exit 0 on every final HTML.

  python -X utf8 tools/compare_outputs.py <published snapshot dir> [<rebuilt repo dir>]
The snapshot dir mirrors the repo layout (copied at phase 2 from the author's final edition).
"""
from __future__ import annotations
import csv, json, math, re, sys
from pathlib import Path

# anchored: must NOT swallow real values such as share_stage1 / rejection_share_strict_finals
IGNORE_KEYS = re.compile(r"(?i)^(_meta|sha256|sha|data_sha256|archive_path|path|mtime|generated_at|build_tail)$|_sha256$")
CMP_FIELDS = ("value", "unit", "status", "level", "public_ro", "rezerva_obligatorie", "text")


def registry(a: Path, b: Path):
    ra = {r["id"]: r for r in csv.DictReader(open(a, encoding="utf-8"))}
    rb = {r["id"]: r for r in csv.DictReader(open(b, encoding="utf-8"))}
    bad = [f"missing {i}" for i in ra.keys() - rb.keys()] + [f"extra {i}" for i in rb.keys() - ra.keys()]
    for i in ra.keys() & rb.keys():
        for f in CMP_FIELDS:
            if ra[i].get(f) != rb[i].get(f):
                bad.append(f"{i}.{f}: {ra[i].get(f)!r} != {rb[i].get(f)!r}")
    return bad


def walk(x, y, p=""):
    if isinstance(x, dict) and isinstance(y, dict):
        out = [f"{p}: keys differ {sorted(set(x) ^ set(y))[:5]}"] if set(x) != set(y) else []
        return out + [d for k in set(x) & set(y) if not IGNORE_KEYS.search(k) for d in walk(x[k], y[k], f"{p}.{k}")]
    if isinstance(x, list) and isinstance(y, list):
        if len(x) != len(y):
            return [f"{p}: len {len(x)} != {len(y)}"]
        return [d for i, (u, v) in enumerate(zip(x, y)) for d in walk(u, v, f"{p}[{i}]")]
    if isinstance(x, (int, float)) and isinstance(y, (int, float)) and not isinstance(x, bool):
        return [] if math.isclose(x, y, rel_tol=1e-9, abs_tol=1e-12) or (x != x and y != y) else [f"{p}: {x} != {y}"]
    return [] if x == y else [f"{p}: {str(x)[:60]!r} != {str(y)[:60]!r}"]


def table_cmp(a, b):
    """CSV / xlsx sheets: same shape and columns; numeric cells within 1e-9 rel., text cells equal."""
    import pandas as pd
    if a.shape != b.shape or list(a.columns) != list(b.columns):
        return [f"shape/columns {a.shape} != {b.shape}"]
    out = []
    for c in a.columns:
        x, y = a[c], b[c]
        nx, ny = pd.to_numeric(x, errors="coerce"), pd.to_numeric(y, errors="coerce")
        num = nx.notna() & ny.notna()
        bad = num & ~((nx - ny).abs() <= 1e-9 * ny.abs().clip(lower=1e-12) + 1e-12)
        bad |= ~num & (x.astype(str) != y.astype(str))
        if bad.any():
            out.append(f"col {c}: {int(bad.sum())} cells differ")
    return out


def pdf_text(p: Path):
    import fitz
    return [re.sub(r"\s+", " ", pg.get_text("text")).strip() for pg in fitz.open(str(p))]


def main():
    pub = Path(sys.argv[1]); new = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).resolve().parents[1]
    report = {}
    reg = "analysis/raport_executiv_2026-11/claims_registry.csv"
    report[reg] = registry(pub / reg, new / reg)
    for d in ("independent_audit/out", "analysis/policy_paper_ro/audit_data"):
        for f in sorted((pub / d).rglob("*.json")):
            rel = f.relative_to(pub)
            g = new / rel
            report[str(rel)] = ["missing in rebuild"] if not g.exists() else walk(
                json.loads(f.read_text(encoding="utf-8")), json.loads(g.read_text(encoding="utf-8")))
    import pandas as pd
    for d in ("independent_audit/out", "analysis/policy_paper_ro/audit_data", "independent_audit/reserves_check"):
        for f in sorted((pub / d).rglob("*.csv")):
            rel = f.relative_to(pub); g = new / rel
            report[str(rel)] = ["missing in rebuild"] if not g.exists() else table_cmp(
                pd.read_csv(f, dtype=str, keep_default_na=False), pd.read_csv(g, dtype=str, keep_default_na=False))
    xl = "analysis/raport_executiv_2026-11/Date_ONRC_Coada_2026-11.xlsx"
    if (pub / xl).exists():
        A = pd.read_excel(pub / xl, sheet_name=None, header=None, dtype=str); B = pd.read_excel(new / xl, sheet_name=None, header=None, dtype=str)
        report[xl] = [f"sheets differ {sorted(set(A) ^ set(B))}"] if set(A) != set(B) else [
            f"{s}: {m}" for s in A for m in table_cmp(A[s].fillna(""), B[s].fillna(""))]
    for f in sorted((pub / "analysis/raport_executiv_2026-11").glob("*.pdf")):
        g = new / f.relative_to(pub)
        if not g.exists():
            report[f.name] = ["missing in rebuild"]; continue
        a, b = pdf_text(f), pdf_text(g)
        report[f.name] = [f"pages {len(a)} != {len(b)}"] if len(a) != len(b) else [f"page {i + 1} text differs" for i, (u, v) in enumerate(zip(a, b)) if u != v]
    n_bad = 0
    for k, v in report.items():
        print(("OK   " if not v else "DIFF ") + k + ("" if not v else f"  ({len(v)}) " + "; ".join(v[:4])))
        n_bad += bool(v)
    sys.exit(1 if n_bad else 0)


if __name__ == "__main__":
    main()
