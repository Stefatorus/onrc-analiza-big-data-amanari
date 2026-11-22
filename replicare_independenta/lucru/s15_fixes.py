"""Follow-up checks: stratum-weighted monthly inflow (C99) with calibration, C71 multi-year, P05 robust, C87 w/o 20.11, filing-time offset."""
from common import *
out=open('res_fixes.txt','w',encoding='utf-8')
def P(*a):
    s=' '.join(str(x) for x in a); print(s); out.write(s+'\n')
B=add_basic(load())
b=B[B.app>='2026-01-01']
env=b.groupby(b.app.dt.normalize()).app_nr.min()
pa=pd.read_pickle('portal_all_dedup.pkl')
# weekly strata on the counter
envw=env.groupby(env.index.to_period('W-SUN')).min()
edges=list(envw.values)+[pa.req_nr.max()+1]
pa['stratum']=pd.cut(pa.req_nr,bins=edges,labels=False,right=False)
width=pd.Series(np.diff(edges),index=range(len(edges)-1)); ns=pa.groupby('stratum').size()
pa['w']=pa.stratum.map(width/ns)
pa['judged']=((pa.details_found==True)&(pa.is_judged==1)).astype(float)
inB=set(b.app_nr.unique()); pa['inBERC']=pa.req_nr.isin(inB).astype(float)
# month of each sampled number from counter position (day mapping via envelope)
day_starts=env.values; days=env.index
idx=np.searchsorted(day_starts,pa.req_nr.values,side='right')-1
pa['day']=days[np.clip(idx,0,len(days)-1)]
pa['m']=pa.day.dt.to_period('M')
# BERC distinct dossiers by filing month and counter numbers by month
key=b.drop_duplicates(['app_nr','app'])
P('== C99 stratum-weighted inflow (judged requests) per wd; calibration: weighted in-BERC share vs BERC/counter')
res={}
for m,g in pa[pa.m>=pd.Period('2026-05')].groupby('m'):
    a=m.start_time; e=min(m.end_time.normalize(),pd.Timestamp('2026-11-19'))
    lo=env[env.index>=a].iloc[0]; nxt=env[env.index>e]; hi=nxt.iloc[0] if len(nxt) else env.max()+1
    nc=hi-lo; wd=wd_count(a,e)
    wsum=g.w.sum(); sh=(g.w*g.judged).sum()/wsum; shB=(g.w*g.inBERC).sum()/wsum
    bcount=((key.app>=a)&(key.app<e+pd.Timedelta(days=1))).sum()
    # stratified SE approx
    se=np.sqrt(((g.w**2)*(g.judged-sh)**2).sum())/wsum
    res[str(m)]=(nc*sh/wd,wd)
    P('  ',m,'n',len(g),'weighted judged share',round(sh,3),'est/wd',round(nc*sh/wd),'(95%',round(nc*(sh-1.96*se)/wd),'-',round(nc*(sh+1.96*se)/wd),')',' weighted inBERC',round(shB,3),' BERC/counter',round(bcount/nc,3),' BERC dossiers/wd',round(bcount/wd))
ao=['2026-08','2026-09','2026-10']; P('   Aug-Oct weighted',round(sum(res[m][0]*res[m][1] for m in ao)/sum(res[m][1] for m in ao)))
mj=['2026-05','2026-06','2026-07']; P('   May-Jul weighted',round(sum(res[m][0]*res[m][1] for m in mj)/sum(res[m][1] for m in mj)))
# ---- C71: filings per wd by filing month relative to November of the previous/same year
E=B[B.cat.isin(['CERERE265','INMATRIC265','AUTO_AMANARI'])]
Enew=E[E.app>='2024-08-01'].drop_duplicates(['app_nr','app'])
Eold=E[E.app<'2024-07-26'].drop_duplicates(['county','app_nr','app'])
EE=pd.concat([Eold,Enew])
mm=EE.groupby(EE.app.dt.to_period('M')).size()
per=pd.Series({m:mm[m]/wd_count(m.start_time,m.end_time.normalize()) for m in mm.index if m>=pd.Period('2023-04') and m<=pd.Period('2026-08')})
P('== C71 BERC filings per wd by filing month:'); P(per.round(0).to_string())
for y in [2024,2025,2026]:
    nov=per.get(pd.Period(f'{y-1}-11'))
    if nov: P('   ',y,'Jan/Feb/Mar vs Nov',y-1,':',[round(per[pd.Period(f"{y}-{k:02d}")]/nov-1,3) for k in (1,2,3)])
for y in [2023,2025]:
    nov=per[pd.Period(f'{y}-11')]; P('   ',y,'Jul/Aug vs Nov same year:',[round(per[pd.Period(f"{y}-{k:02d}")]/nov-1,3) for k in (7,8)])
# ---- P05 robust daily counter increments
st=b.groupby(b.app.dt.normalize()).app_nr.agg(lambda s:s.quantile(0.01)); en=b.groupby(b.app.dt.normalize()).app_nr.agg(lambda s:s.quantile(0.99))
inc_q=st.diff().shift(-1)
rng_=(en-st)
P('== P05 robust: max of next-day-q01 minus q01:',int(inc_q.max()),str(inc_q.idxmax().date()),' top3',{str(k.date()):int(v) for k,v in inc_q.nlargest(3).items()})
P('   q99-q01 within day max:',int(rng_.max()),str(rng_.idxmax().date()), ' around 12-14 Jan:',{str(k.date()):int(v) for k,v in inc_q.loc['2026-01-09':'2026-01-15'].items()})
P('   Sept max (q01 diff):', int(inc_q.loc['2026-09'].max()), str(inc_q.loc['2026-09'].idxmax().date()))
# ---- C87 without 20.11 (both years same window 1.10-19.11)
for y in [2025,2026]:
    a=f'{y}-10-01'; e=f'{y}-11-19'; n=((B.res>=a)&(B.res<pd.Timestamp(e)+pd.Timedelta(days=1))).sum()
    P('== C87 all decisions/wd 1.10-19.11',y,round(n/wd_count(a,e),1))
# ---- filing-time offset (fraction of day) on the new platform, 2025 filings
f=B[(B.app>='2025-01-01')&(B.app<'2026-01-01')]
frac=(f.app-f.app.dt.normalize()).dt.total_seconds()/86400
P('== filing time of day 2025: mean fraction',round(frac.mean(),3),' median',round(frac.median(),3))
out.close()

# ---- Nov 1-19: counter end taken from portal (first sampled number filed on 20.11), since BERC has few 19.11 filings
out=open('res_fixes.txt','a',encoding='utf-8')
dd=pa[pa.details_found==True].copy(); dd['rd']=pd.to_datetime(dd.request_date)
hi=dd[dd.rd>='2026-11-20'].req_nr.min(); lo=env[env.index>='2026-11-01'].iloc[0]
g=pa[(pa.req_nr>=lo)&(pa.req_nr<hi)]
sh=(g.w*g.judged).sum()/g.w.sum(); se=np.sqrt(((g.w**2)*(g.judged-sh)**2).sum())/g.w.sum(); wd=wd_count('2026-11-01','2026-11-19')
P('== C99 Nov 1-19 with portal end-of-counter',int(hi),'est/wd',round((hi-lo)*sh/wd),'(95%',round((hi-lo)*(sh-1.96*se)/wd),'-',round((hi-lo)*(sh+1.96*se)/wd),') n',len(g))
out.close()
