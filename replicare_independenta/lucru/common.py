"""Shared helpers: slim BERC load, RO legal calendar."""
import pandas as pd, numpy as np, datetime as dt, os
HERE=os.path.dirname(os.path.abspath(__file__))
SLIM=os.path.join(HERE,'berc_slim.pkl')

def orthodox_easter(y):
    a=y%4; b=y%7; c=y%19; d=(19*c+15)%30; e=(2*a+4*b-d+34)%7
    month=(d+e+114)//31; day=((d+e+114)%31)+1
    jul=dt.date(y,month,day)
    return jul+dt.timedelta(days=13)  # Julian->Gregorian (1900-2099)

def ro_holidays(y):
    E=orthodox_easter(y); td=dt.timedelta
    h={dt.date(y,1,1),dt.date(y,1,2),dt.date(y,1,24),E-td(2),E,E+td(1),
       dt.date(y,5,1),dt.date(y,6,1),E+td(49),E+td(50),dt.date(y,8,15),
       dt.date(y,11,30),dt.date(y,12,1),dt.date(y,12,25),dt.date(y,12,26)}
    if y>=2024: h|={dt.date(y,1,6),dt.date(y,1,7)}
    return h

HOL=set()
for y in range(2022,2029): HOL|=ro_holidays(y)
HOL_NP=np.array(sorted(HOL),dtype='datetime64[D]')

def is_wd(d):
    d=pd.to_datetime(d); return (d.weekday()<5) and (d.date() not in HOL)

def wd_count(start,end):
    """legal working days in [start,end] inclusive (dates)"""
    return int(np.busday_count(np.datetime64(pd.Timestamp(start).date()),np.datetime64(pd.Timestamp(end).date())+np.timedelta64(1,'D'),holidays=HOL_NP))

def busdays_between(a,b):
    """vectorized: number of legal working days strictly after date(a) up to and including date(b)"""
    a=np.asarray(a,dtype='datetime64[D]'); b=np.asarray(b,dtype='datetime64[D]')
    return np.busday_count(a+np.timedelta64(1,'D'),b+np.timedelta64(1,'D'),holidays=HOL_NP)

def load():
    if not os.path.exists(SLIM):
        df=pd.read_pickle(os.path.join(HERE,'..','date','berc_decizii.pkl'))
        df=df.drop(columns=['office','code4'])
        df['app_nr']=df['app_nr'].astype('int32')
        df.to_pickle(SLIM)
    return pd.read_pickle(SLIM)

FIN_STRICT=['Admis','Respins','Renunțat']
def add_basic(df):
    df['W']=(df['res']-df['app']).dt.total_seconds()/86400
    df['strict']=df['sol'].isin(FIN_STRICT)
    df['cert']=df['sol'].astype(str).str.startswith('Certificare')
    df['amanat']=df['cat'].eq('AUTO_AMANARI')
    df['rday']=df['res'].dt.normalize()
    return df
