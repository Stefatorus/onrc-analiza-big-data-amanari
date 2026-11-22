import pandas as pd, numpy as np
df = pd.read_pickle('../date/berc_decizii.pkl')
for c in ['sol','jtype','office','county']:
    print('---',c); print(df[c].value_counts(dropna=False).head(60).to_string())
print(pd.crosstab(df['cat'],df['sol']).to_string())
print(df['code4'].nunique(), df['code4'].isna().mean()); print(df['code4'].dropna().head(10).tolist())
print(pd.crosstab(df['cat'], df['code4'].isna()))
for c in ['app','res','pub']:
    print(c, df[c].min(), df[c].max(), df[c].isna().sum())
print('app_nr na', df.app_nr.isna().sum(), df.app_nr.min(), df.app_nr.max())
print((df.app.dt.hour!=0).mean())
print(df.groupby(df.res.dt.to_period('M')).size().to_string())
