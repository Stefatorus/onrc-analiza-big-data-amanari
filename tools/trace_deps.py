"""Phase-1 static dependency tracer (AST + grep only; never imports or runs the sources).

Usage:  python -X utf8 trace_deps.py <SOLOResearch root> <out.json>
Separates: imported modules (closure), scripts run via subprocess, files read as text/data,
and, for every referenced data file name, the scripts anywhere in the tree that WRITE it.
"""
import ast, sys, re, json, hashlib, os
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve()
IA, PP = ROOT / "independent_audit", ROOT / "analysis" / "policy_paper_ro"
ENTRY = [PP / f for f in ("build_all_volumes.py", "build_raport_complet.py", "generate_institutii_figures.py",
                         "generate_prognoza_figures.py", "generate_stat_figures.py", "generate_impact_figures.py",
                         "audit_forecast.py", "audit_costs.py", "audit_finance.py")]
ENTRY += [IA / f for f in ("reconcile_sources.py", "stat_pack.py", "stat_pack_ext.py", "county_rankings.py",
                           "osint_crosscheck.py", "serials_consolidate.py", "forecast_grid.py", "forecast_caen_compliance.py",
                           "backtest_queue_mechanics.py", "cost_check.py", "cost_founded.py", "cost_monthly.py",
                           "generate_claims_registry.py", "gen_lean_v3_witnesses.py", "lint_numbers.py", "generate_reel_package.py")]
ENTRY += sorted((IA / "cost_evidence").glob("[0-9]*.py")) + sorted((IA / "reserves_check").glob("[0-9]*.py"))
ENTRY += sorted((IA / "econometrics").glob("*.py"))
ENTRY += [ROOT / "analysis" / "raport_executiv_2026-11" / "lint_numbers.py", ROOT / "analysis" / "build_decisions.py",
          ROOT / "extractBulletinsText.py"]
# phase 2 additions
ENTRY += [PP / f for f in ("postponement_section.py", "rejection_section.py", "add_pdf_links.py", "generate_postponement_figures.py")]
ENTRY += [IA / f for f in ("oug_scenarios.py", "validation_checklist.py")]
for sub in ("delay_reasons", "rejection_reasons", "stakeholders"):
    ENTRY += sorted((IA / sub).glob("*.py"))
ENTRY += sorted((ROOT / "replicare_independenta" / "lucru").glob("*.py"))
DATA_EXT = r"json|jsonl|csv|pkl|svg|png|md|html|pdf|xlsx|lean|ttf|woff2?|css|txt|parquet|otf|log"
FN = re.compile(rf"([A-Za-z0-9_\-\.\*]+\.(?:{DATA_EXT}))\b")
WRITE = re.compile(r"write_text|write_bytes|to_csv|to_excel|json\.dump|savefig|open\([^)]*['\"][wa]b?['\"]|\.save\(|ExcelWriter|to_pickle|pickle\.dump")
STD = set(sys.stdlib_module_names)

def resolve(mod, base):
    top = mod.split(".")[0]
    for d in (base, base.parent, IA, PP, IA / "reserves_check"):
        for p in (d / f"{top}.py", d / top / "__init__.py"):
            if p.exists(): return p.resolve()
    return None

imported, ran, ext = {}, {}, set()
todo = [(p.resolve(), "entry") for p in ENTRY if p.exists()]
while todo:
    f, why = todo.pop()
    if f in imported: continue
    tree = ast.parse(f.read_text(encoding="utf-8"))
    loc = []
    for n in ast.walk(tree):
        mods = [a.name for a in n.names] if isinstance(n, ast.Import) else ([n.module] if isinstance(n, ast.ImportFrom) and n.module and not n.level else [])
        for m in mods:
            p = resolve(m, f.parent)
            if p: loc.append(str(p)); todo.append((p, f"import by {f.name}"))
            elif m.split(".")[0] not in STD: ext.add(m.split(".")[0])
        # subprocess-run scripts: list literals containing a *.py string, inside a subprocess.* call or a 'steps' list
        if isinstance(n, ast.List):
            for e in n.elts:
                if isinstance(e, ast.Constant) and isinstance(e.value, str) and e.value.endswith(".py") and " " not in e.value:
                    p = (f.parent / e.value)
                    if p.exists():
                        ran.setdefault(str(p.resolve()), []).append(f.name); todo.append((p.resolve(), f"run by {f.name}"))
    imported[f] = dict(why=why, imports=sorted(set(loc)))

# data files referenced (raw text, incl. docstrings) and lines
refs = {}
for f in imported:
    for i, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
        for m in FN.finditer(line):
            name = m.group(1)
            if name.endswith(".py"): continue
            refs.setdefault(name, []).append((f.name, i, bool(WRITE.search(line))))

# producers anywhere in the tree (exclude venv / .lake / old)
SKIP = ("venv", ".lake", "__pycache__", "node_modules")
allpy = [p for p in ROOT.rglob("*.py") if not any(s in p.parts for s in SKIP)]
texts = {}
for p in allpy:
    try: texts[p] = p.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception: pass
producers = {}
for name in refs:
    if "*" in name or name.startswith("."): continue
    base = name.split("/")[-1]
    for p, lines in texts.items():
        for i, line in enumerate(lines, 1):
            if base in line and WRITE.search(line):
                producers.setdefault(name, []).append(f"{p.relative_to(ROOT)}:{i}")
    # also look for 2-line pattern: name assigned to var then var written (heuristic left to human review)

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
out = dict(
    imported_or_run={str(f.relative_to(ROOT)): dict(v, sha256=sha(f), bytes=f.stat().st_size, mtime=os.path.getmtime(f)) for f, v in imported.items()},
    run_by_subprocess={str(Path(k).relative_to(ROOT)): v for k, v in ran.items()},
    external_packages=sorted(ext),
    data_refs={k: v for k, v in sorted(refs.items())},
    producers=producers)
Path(sys.argv[2]).write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
print(len(imported), "py files;", len(refs), "data names;", "ext:", sorted(ext))
