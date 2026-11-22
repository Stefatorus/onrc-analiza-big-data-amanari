"""C70: real-time vintage variant - forecast uses only decisions PUBLISHED before origin."""
from common import *
df=add_basic(load()); df=df[df.res>='2025-12-01']
x=df[df.strict]
origins=pd.to_datetime(['2026-03-01','2026-03-29','2026-04-26','2026-05-24','2026-06-21','2026-07-19','2026-08-16','2026-09-13','2026-10-11'])
tp=[4242.6,4133.8,3745.9,3906.9,3804.7,3617.5,3302.0,3338.8,3948.9]; to=[4361.1,4174.5,4140.7,4081.3,3740.8,3558.8,3487.9,4138.8,4131.5]
days=pd.date_range('2025-12-01','2026-11-20'); wdm=pd.Series([is_wd(d) for d in days],index=days)
rows=[]
for o,a1,b1 in zip(origins,tp,to):
    for cut in [o, o+pd.Timedelta(hours=-24*0)]:
        v=x[x.pub<o]
        ser=v.groupby('rday').size().reindex(days,fill_value=0)
        prev=ser[:o-pd.Timedelta(days=1)]; p=prev[wdm[prev.index]].tail(12).mean()
    ser_all=x.groupby('rday').size().reindex(days,fill_value=0)
    a=o+pd.Timedelta(days=1); b=o+pd.Timedelta(days=26)
    obs=ser_all[a:b].sum()/wd_count(a,b)
    rows.append((o.date(),round(p,1),a1,round(obs,1),b1,round((obs/p-1)*100,2),round(abs(obs-p)/obs*100,2)))
r=pd.DataFrame(rows,columns=['origin','pred_realtime','report_pred','obs','report_obs','dev_vs_pred%','abserr_vs_obs%'])
print(r.to_string()); print('MAE',round(r['abserr_vs_obs%'].mean(),2),'obs>=pred',(r['dev_vs_pred%']>=0).sum())
