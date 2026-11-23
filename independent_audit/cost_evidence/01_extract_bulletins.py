"""Task 1 extraction: parse every attached registrar decision in ALL 2026 BERC bulletin PDFs.

For each decision document (split on the 'Oficiul Registrului Comerţului de pe lângă Tribunalul' header) we keep:
bulletin nr (file stem), bulletin date, request nr, fiscal code (only for the local join; never exported), verb
(Admite/Respinge), and boolean object flags computed from the 'având ca obiect: ...' text (fallback: 'referitoare la').
Record-level output goes to _tmp/ (deleted at the end of the work); stdout carries aggregates only.
"""
import glob, os, re, pickle, sys, collections, unicodedata
from concurrent.futures import ProcessPoolExecutor
import fitz  # PyMuPDF
fitz.TOOLS.mupdf_display_errors(False)

HERE = os.path.dirname(os.path.abspath(__file__))
TMP = os.path.join(HERE, '_tmp'); os.makedirs(TMP, exist_ok=True)
SPLIT = re.compile(r'Oficiul\s+Registrului\s+Comer[tţț]ului\s+de\s+pe\s+l[aâ]ng[aă]\s+Tribunalul')


def norm(s):
    s = unicodedata.normalize('NFKD', s.lower())
    s = ''.join(ch for ch in s if not unicodedata.combining(ch))
    return re.sub(r'[^a-z0-9;]', '', s)          # de-spaced: robust to split words ("num ărul", "o biect")


# object flags on the de-spaced, diacritic-free, lower-case object text
FLAGS = {
    'caen_rev3':      r'actualizareobiect\w{0,20}conformcaen|caenrev|conformcaen',
    'activity_codes': r'domeniuprincipal|activitateprincipala|codobiectdeactivitate|codobiect|obiectuldeactivitate|obiectdeactivitate',
    'office_change':  r'modificaredatesediu|schimbaresediu|transfersediu|mutaresediu|sediulsocialsemuta|modificareadresa|altemodificarisediu',
    'office_docs':    r'prelungirevalabilitate|prelungiredurata\w{0,10}sediu|modificaredovadasediu|dovadasediu|valabilitateacte',
    'secondary':      r'sediisecundare|sediusecundar|sediuluisecundar|sediilorsecundare|punct\w{0,3}delucru|sucursal|filial|desfiintaresediu|deschideresediu',
    'capital_shares': r'capitalsocial|asociat|cesiune|partisociale|partilorsociale|participarestraina|actionar|transmitere\w{0,10}parti',
    'admins':         r'administrator|reprezentant|imputernicit|director|consiliudeadministratie|cenzor|auditor|membriconsiliu',
    'dissolution':    r'dizolvare|radiere|lichidare|suspendare|lichidator|inactivitate|inchideriiprocedurii',
    'resumption':     r'reluareactivitat|reluareaactivitat',
    'name_change':    r'schimbaredenumire|denumirefirm|emblema',
    'capital':        r'capitalsocial|participarestraina|majorarecapital|reducerecapital',
    'share_transfer': r'cesiune|transmitere\w{0,10}parti|transferparti|partisocialeintre|retragereasociat|retragere\w{0,12}asociat|adaugare\w{0,12}asociat|cooptare|intrareasociat|asociatunic\w{0,10}nou',
    'shareholder_data': r'modificaredateasociat|modificaredatepersoan\w{0,12}asociat|datedeidentificare|modificaredateactionar',
    'admin_change':   r'(?<!de)numire|revocare|incetaremandat|prelungiremandat|schimbareadministrator|modificareputeri',
    'admin_data':     r'modificaredateadministrator|modificaredatereprezentant|modificaredatepersoaneimputernicite',
    'ancillary':      r'depunereactconstitutiv|actconstitutivactualizat|declaratiepepropriaraspundere|declaratieipepropriaraspundere|declaratiadinpropriaraspundere|beneficiar|indreptare',
}
FLAGS = {k: re.compile(v) for k, v in FLAGS.items()}
# "prelungire durata de functionare" (firm duration) is not an office document; guard office_docs on 'sediu'
SEDIU = re.compile(r'sediu|sediul')


def parse(path):
    stem = os.path.splitext(os.path.basename(path))[0]
    try:
        doc = fitz.open(path)
        pages = [p.get_text() for p in doc]
    except Exception:
        return stem, None, None, []
    first = ' '.join(pages[:1])
    m = re.search(r'(\d{2}\.\d{2}\.\d{4})\s*Nr\.\s*(\d+)', first)
    bdate, bnr = (m.group(1), m.group(2)) if m else (None, None)
    txt = re.sub(r'\s+', ' ', ' '.join(pages))
    out = []
    for ch in SPLIT.split(txt)[1:]:
        a = re.search(r'\bAdmite\b', ch); rj = re.search(r'\bRespinge\b', ch)
        app = re.search(r'sub\s*num\s*[aă]\s*rul\s*(\d{5,8})', ch) or re.search(r'cererii[^.]{0,40}?nr\.?\s*(\d{5,8})', ch)
        cui = re.search(r'Cod\s+unic\s+de\s+[iî]nregistrare\s*:?\s*(?:RO)?\s*(\d{2,10})', ch)
        ob = re.search(r'av\s*[aâî]\s*n\s*d\s*ca\s*o\s*b\s*i\s*e\s*c\s*t\s*:?(.{0,1500}?)(?:potrivit\s+datelor|Dispune|Executori|$)', ch)
        src = 'avand'
        if not ob:
            ob = re.search(r'referitoare\s+la(.{0,1500}?)(?:Examin|Constat|$)', ch); src = 'referitoare' if ob else 'none'
        registration = bool(re.search(r'autoriz\w*\s+constituirea|[iî]nmatricul', ch[:4000]))
        o = norm(ob.group(1)) if ob else ''
        f = {k: bool(rx.search(o)) for k, rx in FLAGS.items()}
        if f['office_docs'] and not SEDIU.search(o):
            f['office_docs'] = False
        # 'cod obiect de activitate' inside the Rev.3 phrase is not a separate activity change
        if f['caen_rev3']:
            o2 = FLAGS['caen_rev3'].sub('', re.sub(r'actualizareobiectdeactivitate', '', o))
            f['activity_codes'] = bool(FLAGS['activity_codes'].search(o2))
        f['admin_change'] = f['admin_change'] and (f['admins'] or 'lichidator' in o or 'cenzor' in o)
        resid = ''
        if ob and not any(v for k, v in f.items() if k != 'ancillary'):
            w = re.sub(r'[\d/.,\-()]+', ' ', ob.group(1)).lower()
            w = re.sub(r'\b\w*[A-ZĂÂÎȘȚŞŢ]{2,}\w*\b', '', w)
            resid = ' '.join(w.split()[:6])
        out.append(dict(bulletin=stem, bnr=bnr, bdate=bdate, app_nr=int(app.group(1)) if app else None,
                        cui=int(cui.group(1)) if cui else None,
                        verb='admite' if a and (not rj or a.start() < rj.start()) else ('respinge' if rj else 'none'),
                        src=src, registration=registration, resid=resid, **f))
    return stem, bdate, bnr, out


def main():
    files = sorted(glob.glob(r'W:\SOLOResearch\bulletins\2026\*.pdf'))
    rows, meta = [], []
    with ProcessPoolExecutor(max_workers=6) as ex:
        for stem, bdate, bnr, out in ex.map(parse, files, chunksize=4):
            meta.append(dict(bulletin=stem, bdate=bdate, bnr=bnr, n=len(out)))
            rows.extend(out)
    with open(os.path.join(TMP, 'pdf_decisions.pkl'), 'wb') as fh:
        pickle.dump(dict(rows=rows, meta=meta), fh)
    c = collections.Counter()
    for r in rows:
        c['decisions'] += 1; c['src_' + r['src']] += 1; c['verb_' + r['verb']] += 1
        c['has_app'] += r['app_nr'] is not None; c['has_cui'] += r['cui'] is not None; c['registration'] += r['registration']
    print('bulletins', len(files), 'with date', sum(m['bdate'] is not None for m in meta), 'unreadable/empty', sum(m['n'] == 0 for m in meta))
    print(dict(c))
    print('bnr==stem', sum(m['bnr'] == m['bulletin'] for m in meta))
    months = collections.Counter((m['bdate'] or 'NA')[3:] for m in meta); print(sorted(months.items()))


if __name__ == '__main__':
    main()
