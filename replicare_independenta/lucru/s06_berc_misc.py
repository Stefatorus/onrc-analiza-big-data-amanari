"""BERC batch 3: definitional variants (C101, C102, C88, C18), C34, C70 backtest, C71 seasonality, C76, truncation."""
from common import *
from scipy import stats
out=open('res_berc_misc.txt','w',encoding='utf-8')
def P(*a):
    s=' '.join(str(x) for x in a); print(s); out.write(s+'\n')
df=add_basic(load())
df=df[df.res>='2023-04-01'].copy()
ok=(df.W>=0)&(df.W<400)
S=df[df.strict & ok]; SB=df[df.strict]; AM=df[df.amanat]; BR=df[df.strict|df.cert]
def win(sub,a,b,col='res'):
    return sub[(sub[col]>=a)&(sub[col]<pd.Timestamp(b)+pd.Timedelta(days=1))]
def bdays(x):
    return busdays_between(x.app.values.astype('datetime64[D]'),x.res.values.astype('datetime64[D]'))
# C101 variants
for lab,sub in [('strict',S),('amanari',AM[(AM.W>=0)&(AM.W<400)]),('inmatric',S[S.cat=='INMATRIC265']),('all decisions',df[ok])]:
    for a,b in [('2026-04-27','2026-06-30'),('2026-04-27','2026-05-31'),('2026-04-27','2026-07-31')]:
        x=win(sub,a,b); bd=bdays(x)
        P('== C101',lab,a,b,'==3wd',round((bd==3).mean()*100,1),' among <=3wd share ==3', round(((bd==3).sum()/(bd<=3).sum())*100,1))
# by filing date
for lab,sub in [('strict',S),('amanari',AM[(AM.W>=0)&(AM.W<400)])]:
    x=win(sub,'2026-04-27','2026-06-30',col='app'); bd=bdays(x); P('   by filing date 27.04-30.06',lab,round((bd==3).mean()*100,1))
# C102 variants
f=win(S,'2026-11-02','2026-11-19')
for cat in ['CERERE265','INMATRIC265']:
    g=f[f.cat==cat]; fa=g[g.W<=14]; sl=g[g.W>14]
    P('== C102',cat,'rej fast',round((fa.sol=='Respins').mean()*100,1),'rej slow',round((sl.sol=='Respins').mean()*100,1),'F fast',round((fa.jtype=='F').mean()*100,1),'F slow',round((sl.jtype=='F').mean()*100,1),'F all',round((g.jtype=='F').mean()*100,1))
    smp=g.sample(min(len(g),150000),random_state=1)
    P('   tau app vs res',round(stats.kendalltau(smp.app.values.astype('int64'),smp.res.values.astype('int64')).statistic,3),' tau app_nr vs res',round(stats.kendalltau(smp.app_nr.values,smp.res.values.astype('int64')).statistic,3))
P('   jtype values in fast lane', f[f.W<=14].jtype.value_counts(normalize=True,dropna=False).round(3).to_dict())
P('   jtype values all', f.jtype.value_counts(normalize=True,dropna=False).round(3).to_dict())
# C88 variants: ratio and z
z=win(S,'2025-01-01','2026-07-31'); z=z[z.county!='CC']; z['m']=z.res.dt.to_period('M')
nat=z.groupby('m').W.median(); om=z.groupby(['county','m'],observed=True).W.median().unstack()
ratio=om.div(nat,axis=1); P('== C88 ratio max', {k:(round(v,2),str(ratio.loc[k].idxmax())) for k,v in ratio.max(axis=1).sort_values(ascending=False).head(6).items()})
lr=np.log(ratio); zz=(lr.sub(lr.mean(axis=0),axis=1)).div(lr.std(axis=0),axis=1)
P('   z(log ratio) max', {k:(round(v,2),str(zz.loc[k].idxmax())) for k,v in zz.max(axis=1).sort_values(ascending=False).head(6).items()})
dz=om.sub(nat,axis=1); sd=dz.std(axis=0)
z2=dz.div(sd,axis=1); P('   z(diff) max', {k:(round(v,2),str(z2.loc[k].idxmax())) for k,v in z2.max(axis=1).sort_values(ascending=False).head(6).items()})
mad=(om.sub(om.median(axis=0),axis=1)).abs().median(axis=0)
z3=om.sub(om.median(axis=0),axis=1).div(1.4826*mad,axis=1)
P('   robust z max', {k:(round(v,2),str(z3.loc[k].idxmax())) for k,v in z3.max(axis=1).sort_values(ascending=False).head(6).items()})
# C18 throughput variants
for a,b in [('2024-07-29','2024-11-30'),('2024-07-18','2024-11-30'),('2024-07-26','2024-11-30')]:
    x=win(S,a,b); P('== C18',a,b,'N timing',len(x),'days with dec',x.rday.nunique(),'per day',round(len(x)/x.rday.nunique()),'median',round(x.W.median(),2))
x=win(S,'2025-01-01','2025-12-31'); P('== C19 N timing/days with dec', len(x), x.rday.nunique(), round(len(x)/x.rday.nunique()))
# C34: week between MJ notes
for a,b in [('2026-10-31','2026-11-06'),('2026-10-30','2026-11-05'),('2026-11-02','2026-11-06')]:
    D_f=len(win(SB,a,b)); D_all=len(win(df,a,b))
    P('== C34',a,b,'strict',D_f,'all decisions',D_all,' stage1 out/stage2 out (strict)',round((D_f+4396)/D_f,3),' (all)',round((D_all+4396)/D_all,3))
# C70 backtest
dd=SB.groupby('rday').size(); ddb=BR.groupby('rday').size()
origins=pd.to_datetime(['2026-03-01','2026-03-29','2026-04-26','2026-05-24','2026-06-21','2026-07-19','2026-08-16','2026-09-13','2026-10-11'])
rows=[]
for o in origins:
    for lab,ser in [('strict',dd),('broad',ddb)]:
        prev=ser[ser.index<o]
        prev=prev[[is_wd(d) for d in prev.index]].tail(12).mean()
        a=o+pd.Timedelta(days=1); b=o+pd.Timedelta(days=26)
        obs=ser[(ser.index>=a)&(ser.index<=b)].sum()/wd_count(a,b)
        rows.append((o.date(),lab,round(prev,1),round(obs,1),round((obs/prev-1)*100,2),round(abs(obs-prev)/obs*100,2), wd_count(a,b)))
bt=pd.DataFrame(rows,columns=['origin','def','pred12','obs','dev_vs_pred%','abs_err_vs_obs%','wd'])
P('== C70 backtest'); P(bt.to_string())
for lab in ['strict','broad']:
    q=bt[bt['def']==lab]; P('   ',lab,'MAE%',round(q['abs_err_vs_obs%'].mean(),2),' obs>=pred',int((q['dev_vs_pred%']>=0).sum()),'/9')
# C71 seasonality: filings (distinct dossiers seen in BERC, CERERE+INMATRIC, strict finals+amanari) per wd by filing month, relative to Nov
E=df[df.cat.isin(['CERERE265','INMATRIC265'])&(df.app>='2024-08-01')].drop_duplicates(['app_nr','app'])
for y in [2025]:
    m=E[E.app.dt.year==y].groupby(E.app.dt.month).size()
    wdm=pd.Series({k:wd_count(f'{y}-{k:02d}-01',(pd.Timestamp(f'{y}-{k:02d}-01')+pd.offsets.MonthEnd(0))) for k in m.index})
    r=(m/wdm); P('== C71 filings per wd by month',y,'relative to Nov:', (r/r.loc[11]).round(3).to_dict())
Eo=df[df.cat.isin(['CERERE265','INMATRIC265'])&(df.app>='2023-04-01')&(df.app<'2024-07-01')].drop_duplicates(['county','app_nr','app'])
m=Eo[Eo.app.dt.year==2023].groupby(Eo.app.dt.month).size()
wdm=pd.Series({k:wd_count(f'2023-{k:02d}-01',(pd.Timestamp(f'2023-{k:02d}-01')+pd.offsets.MonthEnd(0))) for k in m.index})
r=m/wdm; P('   2023 rel Nov', (r/r.loc[11]).round(3).to_dict())
m=Eo[Eo.app.dt.year==2024].groupby(Eo.app.dt.month).size()
wdm=pd.Series({k:wd_count(f'2024-{k:02d}-01',(pd.Timestamp(f'2024-{k:02d}-01')+pd.offsets.MonthEnd(0))) for k in m.index})
P('   2024 H1 per wd', (m/wdm).round(0).to_dict())
# C76 Little: lambda * W
lam=len(win(SB,'2026-10-01','2026-11-20'))/ (pd.Timestamp('2026-11-20')-pd.Timestamp('2026-10-01')).days
P('== C76 lambda finals per calendar day Oct1-Nov20',round(lam),' x median W Nov(50.0)=',round(lam*50.0),' x mean W Oct-Nov', round(lam*win(S,'2026-10-01','2026-11-20').W.mean()))
lam2=len(win(df,'2026-10-01','2026-11-20'))/50
P('   all decisions/cal day x 50 =',round(lam2*50.0))
# truncation of last days: daily strict finals CERERE
d=win(SB,'2026-11-09','2026-11-20').groupby('rday').size(); P('== truncation daily strict finals', d.to_dict())
x=win(S[S.cat=='CERERE265'],'2026-11-16','2026-11-20')
P('   C14 by day of decision', x.groupby('rday').W.median().round(2).to_dict())
out.close()
