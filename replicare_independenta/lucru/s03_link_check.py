from common import *
df=add_basic(load())
n=df[df.app>='2024-08-01']
f=n[n.strict]
k=f.groupby(['app_nr','app']).size()
print('strict finals post-Aug24 rows',len(f),'unique keys',len(k),'dup keys',(k>1).sum())
k2=f.groupby([f.app.dt.year,'app_nr']).size(); print('unique (year,app_nr)',len(k2),'dups',(k2>1).sum())
# same app_nr different app times?
g=n.groupby([n.app.dt.year,'app_nr'])['app'].nunique(); print('year,app_nr with >1 distinct app ts',(g>1).sum())
print(n[n.cat=='AUTO_AMANARI'].groupby(['app_nr','app']).size().value_counts().head())
# daily counts last days
d=df[df.res>='2026-11-02'].groupby(['rday','cat']).size().unstack(); print(d)
# pub lag in Nov
x=df[(df.res>='2026-10-01')]; lag=(x.pub-x.res).dt.total_seconds()/86400
print(lag.describe(percentiles=[.5,.9,.95,.99]))
# share of Oct decisions published >1, >2 days after
print('share lag>1d',(lag>1).mean(),'>2d',(lag>2).mean(), '>3d', (lag>3).mean())
