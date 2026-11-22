"""Remaining checks: C88 mean excess, model capacity input, C48 windows, counter max per day, C05 ratio."""
from common import *
out=open('res_remaining.txt','w',encoding='utf-8')
def P(*a):
    s=' '.join(str(x) for x in a); print(s); out.write(s+'\n')
df=add_basic(load()); df=df[df.res>='2023-04-01'].copy()
ok=(df.W>=0)&(df.W<400); S=df[df.strict&ok]; SB=df[df.strict]
def win(sub,a,b,col='res'):
    return sub[(sub[col]>=a)&(sub[col]<pd.Timestamp(b)+pd.Timedelta(days=1))]
# C88 mean monthly excess Jan 2025-Jul 2026
z=win(S,'2025-01-01','2026-07-31'); z=z[z.county!='CC']; z['m']=z.res.dt.to_period('M')
ex=z.groupby(['county','m'],observed=True).W.median().unstack().sub(z.groupby('m').W.median(),axis=1)
r=pd.DataFrame({'mean':ex.mean(axis=1),'max':ex.max(axis=1),'peak':ex.idxmax(axis=1).astype(str),'months>5':(ex>5).sum(axis=1)}).sort_values('mean',ascending=False)
P('== C88 mean monthly excess over national median (days), top 6'); P(r.head(6).round(2).to_string())
P('   bottom 3'); P(r.tail(3).round(2).to_string())
# model capacity input: mean strict finals per wd, last 12 wd up to various dates
d=SB.groupby('rday').size()
for end in ['2026-11-18','2026-11-19','2026-11-20']:
    s=d[d.index<=end]; s=s[[is_wd(x) for x in s.index]].tail(12)
    P('== model input check: mean strict finals last 12 wd to',end,round(s.mean()),' (min',s.min(),')')
s=d[(d.index>='2026-11-02')&(d.index<='2026-11-19')]; P('   mean strict finals/wd 2-19 Nov', round(s.mean()))
# C48: BERC decisions incl amanari per wd for candidate windows
for a,b in [('2026-01-01','2026-06-30'),('2026-08-01','2026-10-31'),('2026-10-01','2026-10-31'),('2026-10-27','2026-11-06'),('2026-10-30','2026-11-06'),('2026-11-02','2026-11-06'),('2026-10-01','2026-11-06')]:
    x=win(df,a,b); P('== C48 window',a,b,'all decisions/wd',round(len(x)/wd_count(a,b)),' strict/wd',round(len(win(SB,a,b))/wd_count(a,b)),' strict+amanari/wd',round(len(x[x.strict|x.amanat])/wd_count(a,b)))
# P05 counter: max increments per day
b=df[df.app>='2026-01-01']; env=b.groupby(b.app.dt.normalize()).app_nr.min()
inc=env.diff().shift(-1)
P('== P05 counter max numbers/day 2026', int(inc.max()), str(inc.idxmax().date()), ' top3', inc.nlargest(3).astype(int).to_dict())
# C05 ratio
co=S[S.app>='2026-05-01']; m=co.groupby(co.app.dt.to_period('M')).W.median()
P('== C05 ratio Sep/May medians (decided only)', round(m.loc['2026-09']/m.loc['2026-05'],2), ' rounded 39/5 =',39/5, ' KM 57-58 / 5 =',57/5,58/5)
out.close()
