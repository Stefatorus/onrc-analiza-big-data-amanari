"""BERC replications batch 2: postponements, fast lane, rejections, counties, cohorts, press."""
from common import *
from scipy import stats
out=open('res_berc_more.txt','w',encoding='utf-8')
def P(*a):
    s=' '.join(str(x) for x in a); print(s); out.write(s+'\n')
df=add_basic(load())
df=df[df.res>='2023-04-01'].copy()
ok=(df.W>=0)&(df.W<400)
S=df[df.strict & ok]; SB=df[df.strict]; AM=df[df.amanat]
def win(sub,a,b,col='res'):
    return sub[(sub[col]>=a)&(sub[col]<pd.Timestamp(b)+pd.Timedelta(days=1))]
def bdays(x):
    return busdays_between(x.app.values.astype('datetime64[D]'),x.res.values.astype('datetime64[D]'))

# ---------- C101 exploration: distribution of working days after 27.04
x=win(S,'2026-04-27','2026-07-31'); bd=bdays(x)
P('== C101 strict 27.04-31.07 wd distribution', pd.Series(bd).value_counts(normalize=True).sort_index().head(8).round(3).to_dict())
for lab,sub in [('amanari',AM[(AM.W>=0)&(AM.W<400)]),('inmatric',S[S.cat=='INMATRIC265'])]:
    y=win(sub,'2026-04-27','2026-07-31'); P('   ',lab, pd.Series(bdays(y)).value_counts(normalize=True).sort_index().head(8).round(3).to_dict())
for a,b in [('2026-04-27','2026-05-31'),('2026-06-01','2026-06-30'),('2026-07-01','2026-07-31')]:
    y=win(S,a,b); P('   strict exactly 3rd wd',a,b, round((bdays(y)==3).mean()*100,1))

# ---------- linkage postponements <-> finals (post Aug 2024)
key=['app_nr','app']
N=df[df.app>='2024-08-01']
am=N[N.amanat][key+['res']]
fin=N[N.strict & ((N.W>=0)&(N.W<400))][key+['res','W','cat','sol','jtype','county']]
nov=win(fin,'2026-11-01','2026-11-20')
amg=am.groupby(key).agg(n_am=('res','size'),first_am=('res','min'),last_am=('res','max')).reset_index()
nv=nov.merge(amg,on=key,how='left')
# only postponements before the final
nv['n_am']=nv['n_am'].fillna(0)
P('== C74 Nov 1-20 finals with >=1 prior amanare', round((nv.n_am>=1).mean()*100,2), ' dist', nv.n_am.clip(upper=4).value_counts(normalize=True).sort_index().round(4).to_dict())
P('   median W postponed vs not', round(nv.loc[nv.n_am>=1,'W'].median(),1), round(nv.loc[nv.n_am==0,'W'].median(),1))
pp=nv[nv.n_am>=1]
P('== C37 finals Nov with amanare: median days last amanare->final', round(((pp.res-pp.last_am).dt.total_seconds()/86400).median(),1),
  ' median days app->first amanare', round(((pp.first_am-pp.app).dt.total_seconds()/86400).median(),1))
amn=win(N[N.amanat & (N.W>=0)],'2026-11-01','2026-11-20')
P('   amanari issued in Nov: median W', round(amn.W.median(),1), ' n',len(amn))
# first postponements issued in Nov
amfirst=am.sort_values('res').drop_duplicates(key)
f1=win(amfirst,'2026-11-01','2026-11-20'); P('   first amanari issued in Nov: median W',round(((f1.res-f1.app).dt.total_seconds()/86400).median(),1))

# ---------- C41: INMATRIC admitted without amanare in Nov, >10 working days
inm=nv[(nv.cat=='INMATRIC265')&(nv.sol=='Admis')&(nv.n_am==0)]
b=bdays(inm)
P('== C41 inmatric admis no amanare Nov: >10 wd',round((b>10).mean()*100,1),' >=10',round((b>=10).mean()*100,1),' n',len(inm))
inm2=nv[(nv.cat=='INMATRIC265')&(nv.sol=='Admis')]
P('   incl. postponed: >10 wd', round((bdays(inm2)>10).mean()*100,1))

# ---------- C38 / C102 fast lane 2-19 Nov
f=win(S,'2026-11-02','2026-11-19')
for cat in ['CERERE265','INMATRIC265']:
    g=f[f.cat==cat]; P('== C38',cat,'share W<=14',round((g.W<=14).mean()*100,1),' median',round(g.W.median(),1),' n',len(g))
fast=f[f.cat.isin(['CERERE265','INMATRIC265'])]
fa=fast[fast.W<=14]; sl=fast
P('== C102 rejected share fast',round((fa.sol=='Respins').mean()*100,1),' all',round((sl.sol=='Respins').mean()*100,1),
  ' jtype F fast',round((fa.jtype=='F').mean()*100,1),' all',round((sl.jtype=='F').mean()*100,1))
P('   rejected share in non-fast', round((sl[sl.W>14].sol=='Respins').mean()*100,1), ' F non-fast', round((sl[sl.W>14].jtype=='F').mean()*100,1))
smp=fast.sample(200000,random_state=1) if len(fast)>200000 else fast
tau=stats.kendalltau(smp.app.values.astype('int64'),smp.res.values.astype('int64'))
P('   Kendall tau app vs res (2-19 Nov finals)',round(tau.statistic,3))
# fast lane by sol
P('   fast lane composition by sol', fa.sol.value_counts(normalize=True).round(3).to_dict())

# ---------- C39 / C57 rejection shares (strict finals, counts)
def rej(a,b,sub=SB):
    x=win(sub,a,b); return round((x.sol=='Respins').mean()*100,2), len(x)
P('== C39 rejection share old (Apr23-17Jul24)',rej('2023-04-01','2024-07-17'),' crisis Aug-20Nov26',rej('2026-08-01','2026-11-20'))
P('== C57 S2 2025',rej('2025-07-01','2025-12-31'),' 2025',rej('2025-01-01','2025-12-31'),' 1.10-20.11.26',rej('2026-10-01','2026-11-20'),' H1 2026',rej('2026-01-01','2026-06-30'))
P('   S2 2025 median W', round(win(S,'2025-07-01','2025-12-31').W.median(),2))
for cat in ['CERERE265','INMATRIC265']:
    P('   by cat',cat,'old',rej('2023-04-01','2024-07-17',SB[SB.cat==cat]),'2025',rej('2025-01-01','2025-12-31',SB[SB.cat==cat]),'crisis',rej('2026-08-01','2026-11-20',SB[SB.cat==cat]))

# ---------- Counties C49 C75 C89 C90 C88
c=win(S,'2026-11-01','2026-11-18'); c=c[c.county!='CC']
cm=c.groupby('county',observed=True).W.agg(['median','size'])
cm=cm[cm['size']>0]
P('== C49 county medians 1-18 Nov: min',round(cm['median'].min(),2),cm['median'].idxmin(),' max',round(cm['median'].max(),2),cm['median'].idxmax(),' median of offices',round(cm['median'].median(),2),' n offices',len(cm),' min N',cm['size'].min())
P('   top 6:', cm['median'].sort_values(ascending=False).head(6).round(2).to_dict())
P('   CV %', round(cm['median'].std(ddof=1)/cm['median'].mean()*100,2), ' (ddof0)', round(cm['median'].std(ddof=0)/cm['median'].mean()*100,2))
P('   N per county sample (AB,B,CJ,CS):', cm.loc[['AB','B','CJ','CS'],'size'].to_dict())
# quantization: distribution of rounded medians
P('   distinct medians (1dp):', cm['median'].round(1).value_counts().head(8).to_dict())
cc=win(S[S.cat=='CERERE265'],'2026-11-01','2026-11-18'); cc=cc[cc.county!='CC']
ccm=cc.groupby('county',observed=True).W.median()
P('   CERERE-only county medians range',round(ccm.min(),1),round(ccm.max(),1))
# 2025 medians and Spearman
c25=win(S,'2025-01-01','2025-12-31'); c25=c25[c25.county!='CC']
m25=c25.groupby('county',observed=True).W.median()
j=pd.concat([m25,cm['median']],axis=1,keys=['y25','nov']).dropna()
rho=stats.spearmanr(j.y25,j.nov)
# bootstrap CI over offices
rng=np.random.default_rng(0); bs=[]
for _ in range(2000):
    ii=rng.integers(0,len(j),len(j)); bs.append(stats.spearmanr(j.y25.values[ii],j.nov.values[ii]).statistic)
P('== C75 Spearman 2025 vs Nov',round(rho.statistic,3),' boot95',np.round(np.nanpercentile(bs,[2.5,97.5]),2))
# C90 rejection by county, crisis Aug-Nov 2026 (strict finals counts)
r=win(SB,'2026-08-01','2026-11-20'); r=r[r.county!='CC']
rr=r.groupby('county',observed=True).sol.apply(lambda s:(s=='Respins').mean()*100).sort_values()
P('== C90 rejection by county crisis: top3',rr.tail(3).round(2).to_dict(),' min',rr.head(2).round(2).to_dict(), ' range ratio',round(rr.max()/rr.min(),1))
r25=win(SB,'2025-01-01','2025-12-31'); r25=r25[r25.county!='CC']
rr25=r25.groupby('county',observed=True).sol.apply(lambda s:(s=='Respins').mean()*100)
P('   Spearman rejection 2025 vs crisis', round(stats.spearmanr(rr25.loc[rr.index],rr).statistic,2))
# C88: monthly office median minus national, max excess Jan2025-Jul2026
z=win(S,'2025-01-01','2026-07-31'); z=z[z.county!='CC']
z['m']=z.res.dt.to_period('M')
nat=z.groupby('m').W.median()
om=z.groupby(['county','m'],observed=True).W.median().unstack()
ex=om.sub(nat,axis=1)
mx=ex.max(axis=1).sort_values(ascending=False)
P('== C88 max monthly excess over national (2025-01..2026-07): top6', {k:(round(v,1),str(ex.loc[k].idxmax())) for k,v in mx.head(6).items()})
z2=win(S,'2024-12-01','2026-07-31'); z2=z2[z2.county!='CC']; z2['m']=z2.res.dt.to_period('M')
ex2=z2.groupby(['county','m'],observed=True).W.median().unstack().sub(z2.groupby('m').W.median(),axis=1)
P('   same from 2024-12:', {k:(round(v,1),str(ex2.loc[k].idxmax())) for k,v in ex2.max(axis=1).sort_values(ascending=False).head(5).items()})

# ---------- C04/C09/C11 filing-month cohorts (decided only)
co=S[(S.app>='2026-01-01')]
cm2=co.groupby(co.app.dt.to_period('M')).W.agg(['size','median'])
P('== C04 BERC cohort medians (decided only)'); P(cm2.round(2).to_string())

# ---------- C78 publication lag, C81 after hours
for y in [2023,2024,2025,2026]:
    x=df[df.res.dt.year==y]; lag=(x.pub-x.res).dt.total_seconds()/86400
    P('== C78',y,'n',len(x),'p50',round(lag.median(),3),'p90',round(lag.quantile(.9),2),'p99',round(lag.quantile(.99),2))
for y in [2023,2024,2025,2026]:
    x=df[df.res.dt.year==y]; h=x.res.dt.hour+x.res.dt.minute/60
    wdm=np.isin(x.res.values.astype('datetime64[D]'),HOL_NP)|(x.res.dt.weekday>=5).values
    P('== C81',y,'after 16:00',round((h>=16).mean()*100,1),'after 16:30',round((h>=16.5).mean()*100,1),'after 17',round((h>=17).mean()*100,1),'before 8',round((h<8).mean()*100,1),' non-working-day decisions',int(wdm.sum()))

# ---------- C36 online (outside office hours) vs inside, same filing day & county
o=S[(S.app>='2026-05-01')&(S.app<'2026-09-01')&S.cat.isin(['CERERE265','INMATRIC265'])].copy()
hh=o.app.dt.hour+o.app.dt.minute/60
o['out']=(hh<8)|(hh>=16.5)|(o.app.dt.weekday>=5)
o['d']=o.app.dt.normalize()
o['Wd']=(o.res.dt.normalize()-o.d).dt.days
g=o.groupby(['d','county','out'],observed=True).W.median().unstack()
g=g.dropna()
w=o[~o.out].groupby(['d','county'],observed=True).size().reindex(g.index)
diff=(g[True]-g[False])
P('== C36 out-of-hours minus in-hours median W, same day&county (May-Aug 2026 filings): mean',round(diff.mean(),2),' weighted',round(np.average(diff,weights=w),2),' median',round(diff.median(),2),' strata',len(g))
for (a,b) in [('2026-05-01','2026-08-01'),('2026-08-01','2026-09-01')]:
    q=o[(o.app>=a)&(o.app<b)]; gg=q.groupby(['d','county','out'],observed=True).W.median().unstack().dropna()
    P('   window',a,b,'mean diff',round((gg[True]-gg[False]).mean(),2))

# ---------- press: inmatriculari admis, mentiuni admis
IA=df[(df.cat=='INMATRIC265')&(df.sol=='Admis')]; MA=df[(df.cat=='CERERE265')&(df.sol=='Admis')]
def cnt(x,a,b): return len(win(x,a,b))
P('== C92/P12 INMATRIC Admis Jan-Sep 2026',cnt(IA,'2026-01-01','2026-09-30'),' 2025',cnt(IA,'2025-01-01','2025-09-30'),' chg',round((cnt(IA,'2026-01-01','2026-09-30')/cnt(IA,'2025-01-01','2025-09-30')-1)*100,1))
a26=cnt(IA,'2026-08-01','2026-10-31'); a25=cnt(IA,'2025-08-01','2025-10-31')
P('== P13 INMATRIC Admis Aug-Oct 2026 vs 2025',a26,a25,round((a26/a25-1)*100,1))
for mth in ['09','10']:
    i26=cnt(IA,f'2026-{mth}-01',f'2026-{mth}-{30 if mth=="09" else 31}'); i25=cnt(IA,f'2025-{mth}-01',f'2025-{mth}-{30 if mth=="09" else 31}')
    m26=cnt(MA,f'2026-{mth}-01',f'2026-{mth}-{30 if mth=="09" else 31}'); m25=cnt(MA,f'2025-{mth}-01',f'2025-{mth}-{30 if mth=="09" else 31}')
    P('== P14/P15 month',mth,'inmatric',i26,i25,round((i26/i25-1)*100,1),' mentiuni admis',m26,m25,round((m26/m25-1)*100,1))
i24=cnt(IA,'2024-04-01','2024-12-31'); i23=cnt(IA,'2023-04-01','2023-12-31')
P('== P17 INMATRIC Admis Apr-Dec 2024 vs 2023',i24,i23,round((i24/i23-1)*100,1))
P('== P16 2024 summer: strict finals/wd Jun 2024',round(len(win(SB,'2024-06-01','2024-06-30'))/wd_count('2024-06-01','2024-06-30')),' Aug 2024',round(len(win(SB,'2024-08-01','2024-08-31'))/wd_count('2024-08-01','2024-08-31')))
for cty in ['CJ','MH','IS']:
    P('== P04/P19 county',cty,'median 1-18 Nov',round(win(S[S.county==cty],'2026-11-01','2026-11-18').W.median(),1))
out.close()
