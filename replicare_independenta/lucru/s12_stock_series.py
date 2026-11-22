"""Weekly stock series from portal sample (for C99/C100 trend claims)."""
import runpy, io, contextlib
buf=io.StringIO()
with contextlib.redirect_stdout(buf):
    g=runpy.run_path('s11_portal_stock.py')
J=g['J']; pd=g['pd']
f=open('res_stock_series.txt','w',encoding='utf-8')
for t in pd.date_range('2026-09-01','2026-11-21',freq='7D'):
    x=J[J.rd<t]; pt=(x.fin_res>=t)|(x.fin_res.isna()&(x.stage!='rezolvat')); ni=x.type_desc!='Înmatriculare'
    s=f"{t.date()} all {round((x.w*pt).sum())} no-inmatric {round((x.w*(pt&ni)).sum())}"
    print(s); f.write(s+'\n')
