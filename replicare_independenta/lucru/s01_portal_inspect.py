import pandas as pd, json, glob
rows=[]
for f in glob.glob('../date/portal/harvest_*.jsonl'):
    for l in open(f,encoding='utf-8'):
        d=json.loads(l); d['file']=f.split('harvest_')[1]; rows.append(d)
p=pd.DataFrame(rows)
print(p.shape, p.columns.tolist())
print(p.groupby('file').agg(n=('req_nr','size'),nu=('req_nr','nunique'),det=('details_found','sum'),mn=('req_nr','min'),mx=('req_nr','max')))
print('unique req', p.req_nr.nunique())
u=p.drop_duplicates('req_nr',keep='last')
print(u.details_found.value_counts())
d=u[u.details_found==True]
for c in ['type_code','type_desc','phase_code','phase_desc','solution','is_judged','is_quick_finish','subtype_desc','resolution_goal','is_office']:
    if c in d: print('---',c); print(d[c].value_counts(dropna=False).head(25).to_string())
print(pd.crosstab(d.phase_desc, d.is_judged.astype(str)).to_string())
print(d[['request_date','solution_date','first_event_date','last_event_date','solution_term','release_term','n_solution_events']].head(20).to_string())
