import local__config as local
import database as db
import my_logging as mylog
import functions as fn

from datetime import datetime, timedelta
import pandas as pd
from binance.client import Client

default_start_str = '2022-08-01 00:00:00 UTC-3'

def update(symbol):
    try:
        # Obteniendo la fecha y hora de ultima vela registrada en horario UTC
        query = "SELECT * FROM klines_1m WHERE symbol = '" +symbol+"' ORDER BY datetime DESC LIMIT 1"

        last = pd.read_sql(sql=query,con=db.engine)
        if last['datetime'].count()== 1:
            last['datetime'] = pd.to_datetime(last['datetime'], unit='ms') + pd.Timedelta('1 min') + pd.Timedelta('3 hr')
            start_str = last['datetime'].iloc[0].strftime('%Y-%m-%d %X')
        else:
            start_str = default_start_str

        #Conectando a Binance sin API-KEY 
        client = Client()

        try:
            klines = client.get_historical_klines(
                #se buscan velas hasta un minuto antes del minuto actual para que se registre la vela cerrada en la base de datos
                symbol=symbol, interval='1m', start_str=start_str,end_str='1 minute ago')
        except Exception as e:
            mylog.criticalError(f'kline.py - update {e}')

        if klines:
            df = pd.DataFrame(klines)
            df = df.iloc[:, :6]
            df.columns = ["datetime", "open", "high", "low", "close", "volume"]
            df['open'] = df['open'].astype('float')
            df['high'] = df['high'].astype('float')
            df['low'] = df['low'].astype('float')
            df['close'] = df['close'].astype('float')
            df['volume'] = df['volume'].astype('float')
            df['datetime'] = pd.to_datetime(
                df['datetime'], unit='ms') - pd.Timedelta('3 hr')
            df['symbol'] = symbol
        
            df.to_sql('klines_1m', con=db.engine, index=False,
                    if_exists='append', chunksize=1000)
        return True
        
    except Exception as e:
        msg = f'kline.py :: update - No fue posible actualizar velas para {+symbol} {e}'
        mylog.error(msg)
        

# idinterval: Definido en functions.py.get_intervals()
def get(symbol,idinterval,limit):
    interval_str = fn.get_intervals(idinterval,'pandas_resample')
    i_unit = idinterval[0:2]
    i_qty = int(idinterval[2:])
    if i_unit == '0m': #Minutos
        delta_time = timedelta(minutes = i_qty*limit)
    elif i_unit == '1h': #Horas
        delta_time = timedelta(hours = i_qty*limit)
    elif i_unit == '2d': #Dias
        delta_time = timedelta(days = i_qty*limit)
    from_datetime = (datetime.utcnow() - delta_time - timedelta(hours = 3) ).strftime('%Y-%m-%d %H:%M')
        
    query = None
    query = "SELECT * FROM klines_1m WHERE symbol = '" +symbol+"' AND datetime >= '"+from_datetime+"' ORDER BY datetime DESC"
    klines = pd.read_sql(sql=query,con=db.engine)
    klines.sort_values(by="datetime",inplace=True)

    agg_funcs = {
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last",
        "volume": "sum",
    }   
    
    if interval_str:
        return klines.resample(interval_str, on="datetime").agg(agg_funcs)

   
    
    