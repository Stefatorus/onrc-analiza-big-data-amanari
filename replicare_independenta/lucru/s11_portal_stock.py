"""C06, C13, C73/C09, C100: portal phases, KM by filing month, stock estimate weighted by counter density."""
from common import *
out=open('res_portal_stock.txt','w',encoding='utf-8')
def P(*a):
    s=' '.join(str(x) for x in a); print(s); out.write(s+'\n')
b=add_basic(load()); b=b[b.app>='2026-01-01']
env=b.groupby(b.app.dt.normalize()).app_nr.min()
pa=pd.read_pickle('portal_all_dedup.pkl')
d=pa[(pa.details_found==True)].copy(); d['rd']=pd.to_datetime(d.request_date)
# BERC strict final per number (exact timestamp match)
fin=b[b.strict][['app_nr','app','res','sol','cat']].sort_values('res').drop_duplicates(['app_nr','app'])
am=b[b.amanat][['app_nr','app','res']].sort_values('res').drop_duplicates(['app_nr','app'])
d=d.merge(fin.rename(columns={'res':'fin_res','sol':'fin_sol'}),left_on=['req_nr','rd'],right_on=['app_nr','app'],how='left').drop(columns=['app_nr','app'])
d=d.merge(am.rename(columns={'res':'am_res'}),left_on=['req_nr','rd'],right_on=['app_nr','app'],how='left').drop(columns=['app_nr','app'])
J=d[d.is_judged==1].copy()
# pending = only 'in procesare' (operare) and 'in solutionare' (registrator); 'in inscriere'/'inregistrata' treated as past decision
pend_ph={'Cerere in procesare':'operare','Cerere in solutionare':'registrator'}
J['stage']=J.phase_desc.map(pend_ph).fillna('rezolvat')
P('judged',len(J),' stage counts',J.stage.value_counts().to_dict())
P('   pending with BERC final (inconsistent):', int(((J.stage!='rezolvat')&J.fin_res.notna()).sum()), ' resolved without BERC final:', int(((J.stage=='rezolvat')&J.fin_res.isna()).sum()))
P('   resolved w/o BERC final by type:', J[(J.stage=='rezolvat')&J.fin_res.isna()].type_desc.value_counts().to_dict())
pend=J[J.stage!='rezolvat']
P('== C06 share at operare among pending (unweighted)', round((pend.stage=='operare').mean()*100,1), ' n',len(pend))
P('   by type', pend.groupby('type_desc').stage.apply(lambda s:(s=='operare').mean()).round(3).to_dict(), pend.type_desc.value_counts().to_dict())
P('== C13 oldest pending filing date', pend.rd.min().date(), ' | if in inscriere counted pending:', J[J.phase_desc.isin(['Cerere in procesare','Cerere in solutionare','Cerere in inscriere'])].rd.min().date())
# ---- weights: stratum = ISO week of the counter; counter numbers per week from BERC envelope
envw=env.groupby(env.index.to_period('W-SUN')).min()
edges=list(envw.values)+[pa.req_nr.max()+1]
weeks=list(envw.index)
pa['stratum']=pd.cut(pa.req_nr,bins=edges,labels=False,right=False)
ns=pa.groupby('stratum').size()
width=pd.Series(np.diff(edges),index=range(len(edges)-1))
wmap=(width/ns).dropna()
d=d.merge(pa[['req_nr','stratum']],on='req_nr',how='left'); J=J.merge(pa[['req_nr','stratum']],on='req_nr',how='left')
J['w']=J.stratum.map(wmap)
P('   weights: median',round(J.w.median()),' range',round(J.w.min()),round(J.w.max()),' strata sampled',len(wmap))
pend=J[J.stage!='rezolvat']
P('== C06 weighted share at operare', round(np.average(pend.stage=='operare',weights=pend.w)*100,1))
# ---- stock estimate at dates
def stock(t, resolved_nonberc='before'):
    t=pd.Timestamp(t)
    x=J[J.rd<t]
    pending_t = (x.fin_res>=t) | (x.fin_res.isna() & (x.stage!='rezolvat'))
    if resolved_nonberc=='after':
        pending_t = pending_t | (x.fin_res.isna() & (x.stage=='rezolvat'))
    return (x.w*pending_t).sum(), pending_t.sum()
for t in ['2026-10-31','2026-11-07','2026-11-21']:
    s,n=stock(t); s2,_=stock(t,'after')
    P('== C100 stock at',t,'est',round(s),' n sampled pending',int(n),' (if non-BERC-resolved counted pending:',round(s2),')')
# bootstrap CI for 6/7 Nov within strata
rng=np.random.default_rng(1); bs=[]
t=pd.Timestamp('2026-11-07')
J['pend7']=((J.rd<t)&((J.fin_res>=t)|(J.fin_res.isna()&(J.stage!='rezolvat')))).astype(float)
pa2=pa.merge(J[['req_nr','pend7']],on='req_nr',how='left').fillna({'pend7':0})
grp=[g.pend7.values for _,g in pa2.groupby('stratum')]
wid=[width[k] for k,_ in pa2.groupby('stratum')]
for _ in range(1000):
    bs.append(sum(wd_*rng.choice(v,len(v)).mean() for v,wd_ in zip(grp,wid)))
P('   bootstrap 95% (stratified) for 7 Nov:', np.round(np.percentile(bs,[2.5,97.5])))
# ---- C73/C09 KM by filing month (event = BERC strict final; censored 21.11 for pending)
from math import log
def km_median(T,E):
    o=np.argsort(T); T=np.asarray(T)[o]; E=np.asarray(E)[o]
    S=1.0; n=len(T); i=0
    while i<len(T):
        t=T[i]; d_=0; c=0
        while i<len(T) and T[i]==t:
            d_+=E[i]; c+=1; i+=1
        if d_>0:
            S*=1-d_/n
        n-=c
        if S<=0.5: return t
    return np.nan
cen=pd.Timestamp('2026-11-21')
K=J[(J.stage!='rezolvat')|J.fin_res.notna()].copy()
K['ev']=K.fin_res.notna()
K['T']=np.where(K.ev,(K.fin_res-K.rd).dt.total_seconds()/86400,(cen-K.rd).dt.total_seconds()/86400)
K['T']=np.floor(K['T'])
K['m']=K.rd.dt.to_period('M')
P('== C73/C09 KM sample size',len(K))
for m,g in K.groupby('m'):
    P('  ',m,'n',len(g),'resolved%',round(g.ev.mean()*100,1),' median resolved-only',round(g.loc[g.ev,'T'].median(),1),' KM median',km_median(g['T'].values,g.ev.values))
s=K[K.m==pd.Period('2026-09')]; s=s.assign(wk=s.rd.dt.to_period('W-SUN'))
for w_,g in s.groupby('wk'):
    P('   Sep week',w_,'n',len(g),'resolved%',round(g.ev.mean()*100,1),'KM median',km_median(g['T'].values,g.ev.values))

# ---- extra: artefact check - stock without registrations (invisible while pending)
P('== C100 stock by date, all judged vs excluding Inmatriculare (pending registrations are invisible in portal)')
for t in ['2026-10-30','2026-10-31','2026-11-06','2026-11-07','2026-11-20','2026-11-21']:
    tt=pd.Timestamp(t); x=J[J.rd<tt]
    pt=(x.fin_res>=tt)|(x.fin_res.isna()&(x.stage!='rezolvat'))
    ni=x.type_desc!='Înmatriculare'
    P('  ',t,'all',round((x.w*pt).sum()),' no-inmatric',round((x.w*(pt&ni)).sum()),' inmatric part',round((x.w*(pt&~ni)).sum()))
# phases of oldest pending
P('== C13 phases of 4 oldest pending (dates only):', [(str(a.date()),b) for a,b in pend.nsmallest(4,'rd')[['rd','phase_desc']].values])
# inflow by month split registration / other (counter x share)
pa_m=pa.copy()
out.close()
