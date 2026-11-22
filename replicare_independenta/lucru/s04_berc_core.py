"""Core BERC replications. Output: res_berc_core.txt"""
from common import *
out=open('res_berc_core.txt','w',encoding='utf-8')
def P(*a):
    s=' '.join(str(x) for x in a); print(s); out.write(s+'\n')
df=add_basic(load())
df=df[df.res>='2023-04-01']
ok=(df.W>=0)&(df.W<400)
S=df[df.strict & ok]          # strict finals for timing
SB=df[df.strict]              # strict finals (counts)
BR=df[df.strict|df.cert]      # broad finals
AM=df[df.amanat]
def win(sub,a,b):
    return sub[(sub.res>=a)&(sub.res<pd.Timestamp(b)+pd.Timedelta(days=1))]
def per_wd(sub,a,b):
    n=len(win(sub,a,b)); return round(n/wd_count(a,b),1), n
def med(sub,a,b,col='W'):
    x=win(sub,a,b); return round(x[col].median(),2), len(x)
def bdays(x):
    return busdays_between(x.app.values.astype('datetime64[D]'),x.res.values.astype('datetime64[D]'))

P('== C01 broad finals/wd 1.10-20.11.2026', per_wd(BR,'2026-10-01','2026-11-20'), 'strict', per_wd(SB,'2026-10-01','2026-11-20'))
P('   excluding 20.11 (partial): broad/wd 1.10-19.11', per_wd(BR,'2026-10-01','2026-11-19'))
P('   peak Feb-Mar 2025 broad', per_wd(BR,'2025-02-01','2025-03-31'),'strict',per_wd(SB,'2025-02-01','2025-03-31'))
P('== C03 amanari/wd: 1.10-20.11.2026',per_wd(AM,'2026-10-01','2026-11-20'),' 2026 YTD',per_wd(AM,'2026-01-01','2026-11-20'))
a=per_wd(SB,'2026-08-01','2026-08-31')[0]; b=per_wd(SB,'2026-06-01','2026-07-31')[0]
P('== C07 Aug/JunJul strict per legal wd', a, b, round(a/b,3))
def per_dd(sub,a,b):
    x=win(sub,a,b); return len(x)/x['rday'].nunique()
P('   C07 per day-with-decisions', round(per_dd(SB,'2026-08-01','2026-08-31')/per_dd(SB,'2026-06-01','2026-07-31'),3))
for cat,lab in [('CERERE265','C14'),('INMATRIC265','C15')]:
    s=S[S.cat==cat]; P('==',lab,cat,'16-20 Nov median',med(s,'2026-11-16','2026-11-20'), ' 16-19 Nov',med(s,'2026-11-16','2026-11-19'))
P('== C84 all strict 1-20 Nov median',med(S,'2026-11-01','2026-11-20'), 'CERERE only', med(S[S.cat=='CERERE265'],'2026-11-01','2026-11-20'))
P('   P02 Oct median all strict',med(S,'2026-10-01','2026-10-31'))
S2=S[(S.res>='2026-09-28')]
wk=S2.res.dt.to_period('W-SUN')
t=S2.groupby([wk,'cat'],observed=True)['W'].median().unstack()[['CERERE265','INMATRIC265']]
t['N_all']=S2.groupby(wk).size()
P('== C16 weekly medians (by decision week Mon-Sun)'); P(t.round(2).to_string())
P('   monotone CERERE:',bool(t.CERERE265.is_monotonic_increasing),' INMATRIC:',bool(t.INMATRIC265.is_monotonic_increasing))
for lab,a,b in [('C17 old platform','2023-04-01','2024-07-17'),('C18 launch','2024-07-29','2024-11-30'),('C19 2025','2025-01-01','2025-12-31'),('2026 Jan-Jul','2026-01-01','2026-07-31')]:
    x=win(S,a,b); xs=win(SB,a,b)
    P('==',lab,'median W',round(x.W.median(),2),'N',len(x),'strict finals/day-with-decisions',round(len(xs)/xs.rday.nunique()),'per legal wd',round(len(xs)/wd_count(a,b)), 'p90',round(x.W.quantile(.9),1))
for lab,a,b in [('old','2023-04-01','2024-07-17'),('launch','2024-07-29','2024-11-30'),('2025','2025-01-01','2025-12-31'),('2026 to Jul','2026-01-01','2026-07-31'),('Aug-Nov26','2026-08-01','2026-11-20'),('2026 all','2026-01-01','2026-11-20')]:
    x=win(df,a,b)
    P('== C21 amanari share of all decisions',lab, round(x.amanat.mean()*100,2), ' of (strict+amanari)', round(x.amanat.sum()/(x.amanat.sum()+x.strict.sum())*100,2),' n',len(x))
for y in [2023,2024,2025,2026]:
    x=df[df.res.dt.year==y]; P('== C80/C82 year',y,'all decisions',len(x),'amanari',int(x.amanat.sum()), round(x.amanat.mean()*100,2))
for y in [2023,2024,2025,2026]:
    a=f'{y}-10-01'; b=f'{y}-11-20'
    P('== C30/C79/C87',y,'strict/wd',per_wd(SB,a,b)[0],'broad/wd',per_wd(BR,a,b)[0],'all decisions/wd',per_wd(df,a,b)[0],' wd',wd_count(a,b))
for y in [2024,2025,2026]:
    h=per_wd(df,f'{y}-01-01',f'{y}-06-30')[0]; s=per_wd(df,f'{y}-08-01',f'{y}-10-31')[0]
    hs=per_wd(SB,f'{y}-01-01',f'{y}-06-30')[0]; ss=per_wd(SB,f'{y}-08-01',f'{y}-10-31')[0]
    P('== C86',y,'all decisions/wd H1',h,'Aug-Oct',s,'chg',round((s/h-1)*100,1),'% | strict',hs,ss,round((ss/hs-1)*100,1))
for lab,a,b in [('old','2023-04-01','2024-07-17'),('old to Jul31','2023-04-01','2024-07-31'),('crisis','2026-08-01','2026-11-20')]:
    x=win(S,a,b); bd=bdays(x)
    P('== C31',lab,'<=1 wd',round((bd<=1).mean()*100,2),' same day(<=0wd)',round((bd<=0).mean()*100,2),' W<=24h',round((x.W<=1).mean()*100,2), ' W<=1.5d', round((x.W<=1.5).mean()*100,2))
for lab,a,b in [('1.03-26.04','2026-03-01','2026-04-26'),('27.04-31.07','2026-04-27','2026-07-31')]:
    x=win(S,a,b); bd=bdays(x)
    P('== C32',lab,'W<=2d',round((x.W<=2).mean()*100,2),' <=2 wd',round((bd<=2).mean()*100,2),' N',len(x))
    cs=x.groupby('county',observed=True).W.apply(lambda w:(w<=2).mean()).median(); P('   county-median share W<=2d',round(cs*100,2))
xa=win(S,'2026-03-01','2026-04-26'); xb=win(S,'2026-04-27','2026-07-31')
ca=xa.groupby('county',observed=True).W.apply(lambda w:(w<=2).mean()); cb=xb.groupby('county',observed=True).W.apply(lambda w:(w<=2).mean())
c=pd.concat([ca,cb],axis=1,keys=['before','after']).dropna(); c=c[c.index!='CC']
P('   counties with after<0.03:',int((c.after<0.03).sum()),'of',len(c),' after max',round(c.after.max(),3))
AMo=AM[(AM.W>=0)&(AM.W<400)]
for lab,sub in [('strict',S),('amanari',AMo),('inmatric',S[S.cat=='INMATRIC265']),('cerere',S[S.cat=='CERERE265'])]:
    for a,b in [('2026-03-01','2026-04-26'),('2026-04-27','2026-07-31')]:
        x=win(sub,a,b); bd=bdays(x)
        P('== C101',lab,a,b,'exactly 3rd wd',round((bd==3).mean()*100,1),' <3 wd',round((bd<3).mean()*100,1),' p5 hours',round(x.W.quantile(.05)*24,1))
out.close()
