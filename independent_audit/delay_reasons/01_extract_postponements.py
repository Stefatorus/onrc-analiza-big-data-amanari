"""Step 1: extract every postponement notice ("Comunicare încheiere de amânare ... Motivul amânării: ...") from all 2026
BERC bulletin PDFs (PyMuPDF, same reader as cost_evidence/01). Record-level output (with request numbers, used only for the
local join to the decisions archive) goes to _tmp/ and is deleted at the end. stdout carries aggregates only.
"""
import glob, os, re, pickle, collections
from concurrent.futures import ProcessPoolExecutor
import fitz
fitz.TOOLS.mupdf_display_errors(False)

HERE = os.path.dirname(os.path.abspath(__file__))
TMP = os.path.join(HERE, '_tmp'); os.makedirs(TMP, exist_ok=True)
START = re.compile(r'Comunicare\s+[iî]ncheiere\s+de\s+am[aâ]nare')
REGION = re.compile(r'(Jude[tţț]ul\s+[A-ZĂÂÎȘȚŞŢ][\wăâîșțşţ\-]+(?:[\- ][A-ZĂÂÎȘȚŞŢ][\wăâîșțşţ]+)?|Municipiul\s+Bucure[sșş]ti)\s+1\.\s')
FIELD = {
    'din_data': re.compile(r'Din\s+data:\s*(\d{2}\.\d{2}\.\d{4})'),
    'sol': re.compile(r'Solu[tţț]ie:\s*([A-Za-zăâîșțşţĂÂÎȘȚ]+)'),
    'termen': re.compile(r'Termen\s+pentru\s+solu[tţț]ionare:\s*(\d{2}\.\d{2}\.\d{4})'),
    'app_nr': re.compile(r'nr\.\s*cerere:\s*(\d{5,8})'),
    'data_cerere': re.compile(r'data\s+cerere:\s*(\d{2}\.\d{2}\.\d{4})'),
}
MOTIV = re.compile(r'Motivul\s+am[aâ]n[aă]rii:\s*(.*?)(?=Termen\s+pentru\s+solu[tţț]ionare:|nr\.\s*cerere:|$)', re.S)


def parse(path):
    stem = os.path.splitext(os.path.basename(path))[0]
    try:
        doc = fitz.open(path)
        txt = re.sub(r'\s+', ' ', ' '.join(p.get_text() for p in doc))
    except Exception:
        return stem, None, -1, []
    m = re.search(r'(\d{2}\.\d{2}\.\d{4})\s*Nr\.\s*(\d+)', txt[:3000])
    bdate = m.group(1) if m else None
    # drop running page headers that may split a reason text across pages
    txt = re.sub(r'\d{0,3}\s*BULETINUL ELECTRONIC AL REGISTRULUI COMER[TȚŢ]ULUI Nr\.\s*\d+/\d{2}-\d{2}-\d{4}', ' ', txt)
    regions = [(r.start(), r.group(1)) for r in REGION.finditer(txt)]
    starts = [s.start() for s in START.finditer(txt)]
    out = []
    for i, s in enumerate(starts):
        # an entry ends at the next entry header "N. NAME Număr de ordine" -- approximate by the next 'Număr de ordine'
        nxt = txt.find('Număr de ordine în registrul', s)
        end = nxt if nxt != -1 else len(txt)
        if i + 1 < len(starts):
            end = min(end, starts[i + 1])
        ch = txt[s:end]
        rec = {k: (rx.search(ch).group(1) if rx.search(ch) else None) for k, rx in FIELD.items()}
        mm = MOTIV.search(ch)
        reg = [r for p, r in regions if p < s]
        # registry prefix (county code) of the J/F number just before the notice
        pre = txt[max(0, s - 700):s]
        jm = re.findall(r'registrul comer[tțţ]ului:\s*-?[JFC]?(\d{1,2})/', pre)
        out.append(dict(bulletin=stem, bdate=bdate, region=reg[-1] if reg else None, jcode=jm[-1] if jm else None,
                        reason=mm.group(1).strip() if mm else None, **rec))
    return stem, bdate, len(starts), out


def main():
    files = sorted(glob.glob(r'W:\SOLOResearch\bulletins\2026\*.pdf'))
    rows, meta = [], []
    with ProcessPoolExecutor(max_workers=6) as ex:
        for stem, bdate, n, out in ex.map(parse, files, chunksize=4):
            meta.append(dict(bulletin=stem, bdate=bdate, n=n)); rows.extend(out)
    with open(os.path.join(TMP, 'postponements_raw.pkl'), 'wb') as fh:
        pickle.dump(dict(rows=rows, meta=meta), fh)
    c = collections.Counter()
    for r in rows:
        c['notices'] += 1; c['with_reason'] += r['reason'] is not None; c['with_app'] += r['app_nr'] is not None
        c['with_din_data'] += r['din_data'] is not None; c['sol_' + str(r['sol'])] += 1; c['with_region'] += r['region'] is not None
    print('bulletins', len(files), 'unreadable', sum(m['n'] == -1 for m in meta), 'with>=1 notice', sum(m['n'] > 0 for m in meta))
    print(dict(c))
    print('notice months (din_data):', sorted(collections.Counter((r['din_data'] or 'NA')[3:] for r in rows).items()))
    print('bulletin months with notices:', sorted(collections.Counter((m['bdate'] or 'NA')[3:] for m in meta if m['n'] > 0).items()))
    lens = sorted(len(r['reason'] or '') for r in rows)
    print('reason length quantiles', [lens[int(q * (len(lens) - 1))] for q in (0, .1, .5, .9, .99, 1)] if lens else None)


if __name__ == '__main__':
    main()
