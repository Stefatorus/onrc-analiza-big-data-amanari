"""Step 1: extract every REJECTION decision ("ÎNCHEIERE ... urmează a respinge prezenta cerere, pe motiv: ... D I S P U N E Respinge")
from all 2026 BERC bulletin PDFs (PyMuPDF, same reader as delay_reasons/01 and cost_evidence/01).

Per page the running header ("BULETINUL ELECTRONIC ... Nr.x/dd-mm-yyyy"), the leading document-page marker (" k / m") and the trailing
bulletin page number are stripped BEFORE pages are joined, so that a decision split across pages is read as one text.
Also collected:
  * the bulletin index entries ("Încheieri pronunțate în soluționarea cererilor de înmatriculare" = registrations /
    "... altor cereri de înregistrare" = amendments/other; Tip act, Încheiere nr., din data, Soluție, nr. cerere) for every solution;
  * the postponement notices of the same bulletins (parsed with delay_reasons/01 `parse`, imported read-only), kept only for the
    request numbers that are later rejected (pair comparison in step 7).
Record-level output (request numbers, raw reason text) goes to _tmp/ and is deleted at the end. Only the span between
"urmează a respinge ... pe motiv" and "D I S P U N E" is kept as reason text (the header with firm, registrar, applicant is never kept).
stdout: aggregates only.
"""
import sys; sys.dont_write_bytecode = True  # never leave __pycache__ in delay_reasons (read-only reuse)
import glob, os, re, pickle, collections, importlib.util
from concurrent.futures import ProcessPoolExecutor
import fitz
fitz.TOOLS.mupdf_display_errors(False)

HERE = os.path.dirname(os.path.abspath(__file__))
TMP = os.path.join(HERE, '_tmp'); os.makedirs(TMP, exist_ok=True)
DR = os.path.join(HERE, '..', 'delay_reasons')


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


DR01 = _load(os.path.join(DR, '01_extract_postponements.py'), 'dr01')   # read-only reuse of the postponement parser

HDR = re.compile(r'BULETINUL ELECTRONIC AL REGISTRULUI COMER[TȚŢ]ULUI Nr\.\s*\d+/\d{2}-\d{2}-\d{4}')
IDX = re.compile(r'(Încheieri pronunțate în soluționarea (?:cererilor de înmatriculare|altor cereri de înregistrare))\s*Tip act:.{0,40}?'
                 r'Încheiere nr\.:\s*(\d+)\s*din data:\s*(\d{2}\.\d{2}\.\d{4})\s*Solu[tțţ]ie:\s*([A-Za-zăâîșțşţĂÂÎȘȚ ]+?)\s*nr\. cerere:\s*(\d+)')
DOS = re.compile(r'DOSAR NR\.\s*(\d+)\s*/\s*(\d{2}\.\d{2}\.\d{4})\s*ÎNCHEIERE nr\.\s*(\d+)\s*Pronun[tţț]at[aă] [iî]n data de:\s*(\d{2}\.\d{2}\.\d{4})')
ROMANIA = re.compile(r'R O M [AÂ] N I A')
URM = re.compile(r'urmeaz[aă] a respinge (?:prezenta )?cerere(?:a)?\s*,?\s*(?:pe motiv(?:ul|ele)?\s*(?:c[aă])?\s*:?)?', re.I)
DISP = re.compile(r'D\s?I\s?S\s?P\s?U\s?N\s?E\s*:?\s*(\w+)')


def page_text(p):
    t = re.sub(r'\s+', ' ', p.get_text()).strip()
    t = HDR.sub(' ', t)
    t = re.sub(r'^\s*\d{1,2}\s*/\s*\d{1,2}\s+', ' ', t)      # leading document-page marker " k / m"
    t = re.sub(r'\s+\d{1,4}\s*$', ' ', t)                     # trailing bulletin page number
    return t.strip()


def parse(path):
    stem = os.path.splitext(os.path.basename(path))[0]
    try:
        doc = fitz.open(path)
        txt = ' '.join(page_text(p) for p in doc)
    except Exception:
        return stem, None, [], [], []
    m = re.search(r'(\d{2}\.\d{2}\.\d{4})\s*Nr\.\s*(\d+)', txt[:3000])
    bdate = m.group(1) if m else None
    idx = [dict(bulletin=stem, section='INMATRICULARE' if 'înmatriculare' in g.group(1) else 'ALTE_CERERI', inch_nr=g.group(2),
                idx_date=g.group(3), idx_sol=g.group(4).strip(), app_nr=g.group(5)) for g in IDX.finditer(txt)]
    docs = []
    ds = list(DOS.finditer(txt))
    for i, d in enumerate(ds):
        end = ds[i + 1].start() if i + 1 < len(ds) else len(txt)
        body = txt[d.start():end]
        r = ROMANIA.search(body, 50)
        if r:
            body = body[:r.start()]
        disp = DISP.search(body)
        u = URM.search(body)
        reason = None
        if u:
            e = DISP.search(body, u.end())
            reason = body[u.end(): e.start()] if e else body[u.end(): u.end() + 8000]
        dword = disp.group(1) if disp else None
        is_rej = bool(u) or (dword or '').lower().startswith('respin')
        if not is_rej:
            docs.append(dict(bulletin=stem, app_nr=d.group(1), dword=dword, rejected=False))
            continue
        docs.append(dict(bulletin=stem, bdate=bdate, app_nr=d.group(1), data_cerere=d.group(2), inch_nr=d.group(3), din_data=d.group(4),
                         dword=dword, rejected=True, has_urm=bool(u), has_disp_after=bool(u and DISP.search(body, u.end())),
                         reason=reason.strip() if reason else None))
    try:
        _, _, _, post = DR01.parse(path)
    except Exception:
        post = []
    post = [dict(bulletin=stem, app_nr=x['app_nr'], din_data=x['din_data'], data_cerere=x['data_cerere'], reason=x['reason'])
            for x in post if x.get('reason')]
    return stem, bdate, idx, docs, post


def main():
    files = sorted(glob.glob(r'W:\SOLOResearch\bulletins\2026\*.pdf'))
    IDXR, DOCS, POST, unread = [], [], [], 0
    with ProcessPoolExecutor(max_workers=6) as ex:
        for stem, bdate, idx, docs, post in ex.map(parse, files, chunksize=4):
            unread += bdate is None and not idx and not docs
            IDXR.extend(idx); DOCS.extend(docs); POST.extend(post)
    rej = [d for d in DOCS if d['rejected']]
    rej_apps = {d['app_nr'] for d in rej}
    POST = [p for p in POST if p['app_nr'] in rej_apps]
    with open(os.path.join(TMP, 'rejections_raw.pkl'), 'wb') as fh:
        pickle.dump(dict(index=IDXR, rejections=rej, postponements_of_rejected=POST,
                         n_docs=len(DOCS), n_files=len(files)), fh)
    c = collections.Counter()
    for d in rej:
        c['rejection_docs'] += 1; c['with_urmeaza'] += d['has_urm']; c['with_reason'] += bool(d['reason'])
        c['reason_closed_by_DISPUNE'] += d['has_disp_after']; c['dispune_word_' + str(d['dword'])[:8]] += 1
    print('bulletins', len(files), 'unreadable/empty', unread, 'decision documents', len(DOCS))
    print(dict(c))
    ic = collections.Counter((x['section'], x['idx_sol'], x['idx_date'][3:]) for x in IDXR)
    print('index entries (section, solution, month) top:', ic.most_common(14))
    print('rejection docs by decision month:', sorted(collections.Counter(d['din_data'][3:] for d in rej).items()))
    print('postponement notices for rejected requests:', len(POST))
    lens = sorted(len(d['reason'] or '') for d in rej)
    print('reason length quantiles', [lens[int(q * (len(lens) - 1))] for q in (0, .1, .5, .9, .99, 1)])
    try:   # delay_reasons/01 creates its own (empty) _tmp at import: remove it so nothing is left in that folder
        os.rmdir(os.path.join(DR, '_tmp'))
    except OSError:
        pass


if __name__ == '__main__':
    main()
