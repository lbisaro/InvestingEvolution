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

# tb.send_message(chatid, "Mensaje ✅ uno 🔻 dos ")
# tb.send_message(chatid, '*Bold* _Italic_ __Underline__', parse_mode="MarkdownV2")
# exit()


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
            symbol_info = fn.get_symbol_info(self.client, self.SYMBOL)

            """Obtiene el balance que existe para cada asset
               Esto se utiliza actualmente cuando aparece una señal de venta
               Por el momento vende todo lo que hay en el balance del base_asset
               Pero en el futuro tiene que vender lo que se haya comprado
               obteniendo la cantidad de token de las ordenes registradas en la DB 
            """
            base_asset = symbol_info['baseAsset']
            quote_asset = symbol_info['quoteAsset']
            quote_balance = round(float(self.client.get_asset_balance(asset=quote_asset)['free']), 2)
            print('quote_balance',quote_asset,quote_balance)
            asset_balance = round(float(self.client.get_asset_balance(asset=base_asset)['free']), symbol_info['qty_dec_qty'])
            print('asset_balance',base_asset,asset_balance)

            """ TODO Esto queda pendiente para calcular lo que hay comprado desde la DB
                En la testnet se recalcula el balance cada tanto y ppuede no coincidir con 
                las ordenes de compra y venta registradas
            """
            #query = "SELECT * FROM bot_order WHERE idbot = 1 AND completed = 0"
            #open_orders = pd.read_sql(sql=query, con=db.engine)
            #comprado_qty = 0
            #comprado_quote = 0
            #if open_orders['idbotorder'].count() > 0:
            #    for i in open_orders.index:
            #        if open_orders.loc[i]['side'] == self.SIDE_BUY:
            #            comprado_qty = comprado_qty + open_orders.loc[i]['origQty']
            #            comprado_quote = comprado_quote + open_orders.loc[i]['origQty'] * open_orders.loc[i]['price']
            #        if open_orders.loc[i]['side'] == self.SIDE_SELL:
            #            comprado_qty = comprado_qty - open_orders.loc[i]['origQty']
            #            comprado_quote = comprado_quote - open_orders.loc[i]['origQty'] * open_orders.loc[i]['price']
            #print('comprado: ',base_asset, comprado_qty, quote_asset,comprado_quote)

            #Crea un dataframe con una orden de compra/venta con valores por default
            new_order = pd.DataFrame([[1,base_asset,quote_asset]],columns=['idbot','base_asset','quote_asset'])
        
            #Si no esta comprado y hay señal de compra 
            if asset_balance == 0 and signal == 'COMPRA':
                
                #Calcula el precio promedio - Ver en la funcion functions.py:precio_actual que hay varias formas
                avg_price = fn.precioActual(self.client, self.SYMBOL)
                price = round(avg_price, symbol_info['qty_dec_price'])

                #Calcula los parametros de la orden
                origQty = round(self.QUOTE_TO_BUY/price,symbol_info['qty_dec_qty'])
                new_order['side'] = self.SIDE_BUY
                new_order['origQty'] = origQty
                new_order['orderId'] = ''
                new_order['completed'] = 0
                
                order = self.client.create_order(
                                symbol=self.SYMBOL,
                                side=self.client.SIDE_BUY,
                                type='MARKET',
                                quantity= origQty
                                )
                #Obtiene los resultados de la orden
                new_order['orderId'] = order['orderId']
                executedPrice = round(float(order['cummulativeQuoteQty'])/float(order['executedQty']),symbol_info['qty_dec_price'])
                new_order['price'] = executedPrice
                new_order['origQty'] = round(float(order['executedQty']),symbol_info['qty_dec_qty'])
                new_order['completed'] = 1
                quote_buyed = round(executedPrice*float(order['executedQty']),2)
                
                #Guarda al orden en la DB
                new_order.to_sql('bot_order', con=db.engine, index=False,if_exists='append')

                #Envia mensaje a Telegram
                emoji = '✅'
                msg_text = local.SERVER_IDENTIFIER+"\n"+self.SYMBOL+" "+binance_interval + " COMPRA "+emoji+" "+str(price)+" Exc.Price "+str(executedPrice)+" "+quote_asset+" "+str(quote_buyed)
                tb.send_message(chatid, msg_text)
            
            #Si esta comprado y hay señal de venta
            elif asset_balance > 0 and signal == 'VENTA':

                #Calcula el precio promedio - Ver en la funcion functions.py:precio_actual que hay varias formas
                avg_price = fn.precio_actual(self.client, self.SYMBOL)
                price = round(avg_price, symbol_info['qty_dec_price'])

                #Calcula los parametros de la orden
                origQty = round((asset_balance),symbol_info['qty_dec_qty'])
                new_order['side'] = self.SIDE_SELL
                new_order['origQty'] = origQty
                new_order['orderId'] = ''
                new_order['completed'] = 0
                                
                order = self.client.create_order(
                                symbol=self.SYMBOL,
                                side=self.client.SIDE_SELL,
                                type='MARKET',
                                quantity= origQty
                                )
                #Obtiene los resultados de la orden
                new_order['orderId'] = order['orderId']
                executedPrice = round(float(order['cummulativeQuoteQty'])/float(order['executedQty']),symbol_info['qty_dec_price'])
                new_order['price'] = executedPrice
                new_order['origQty'] = round(float(order['executedQty']),symbol_info['qty_dec_qty'])
                new_order['completed'] = 1
                quote_selled = round(executedPrice*float(order['executedQty']),2)
                
                #Guarda al orden en la DB
                new_order.to_sql('bot_order', con=db.engine, index=False,if_exists='append')
                
                #Envia mensaje a Telegram
                emoji = '🔻'
                msg_text = local.SERVER_IDENTIFIER+"\n"+self.SYMBOL+" "+binance_interval + " VENTA "+emoji+" "+str(price)+" Exc.Price "+str(executedPrice)+" "+quote_asset+" "+str(quote_selled)
                tb.send_message(chatid, msg_text)




            """TODO

            - Funciones de compra y venta
            - Registro de ordenes abiertas y completas y gestion del PNL
            - Calculo de comisiones
            - 
            - Reportes
            """

        else:
            mylog.error('Bot::start - No fue posible actualizar las velas')
