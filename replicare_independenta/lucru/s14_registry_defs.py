"""Recompute C41 and C101 under the definitions found in the report's claims registry (looked up after first pass)."""
from common import *
df=add_basic(load()); df=df[df.res>='2024-08-01']
ok=(df.W>=0)&(df.W<400)
def bd(x): return busdays_between(x.app.values.astype('datetime64[D]'),x.res.values.astype('datetime64[D]'))
w=lambda x,a,b:x[(x.res>=a)&(x.res<pd.Timestamp(b)+pd.Timedelta(days=1))]
f=open('res_registry_defs.txt','w',encoding='utf-8')
for lab,sub in [('modificari',df[df.strict&ok&(df.cat=='CERERE265')]),('inmatriculari',df[df.strict&ok&(df.cat=='INMATRIC265')]),('amanari',df[df.amanat&ok])]:
    x=w(sub,'2026-04-27','2026-06-28'); s=f'C101 27.04-28.06 {lab}: exactly 3rd wd {round((bd(x)==3).mean()*100,1)}%  n={len(x)}'; print(s); f.write(s+'\n')
key=['app_nr','app']
am=df[df.amanat][key].drop_duplicates(); am['had']=1
x=w(df[(df.cat=='INMATRIC265')&(df.sol=='Admis')&ok],'2026-11-01','2026-11-20').merge(am,on=key,how='left')
x=x[x.had.isna()]
for j in ['J','F']:
    y=x[x.jtype==j]; s=f'C41 INMATRIC Admis fara amanare 1-20.11 jtype={j}: >10 wd {round((bd(y)>10).mean()*100,1)}%  n={len(y)}'; print(s); f.write(s+'\n')
