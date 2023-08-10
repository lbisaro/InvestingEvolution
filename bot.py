import local__config as local
import functions as fn
import database as db
import kline
import local__signals as signals
from sqlalchemy import insert

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import telebot
from binance.client import Client
import my_logging as mylog


# Conectar con Telegram
chatid = local.LOC_TLGRM_CHATID
tb = telebot.TeleBot(local.LOC_TLGRM_TK)

#tb.send_message(chatid, "Mensaje ✅ uno 🔻 dos ")
#tb.send_message(chatid, '*Bold* _Italic_ __Underline__', parse_mode="MarkdownV2")
#exit()


class Bot:
    SIDE_BUY = 0
    SIDE_SELL = 1

    VALID_IDESTRATEGIA = 1

    # Conectar Binance
    client = Client(local.LOC_BNC_AK, local.LOC_BNC_SK,
                    testnet=local.LOC_BNC_TESNET)
    

    def run(self,idbot):

        #mylog.info("Inicio idbot:"+str(idbot))

        """Configura el bot en funcion del parametro idbot recibido"""
        query = "SELECT * FROM bot WHERE idbot = '"+str(idbot)+"' "
        bots = pd.read_sql(sql=query, con=db.engine)
        if bots['idbot'].count()== 1:
            if bots.iloc[0]['idbot'] != idbot:
                mylog.error("Bot::run(idbot="+idbot+") ID invalido")
                return False
            
            if np.int64(bots.iloc[0]['idestrategia']) != self.VALID_IDESTRATEGIA:
                mylog.error("Bot::run(idbot="+str(idbot)+") idestrategia erronea")
                return False
            idbot = idbot.item()
            self.idbot = idbot 
            self.SYMBOL = bots.iloc[0]['base_asset']+bots.iloc[0]['quote_asset']
            self.KLINE_INTERVAL = bots.iloc[0]['idinterval']
            binance_interval = fn.get_intervals(self.KLINE_INTERVAL,'binance')
            self.QUOTE_QTY = bots.iloc[0]['quote_qty']
            
            prms = (bots.iloc[0]['prm_values']).split(',')
            self.LONG_MEDIA_VALUE = int(prms[0])
            self.VELAS_PREVIAS = int(prms[1])
            self.QUOTE_TO_BUY = self.QUOTE_QTY * ( float(prms[2]) / 100 )
 

                    
        else:
            mylog.error('Bot::Init - No fue posible iniciar el bot ID: '+str(idbot))
            return False

        if self.idbot == 0:
            mylog.error('Bot::start - Bot ID invalido ')

        """Actualiza las velas"""
        if kline.update(self.SYMBOL):

            """Obtiene velas de la DB """
            klines = kline.get(self.SYMBOL, self.KLINE_INTERVAL, self.VELAS_PREVIAS)

            """Define la señal de Compra/Venta/Neutro"""
            signal = signals.adx_alternancia(klines, self.LONG_MEDIA_VALUE)

            """Obtiene info del SYMBOL"""
            """TODO Este metodo se va a reemplazar por una consulta guardada en la cache
                    para no generar consultas excesivas a Binance, sobre datos que pueden cambiar eventualmente
            """
            self.symbol_info = fn.get_symbol_info(self.client, self.SYMBOL)

            """Consultando balances"""
            base_asset = self.symbol_info['baseAsset']
            quote_asset = self.symbol_info['quoteAsset']
            quote_balance = round(float(self.client.get_asset_balance(asset=quote_asset)['free']), 2)
            base_balance = round(float(self.client.get_asset_balance(asset=base_asset)['free']), self.symbol_info['qty_dec_qty'])
            
            """Consultando posiciones de compra abiertas"""
            comprado_qty = 0
            query = "SELECT * FROM bot_order WHERE idbot = "+str(idbot)+" AND side = "+str(self.SIDE_BUY)+" AND pos_idbotorder = 0"
            open_pos_order = pd.read_sql(sql=query, con=db.engine)

            
            if open_pos_order['idbotorder'].count() > 1:
                mylog.criticalError('bot.py::run() - Existe mas de una posicion de compra abierta')
            elif open_pos_order['idbotorder'].count() > 0:
                comprado_qty = comprado_qty + open_pos_order.iloc[0]['qty']
            
            print('Comprado: ',base_asset, comprado_qty)
            print('Balance:  ',base_asset, base_balance,quote_asset, quote_balance)

            #Si no esta comprado y hay señal de compra 
            if comprado_qty == 0 and quote_balance >= self.QUOTE_TO_BUY: # and signal == 'COMPRA':
                
                #Calcula el precio promedio - Ver en la funcion functions.py:precio_actual que hay varias formas
                avg_price = fn.precio_actual(self.client, self.SYMBOL)
                price = round(avg_price, self.symbol_info['qty_dec_price'])

                #Calcula los parametros de la orden
                qty = round(self.QUOTE_TO_BUY/price,self.symbol_info['qty_dec_qty'])

                order = self.create_order(base_asset,
                                          quote_asset,
                                          self.SIDE_BUY,
                                          'MARKET',
                                          qty,
                                          price)
            
            #Si esta comprado y hay señal de venta
            elif comprado_qty > 0 and base_balance >= comprado_qty: # and signal == 'VENTA':
                
                #Calcula el precio promedio - Ver en la funcion functions.py:precio_actual que hay varias formas
                avg_price = fn.precio_actual(self.client, self.SYMBOL)
                price = round(avg_price, self.symbol_info['qty_dec_price'])

                #Calcula los parametros de la orden
                qty = round((base_balance),self.symbol_info['qty_dec_qty'])
                
                """
                order = self.create_order(self.client,
                                        self.SYMBOL,
                                        self.client.SIDE_SELL,
                                        'MARKET',
                                        qty)                
                """




            """TODO

            - Funciones de compra y venta
            - Registro de ordenes abiertas y completas y gestion del PNL
            - Calculo de comisiones
            - 
            - Reportes
            """

        else:
            mylog.error('Bot::start - No fue posible actualizar las velas')

    def create_order(self,base_asset,quote_asset,idside,type,qty,price):
        symbol = base_asset+quote_asset
        completed = 0
        order = False
        orderId = '_NOBINANCE_'

        operaBinance = True

        if idside == self.SIDE_BUY:
            side = self.client.SIDE_BUY
        elif idside == self.SIDE_SELL:
            side = self.client.SIDE_SELL
        #try:
        if operaBinance:
            order = self.client.create_order(
                        symbol=symbol,
                        side=side,
                        type=type,
                        quantity= qty
                        )
            
            if order:
                
                if order['status']=='FILLED':
                    completed = 1
                orderId = order['orderId']
                price = round(float(order['cummulativeQuoteQty'])/float(order['executedQty']),self.symbol_info['qty_dec_price'])
                qty = round(float(order['executedQty']),self.symbol_info['qty_dec_qty'])
        
        #Guarda al orden en la DB
        sql = "INSERT INTO bot_order (idbot,base_asset,quote_asset,side,completed,qty,price,orderId) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)"
        idbot = self.idbot
        print(idbot)     
        values = (idbot,base_asset,quote_asset,idside,completed,float(qty),float(price),orderId)
        res = db.cursor.execute(sql,values)
        print(res)
        #Envia mensaje a Telegram
        #msg_text = self.SYMBOL+" "+binance_interval + " COMPRA "+str(price)+" Exc.Price "+str(executedPrice)+" "+quote_asset+" "+str(quote_buyed)
        #tb.send_message(chatid, msg_text+"\n"+local.SERVER_IDENTIFIER)

        return order
        
        #except Exception as e:
        #    mylog.error(e)
        #    return False