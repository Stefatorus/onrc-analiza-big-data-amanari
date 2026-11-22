"""C93/C98/C99/C22: inflow of registration requests from the national counter + portal sample + BERC."""
from common import *
out=open('res_inflow.txt','w',encoding='utf-8')
def P(*a):
    s=' '.join(str(x) for x in a); print(s); out.write(s+'\n')
b=load(); b=b[b.app>='2026-01-01'].copy()
# ---- counter at start of each calendar day (min app_nr observed on that day; monotone check)
env=b.groupby(b.app.dt.normalize()).app_nr.agg(['min','max'])
env=env[env.index>='2026-01-01']
P('counter monotone (daily min):',bool(env['min'].is_monotonic_increasing))
# use the portal sample too (it has request_date for every detailed number)
pa=pd.read_pickle('portal_all_dedup.pkl'); pd_=pd.read_pickle('portal_dedup.pkl')
def C_at(day):
    day=pd.Timestamp(day)
    s=env[env.index>=day]['min']
    return s.iloc[0] if len(s) else np.nan
months=pd.period_range('2026-01','2026-11',freq='M')
cnt={}
for m in months:
    a=m.start_time; e=min(m.end_time.normalize()+pd.Timedelta(days=1),pd.Timestamp('2026-11-20'))
    cnt[str(m)]=(C_at(a), C_at(e) if e<pd.Timestamp('2026-11-20') else env['max'].max())
# ---- C93: counter numbers per wd Jan-Jul
c0=C_at('2026-01-01'); c1=C_at('2026-08-01')
P('== C93 counter numbers per wd Jan-Jul 2026:',round((c1-c0)/wd_count('2026-01-01','2026-07-31')),' per calendar day',round((c1-c0)/212))
# ---- BERC distinct dossiers (any category) by filing month = mature inflow measure
key=b.drop_duplicates(['app_nr','app'])
key=key[key.cat!='CERERE_HJ265']
P('== BERC distinct dossiers by filing month (CERERE265+INMATRIC265+AUTO_AMANARI, any decision), per wd')
bm={}
for m in months:
    a=m.start_time; e=min(m.end_time.normalize(),pd.Timestamp('2026-11-20'))
    n=((key.app>=a)&(key.app<e+pd.Timedelta(days=1))).sum(); bm[str(m)]=n
    P('  ',m,'n',n,'per wd',round(n/wd_count(a,e)),' counter nums',cnt[str(m)][1]-cnt[str(m)][0],' BERC/counter',round(n/(cnt[str(m)][1]-cnt[str(m)][0]),3))
h1=sum(bm[f'2026-0{k}'] for k in range(1,7)); P('== C98 BERC H1 2026 distinct dossiers per wd:',round(h1/wd_count('2026-01-01','2026-06-30')))
# include HJ
keyall=b.drop_duplicates(['app_nr','app'])
h1b=((keyall.app>='2026-01-01')&(keyall.app<'2026-07-01')).sum(); P('   incl CERERE_HJ265:',round(h1b/wd_count('2026-01-01','2026-06-30')))
# ---- portal: share of counter numbers that are judged registration requests, by counter month
pa['month']=None
for m in months:
    lo,hi=cnt[str(m)]
    pa.loc[(pa.req_nr>=lo)&(pa.req_nr<hi),'month']=str(m)
pa['judged']=(pa.details_found==True)&(pa.is_judged==1)
pa['judged_x017']=pa.judged & (pa.type_code!='017')
# BERC presence of sampled numbers (exact number in 2026 BERC)
inB=set(b.app_nr.unique())
pa['inBERC']=pa.req_nr.isin(inB)
g=pa.groupby('month').agg(n=('req_nr','size'),det=('details_found','mean'),judged=('judged','mean'),inBERC=('inBERC','mean'))
g['inBERC_nodetail']=pa[pa.details_found!=True].groupby('month').inBERC.mean()
g['inBERC_judged']=pa[pa.judged].groupby('month').inBERC.mean()
g['inBERC_017']=pa[pa.type_code=='017'].groupby('month').inBERC.mean()
P('== portal sample by counter month'); P(g.round(3).to_string())
# ---- inflow estimate = counter numbers x share judged / wd
P('== C99 inflow estimate (counter x portal judged share) per wd vs BERC distinct dossiers per wd')
est={}
for m in g.index:
    a=pd.Period(m).start_time; e=min(pd.Period(m).end_time.normalize(),pd.Timestamp('2026-11-20'))
    if m=='2026-11': e=pd.Timestamp('2026-11-19')
    wd=wd_count(a,e); nc=cnt[m][1]-cnt[m][0]
    sh=g.loc[m,'judged']; n=g.loc[m,'n']; se=np.sqrt(sh*(1-sh)/n)
    est[m]=(nc*sh/wd, nc*(sh-1.96*se)/wd, nc*(sh+1.96*se)/wd, wd)
    P('  ',m,'n_sample',int(n),'share',round(sh,3),'est/wd',round(nc*sh/wd),'95%',round(nc*(sh-1.96*se)/wd),'-',round(nc*(sh+1.96*se)/wd),' BERC/wd',round(bm[m]/wd), ' wd',wd)
ao=['2026-08','2026-09','2026-10']
w=sum(est[m][3] for m in ao); P('   Aug-Oct est per wd', round(sum(est[m][0]*est[m][3] for m in ao)/w))
# ---- C22: portal weekly filings (detailed numbers) peak Sept vs summer
pdj=pd_[pd_.is_judged==1].copy(); pdj['wk']=pdj.rd.dt.to_period('W-SUN')
# sampled numbers are not uniform in counter-space across files -> weight by counter density
wkc=pdj.groupby('wk').size()
P('== C22 portal judged requests per week (raw sample counts):'); P(wkc.loc['2026-06':'2026-10'].to_string())
# counter increments per week (all numbers) from BERC envelope
envd=env['min']
wk_counter=envd.groupby(envd.index.to_period('W-SUN')).min().diff().shift(-1)
P('== counter numbers per week (all types):'); P(wk_counter.loc['2026-06':'2026-10'].to_string())
out.close()
