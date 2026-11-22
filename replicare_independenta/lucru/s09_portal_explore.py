"""Portal sample: dedupe, coverage, link to BERC, counter-date mapping."""
from common import *
import json, glob
rows=[]
for f in sorted(glob.glob('../date/portal/harvest_*.jsonl')):
    for l in open(f,encoding='utf-8'):
        d=json.loads(l); d['file']=os.path.basename(f); d.pop('raw_search',None); d.pop('raw_details',None); rows.append(d)
p=pd.DataFrame(rows)
p['rich']=p.details_found.fillna(False).astype(int)*10+p.notna().sum(axis=1)/100
p=p.sort_values('rich').drop_duplicates('req_nr',keep='last')
print('unique',len(p),'details',p.details_found.sum())
print('err values', p.err.value_counts().head(10).to_dict())
print('s1_found', p.s1_found.value_counts(dropna=False).to_dict())
print('has_company_id x details', pd.crosstab(p.has_company_id,p.details_found).to_dict())
d=p[p.details_found==True].copy()
d['rd']=pd.to_datetime(d.request_date)
print('request_date range',d.rd.min(),d.rd.max())
print('solution_date nonempty',(d.solution_date.fillna('')!='').sum(),' solution nonempty',(d.solution.fillna('')!='').sum(),' last_event nonempty',(d.last_event_date.fillna('')!='').sum())
print(pd.crosstab(d.phase_desc,d.solution.fillna('')).to_string())
# counter monotonic vs date
d=d.sort_values('req_nr')
print('req_nr vs date spearman', d[['req_nr']].assign(t=d.rd.astype('int64')).corr(method='spearman').iloc[0,1])
print(d[['req_nr','rd']].iloc[::150].to_string())
# BERC link: 2026 app_nr
b=load(); b=b[b.app>='2026-01-01']
print('BERC 2026 app_nr range', b.app_nr.min(), b.app_nr.max())
m=d.merge(b[['app_nr','app','res','sol','cat']].drop_duplicates(['app_nr','cat','res']),left_on='req_nr',right_on='app_nr',how='left')
m['dt']=(m.app-m.rd).dt.total_seconds()
print('linked rows',m.app_nr.notna().sum(),' |app-rd|<60s',(m.dt.abs()<60).sum(), ' of details',len(d))
print('linked by type', m[m.app_nr.notna()].groupby('type_desc').size().to_dict())
print('judged linked', m[(m.is_judged==1)].groupby(m.app_nr.notna()).size().to_dict())
# daily counter envelope from BERC
bb=b.groupby(b.app.dt.normalize()).app_nr.agg(['min','max','size'])
print(bb.loc['2026-09-01':'2026-09-12'].to_string()); print(bb.tail(10).to_string())
print(bb.loc['2026-01-02':'2026-01-10'].to_string())
d.to_pickle('portal_dedup.pkl'); p.to_pickle('portal_all_dedup.pkl')
