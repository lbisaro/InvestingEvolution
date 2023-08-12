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
import my_logging_klines as kline_log


# Conectar con Telegram
chatid = local.TLGMR_CHANNELID
tb = telebot.TeleBot(local.TLGMR_CHANNELID)

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
        #tb.send_message(chatid, "Entra "+local.SERVER_IDENTIFIER)
        #mylog.info('Inicia bot '+str(idbot))

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
            self.binance_interval = fn.get_intervals(self.KLINE_INTERVAL,'binance')
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
            klines = kline.get(self.SYMBOL, self.KLINE_INTERVAL, self.VELAS_PREVIAS+self.LONG_MEDIA_VALUE)

            """Define la señal de Compra/Venta/Neutro"""
            dfSignal = signals.adx_alternancia(klines, self.LONG_MEDIA_VALUE)
            signal = dfSignal['signal']

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
                idbotorder_master = open_pos_order.iloc[0]['idbotorder']
                comprado_qty = comprado_qty + open_pos_order.iloc[0]['qty']
            
            print('Comprado: ',base_asset, comprado_qty)
            print('Balance:  ',base_asset, base_balance,quote_asset, quote_balance)

            idbotorder = None
            op_price = None
            #Si no esta comprado y hay señal de compra 
            if comprado_qty == 0 and quote_balance >= self.QUOTE_TO_BUY and signal == 'COMPRA':
                
                #Calcula el precio promedio - Ver en la funcion functions.py:precio_actual que hay varias formas
                avg_price = fn.precio_actual(self.client, self.SYMBOL)
                price = round(avg_price, self.symbol_info['qty_dec_price'])

                #Calcula los parametros de la orden
                qty = round(self.QUOTE_TO_BUY/price,self.symbol_info['qty_dec_qty'])

                idbotorder = self.create_order(base_asset,
                                          quote_asset,
                                          self.SIDE_BUY,
                                          'MARKET',
                                          qty,
                                          price)
                op_price = -price
            #Si esta comprado y hay señal de venta
            elif comprado_qty > 0 and base_balance >= comprado_qty and signal == 'VENTA':
                
                #Calcula el precio promedio - Ver en la funcion functions.py:precio_actual que hay varias formas
                avg_price = fn.precio_actual(self.client, self.SYMBOL)
                price = round(avg_price, self.symbol_info['qty_dec_price'])

                #Calcula los parametros de la orden
                qty = round((base_balance),self.symbol_info['qty_dec_qty'])
                
                idbotorder = self.create_order(base_asset,
                                                quote_asset,
                                                self.SIDE_SELL,
                                                'MARKET',
                                                qty,
                                                price)                
                idbotorders_child = [idbotorder]
                self.close_position(idbotorder_master,idbotorders_child)
                op_price = price
            
            alternancia = 'No'
            if dfSignal['volume']:
                alternancia = 'Si'
            msg_kline = (datetime.utcnow() - timedelta(hours = 3) ).strftime('%Y-%m-%d %H:%M')
            msg_kline += ';'+self.SYMBOL
            msg_kline += ';'+str(dfSignal['close'])
            msg_kline += ';'+str(dfSignal['volume'])
            msg_kline += ';'+str(round(dfSignal['ADX'],2))
            msg_kline += ';'+str(round(dfSignal['ADX+'],2))
            msg_kline += ';'+str(round(dfSignal['ADX-'],2))
            msg_kline += ';'+alternancia+';'
            msg_kline += dfSignal['signal']
            msg_kline += ';'+str(idbotorder)
            msg_kline += ';'+str(op_price)
            msg_kline += ';'
            kline_log.send(msg_kline)
            

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

        operaBinance = False

        if idside == self.SIDE_BUY:
            side = self.client.SIDE_BUY
        elif idside == self.SIDE_SELL:
            side = self.client.SIDE_SELL
        
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
        idbot = self.idbot
        sql = "INSERT INTO bot_order (idbot,base_asset,quote_asset,side,completed,qty,price,orderId) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)"
        values = (idbot,base_asset,quote_asset,idside,completed,qty,price,orderId)
        db.cursor.execute(sql,values)
        db.connection.commit()
        idbotorder = db.cursor.lastrowid
        
        #Envia mensaje a Telegram
        # msg_text = self.SYMBOL+" "+self.binance_interval + " "+side+" "+str(price)+" Exc.Price "+str(price)+" "+quote_asset+" "+str(round(price*qty,2))
        # tb.send_message(chatid, msg_text+"\n"+local.SERVER_IDENTIFIER)

        return idbotorder
    
    def close_position(self,idbotorder_master,idbotorders_child):
        whereIn = str(idbotorder_master)
        for idbotorder in idbotorders_child:
            whereIn += ','+str(idbotorder) 
        sql = "UPDATE bot_order SET pos_idbotorder = '"+str(idbotorder_master)+"' WHERE idbotorder in ("+whereIn+")"
        db.cursor.execute(sql)
        db.connection.commit()