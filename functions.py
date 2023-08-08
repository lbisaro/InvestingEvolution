import math
from datetime import datetime
import my_logging as mylog
import pandas as pd


#step_size debe ser un numero decimal expresado en potencia de 10, como por ejemplo: 0.0001, 0.01, 10.0, 1000.0
def calcular_decimales(step_size):
    potencia = int(math.log10(step_size))
    decimales = ( 0 if potencia>0 else -potencia )
    return decimales

def precio_actual(client,symbol):
    #Diferentes formas de obener el precio de un SIMBOLO

    # - Esta es la forma propuesta tomando el precio promedio ofrecido por binance
    #Resuelve mas rapido la consulta a Binance y ocupa menos recursos
    result = client.get_avg_price(symbol=symbol)
    avg_price = float(result['price'])
    #print('get_avg_price         - Precio Promedio ',avg_price)

    # - Esta es la forma que toma el bid y ask propuesto por binance
    #tickers = client.get_orderbook_tickers()
    #res = [data for data in tickers if symbol in data['symbol']]
    #buy_price = float(res[0]['askPrice'])
    #sell_price = float(res[0]['bidPrice'])
    #avg_price  = (buy_price + sell_price) / 2
    ##print("get_orderbook_tickers - Precio Promedio ",avg_price,"Compra:",buy_price,"Venta:",sell_price)

    # - Esta es la forma calculando el bid y ask tomando la 5ta posicion en el order_book
    #tickers = client.get_order_book(symbol=symbol)
    #buy_price = float(tickers['asks'][5][0])
    #sell_price = float(tickers['bids'][5][0])
    #avg_price = (buy_price + sell_price) / 2 
    ##print("get_orderbook_tickers - Precio Promedio ",avg_price,"Compra:",buy_price,"Venta:",sell_price)

    # - POR DESARROLLAR - Hay otra forma mas exacta usando el order_book
    #   y calculando la cantidad de unidades del bid y ask, en comparacion
    #   con la cantidad de unidades aproximadas a comprar
    #   Es posible que sea mas lenta y ocume mas recursos   

    return avg_price

def get_symbol_info(client,symbol):
    symbol_info = client.get_symbol_info(symbol)
    qty_dec_qty   = calcular_decimales(float(symbol_info['filters'][1]['minQty']))
    qty_dec_price = calcular_decimales(float(symbol_info['filters'][0]['minPrice']))
    symbol_info['qty_dec_price'] = qty_dec_price
    symbol_info['qty_dec_qty'] = qty_dec_qty
    return symbol_info

def get_intervals(i='ALL',c='ALL'):
    columns=['id','name','binance','pandas_resample','minutes']
    intervals = pd.DataFrame([['0m01','1 minuto','1m','1T',1],
                             ['0m05','5 minutos','5m','5T',5],
                             ['0m15','15 minutos','15m','15T',15],
                             ['0m30','30 minutos','30m','30T',30],
                             ['1h01','1 hora','1h','1H',60],
                             ['1h04','4 horas','4h','4H',(60*4)],
                             ['2d01','1 dia','1d','1D',(60*4*24)],
                             ],columns=columns)
    intervals.set_index('id',inplace=True)

    if i=='ALL' and c=='ALL':
        return intervals
    else:
        if i!='ALL' and c=='ALL':
            if i in intervals.index:
                return intervals.loc[i]
            else:
                mylog.criticalError('functions.py.get_intervals - El idinterval especificado es invalido')
        elif i!='ALL' and c!='ALL':
            if i in intervals.index:
                if c in intervals.loc[i]:
                    return intervals.loc[i][c]
                else:
                    mylog.criticalError('functions.py.get_intervals - El dato especificado es invalido')
            else:
                mylog.criticalError('functions.py.get_intervals - El idinterval especificado es invalido')
    
    

def get_interval_actual():
    
    hr = datetime.now().strftime('%H')
    mn = datetime.now().strftime('%M')

    whereIn = "'0m01'"
    if mn[1]=='0' or mn[1]=='5':
        whereIn = whereIn + ",'0m05'"
    if mn=='00' or mn=='15' or mn=='30' or mn=='45':
        whereIn = whereIn + ",'0m15'"
    if mn=='00' or mn=='30':
        whereIn = whereIn + ",'0m30'"
    if mn=='00' :
        whereIn = whereIn + ",'1h01'"
    if mn=='00' and (hr=='00' or hr=='04' or hr=='08' or hr=='12' or hr=='16' or hr=='20'):
        whereIn = whereIn + ",'1h04'"
    if mn=='00' and (hr=='21'):
        whereIn = whereIn + ",'2d01'"

    return whereIn

def create_order(client,symbol,side,type,quantity):
    try:
        order = client.create_order(
                    symbol=symbol,
                    side=side,
                    type=type,
                    quantity= quantity
                    )
        return order
    except Exception as e:
        msg_text = f'{e} '+ symbol+" "+side+" "+quantity
        mylog.error(msg_text)
        return False