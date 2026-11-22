from common import *
df=load(); print(df.memory_usage(deep=True).sum()/1e6)
df=add_basic(df)
# Table 1 reproduction
print('W<0', (df.W<0).sum(), 'W>400', (df.W>400).sum(), 'W>=400',(df.W>=400).sum(), 'strict', df.strict.sum(), 'amanat sol', (df.sol=='Amânat').sum(), 'before 2023-04-01', (df.res<'2023-04-01').sum())
# monthly legal wd vs days with decisions
months=pd.period_range('2023-04','2026-11',freq='M')
dd=df[df.res>='2023-04-01'].groupby('rday').size()
out=[]
for m in months:
    s=m.start_time; e=min(m.end_time.normalize(), pd.Timestamp('2026-11-20'))
    out.append((str(m), wd_count(s,e), int(((dd.index>=s)&(dd.index<=e)).sum())))
print(out)
# weekdays non-holiday with few decisions, and holidays with many
days=pd.date_range('2023-04-01','2026-11-20')
cnt=dd.reindex(days,fill_value=0)
wdmask=np.array([is_wd(d) for d in days])
print('legal wd with <300 decisions:'); print(cnt[wdmask & (cnt<300)].to_string())
print('non-wd with >300 decisions:'); print(cnt[(~wdmask) & (cnt>300)].to_string())
# midnight app share by year
df['mid']=(df.app==df.app.dt.normalize())
print(df.groupby(df.app.dt.to_period('Q'))['mid'].mean().loc['2023Q1':].round(3).to_string())
