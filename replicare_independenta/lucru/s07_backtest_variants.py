"""C70: try several definitions of 'last 12 days' forecast and observed rate to see which reproduces Table 24."""
from common import *
df=add_basic(load()); df=df[df.res>='2025-12-01']
ok=(df.W>=0)&(df.W<400)
sets={'strict':df[df.strict],'strict_ok':df[df.strict&ok],'broad':df[df.strict|df.cert],'all':df}
origins=pd.to_datetime(['2026-03-01','2026-03-29','2026-04-26','2026-05-24','2026-06-21','2026-07-19','2026-08-16','2026-09-13','2026-10-11'])
target_pred=[4242.6,4133.8,3745.9,3906.9,3804.7,3617.5,3302.0,3338.8,3948.9]
target_obs=[4361.1,4174.5,4140.7,4081.3,3740.8,3558.8,3487.9,4138.8,4131.5]
days=pd.date_range('2025-12-01','2026-11-20')
for name,x in sets.items():
    ser=x.groupby('rday').size().reindex(days,fill_value=0)
    wdm=pd.Series([is_wd(d) for d in days],index=days)
    res={}
    for o in origins:
        a=o+pd.Timedelta(days=1); b=o+pd.Timedelta(days=26)
        obs_wd=ser[a:b].sum()/wd_count(a,b)
        obs_dd=ser[a:b][ser[a:b]>0].mean()
        prev=ser[:o-pd.Timedelta(days=1)]
        p_wd12=prev[wdm[prev.index]].tail(12).mean()
        p_dd12=prev[prev>0].tail(12).mean()
        p_cal12=prev.tail(12).sum()/12
        p_cal12wd=prev.tail(12).sum()/max(1,wdm[prev.tail(12).index].sum())
        p_cal12x=prev.tail(12).mean()*7/5
        res[o.date()]=(obs_wd,obs_dd,p_wd12,p_dd12,p_cal12,p_cal12wd,p_cal12x)
    r=pd.DataFrame(res,index=['obs_wd','obs_dd','p_wd12','p_dd12','p_cal12','p_cal12wd','p_cal12x7/5']).T
    r['tp']=target_pred; r['to']=target_obs
    print('=====',name); print(r.round(1).to_string())
