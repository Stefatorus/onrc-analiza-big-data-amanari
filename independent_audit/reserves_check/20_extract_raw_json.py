"""Extract a compact, PSEUDONYMISED table from the raw BERC JSON (one file at a time).
No names, CUI, addresses, euid or raw UUIDs are written: firm / application / article ids
are replaced by salted 64-bit hashes (salt random per run, never stored).
Output: reserves_check/tmp/raw_compact.pkl (delete after use)."""
import sys as _sys, pathlib as _pl; _sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[2])); import config  # repo config.py
import json, glob, os, re, hashlib, secrets, sys, time
import pandas as pd, numpy as np
SALT = secrets.token_bytes(16)
def h(x):
    if not x: return 0
    return int.from_bytes(hashlib.blake2b(str(x).encode(), key=SALT, digest_size=8).digest(), 'little', signed=True)
FN = re.compile(r'^(\d+)_([^_]+)_([0-9.]+)_([^_]+)_(.*?)(?:\.pdf)?$', re.I)
cols = {k: [] for k in ['cat','app_nr_s','app','app_cty','created','publishable','published','res','sol','jt','siruta',
        'reg_year','src','f_office','f_appnr','f_date','f_code','f_doc','firm','app_id','art','corr','orig','has_docnr','has_folder','instance','fvis']}
files = sorted(glob.glob(str(config.ARTICLES_DIR / '*' / '*.json')))
t0=time.time(); bad=0; chunks=[]
def compact(df):
    for c in ['app','created','publishable','published','res']:
        df[c]=pd.to_datetime(df[c].astype(str).str[:19], errors='coerce')
    df['f_date']=pd.to_datetime(df.f_date, format='%d.%m.%Y', errors='coerce')
    for c in ['cat','app_cty','sol','jt','src','f_office','f_code','f_doc','app_nr_s','f_appnr']: df[c]=df[c].astype('category')
    df['siruta']=pd.to_numeric(df.siruta,errors='coerce').astype('float32'); df['reg_year']=pd.to_numeric(df.reg_year,errors='coerce').astype('float32')
    return df
for i,f in enumerate(files):
    cat = os.path.basename(f)[11:-5]
    try:
        with open(f, encoding='utf-8') as fh: L = json.load(fh)
    except Exception as e:
        bad+=1; print('BAD',f,e); continue
    for r in L:
        fnm = r.get('fileName') or ''
        m = FN.match(fnm)
        cols['cat'].append(cat); cols['app_nr_s'].append(r.get('applicationNr'))
        cols['app'].append(r.get('applicationDate')); cols['app_cty'].append(r.get('applicationCounty'))
        cols['created'].append(r.get('createdAt')); cols['publishable'].append(r.get('publishableAt'))
        cols['published'].append(r.get('publishedAt')); cols['res'].append(r.get('resolutionDate'))
        cols['sol'].append(r.get('resolution')); cols['jt'].append(r.get('juridicType')); cols['siruta'].append(r.get('siruta'))
        cols['reg_year'].append(r.get('registrationYear')); cols['src'].append(r.get('sourceCode'))
        cols['f_office'].append(m.group(1) if m else None); cols['f_appnr'].append(m.group(2) if m else None)
        cols['f_date'].append(m.group(3) if m else None); cols['f_code'].append(m.group(4) if m else None)
        cols['f_doc'].append(m.group(5)[:40] if m else (fnm[-40:] if fnm else None))
        cols['firm'].append(h(r.get('companyIdSource') or r.get('companyCode'))); cols['app_id'].append(h(r.get('applicationIdSource')))
        cols['art'].append(h(r.get('id'))); cols['corr'].append(h(r.get('idCorrectedArticle'))); cols['orig'].append(h(r.get('idOriginalArticle')))
        cols['has_docnr'].append(r.get('documentNr') is not None); cols['has_folder'].append(r.get('folderNr') is not None)
        cols['instance'].append(r.get('instance') is not None); cols['fvis'].append(r.get('isFileVisible'))
    del L
    if len(cols['cat'])>150000 or i==len(files)-1:
        chunks.append(compact(pd.DataFrame(cols)))
        for k in cols: cols[k]=[]
    if i%250==0: print(i,len(files),round(time.time()-t0),'s rows',len(cols['cat']),flush=True)
from pandas.api.types import union_categoricals
df = pd.concat(chunks, ignore_index=True); del chunks
for c in ['cat','app_cty','sol','jt','src','f_office','f_code','f_doc']: df[c]=df[c].astype('category')
df['app_nr_s']=df.app_nr_s.astype(str); df['f_appnr']=df.f_appnr.astype(str)
df.to_pickle(str(config.WORK_DIR / 'raw_compact.pkl'))
print('done', df.shape, 'bad files', bad, round(time.time()-t0),'s', df.memory_usage(deep=True).sum()/1e9,'GB')
