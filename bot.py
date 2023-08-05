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
logging.basicConfig(filename='bot.log', filemode='a', format='%(asctime)s %(name)s - %(levelname)s - %(message)s',datefmt='%Y-%m-%d %H:%M:%S')
#logging.warning("Inicio", exc_info=False)

#Conectar con Telegram
chatid=local.LOC_TLGRM_CHATID
tb = telebot.TeleBot(local.LOC_TLGRM_TK)

#tb.send_message(chatid, "Mensaje ✅ uno 🔻 dos ")
#tb.send_message(chatid, '*Bold* _Italic_ __Underline__', parse_mode="MarkdownV2")
#exit()


class Bot:
    def __init__(self, SYMBOL,KLINE_INTERVAL,VELAS_PREVIAS,LONG_MEDIA_VALUE):
        self.SYMBOL = SYMBOL
        self.KLINE_INTERVAL = KLINE_INTERVAL 
        self.VELAS_PREVIAS = VELAS_PREVIAS        
        self.LONG_MEDIA_VALUE = LONG_MEDIA_VALUE

    #Conectar Binance
    client = Client(local.LOC_BNC_AK, local.LOC_BNC_SK, testnet=local.LOC_BNC_TESNET)
    logging.warning("Inicio", exc_info=False)



 


    def start(self):
        logging.warning("Start", exc_info=False)
        if kline.update(self.SYMBOL):

            klines = kline.get(self.SYMBOL,self.KLINE_INTERVAL,self.VELAS_PREVIAS)
            
            signal = signals.adx_alternancia(klines,self.LONG_MEDIA_VALUE)

            
            symbol_info = fn.getSymbolInfo(self.client,self.SYMBOL)
            avg_price = fn.precioActual(self.client,self.SYMBOL) 
            
            price = round(avg_price,symbol_info['qty_dec_price'])

            msg_text = self.SYMBOL+" "+self.KLINE_INTERVAL+"\n"+signal+"\n"+str(price)
            
            emoji = '  '
            if signal != 'NEUTRO':
                if signal == 'COMPRA':
                    emoji = '✅'
                elif signal == 'VENTA':
                    emoji = '🔻'
                    
                msg_text = self.SYMBOL+" "+self.KLINE_INTERVAL+"\n"+signal+" "+emoji+"\n"+str(price)
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