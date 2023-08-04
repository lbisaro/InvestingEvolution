import math

#step_size debe ser un numero decimal expresado en potencia de 10, como por ejemplo: 0.0001, 0.01, 10.0, 1000.0
def calcularDecimales(step_size):
    potencia = int(math.log10(step_size))
    decimales = ( 0 if potencia>0 else -potencia )
    return decimales

def precioActual(client,symbol):
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

def getSymbolInfo(client,symbol):
    symbol_info = client.get_symbol_info(symbol)
    qty_dec_qty   = calcularDecimales(float(symbol_info['filters'][1]['minQty']))
    qty_dec_price = calcularDecimales(float(symbol_info['filters'][0]['minPrice']))
    symbol_info['qty_dec_price'] = qty_dec_price
    symbol_info['qty_dec_qty'] = qty_dec_qty
    return symbol_info