import local__config as local
import functions as fn
import database as db
import kline 
import local__signals as signals

import pandas as pd
from datetime import datetime, timedelta
import telebot
from binance.client import Client
import logging

# Configura el logging
logging.basicConfig(filename='bot.log', filemode='a', format='%(name)s - %(levelname)s - %(message)s')
logging.warn("Inicio", exc_info=False)

#Conectar con Telegram
chatid=local.LOC_TLGRM_CHATID
tb = telebot.TeleBot(local.LOC_TLGRM_TK)


#tb.send_message(chatid, "Mensaje ✅ uno 🔻 dos ")



#Conectar Binance
client = Client(local.LOC_BNC_AK, local.LOC_BNC_SK, testnet=local.LOC_BNC_TESNET)

SYMBOL = 'BTCUSDT'
KLINE_INTERVAL = '1h'  #Interval:  1m 5m 15m 30m 1h 4h 1d
VELAS_PREVIAS = 50
LONG_MEDIA_VALUE = 14

if kline.update(SYMBOL):

    klines = kline.get(SYMBOL,KLINE_INTERVAL,VELAS_PREVIAS)
    
    signal = signals.adx_alternancia(klines,LONG_MEDIA_VALUE)

    
    symbol_info = fn.getSymbolInfo(client,SYMBOL)
    avg_price = fn.precioActual(client,SYMBOL) 
    
    price = round(avg_price,symbol_info['qty_dec_price'])

    msg_text = SYMBOL+" "+KLINE_INTERVAL+"\n"+signal+"\n"+str(price)
        
    if signal != 'NEUTRO':
        if signal == 'COMPRA':
            emoji = '✅'
        elif signal == 'VENTA':
            emoji = '🔻'
        msg_text = SYMBOL+" "+KLINE_INTERVAL+"\n"+emoji+" "+signal+"\n"+str(price)
        tb.send_message(chatid, msg_text)

    print(msg_text)
    #for i in klines[-10:].index:
    #    print(klines['datetime'].loc[i],klines['volume'].loc[i])


    """
    TO DO

    - Funcion para precio y cantidades a operar
    - Funciones de compra y venta
    - Registro de ordenes abiertas y completas
    - Calculo de comisiones
    - 
    - Reportes


    
    """

    


else:
    exit('ERROR - No fue posible actualizar las velas')