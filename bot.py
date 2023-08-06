import local__config as local
import functions as fn
import database as db
import time
import kline
import local__signals as signals
from sqlalchemy import insert

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import telebot
from binance.client import Client
import logging

# Configura el logging
logging.basicConfig(filename='bot.log', filemode='a',
                    format='%(asctime)s %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S', level=logging.INFO)

# logging.warning("Inicio", exc_info=False)

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
    #logging.info("Inicio", exc_info=False)

    def run(self,idbot):

        query = "SELECT * "+ \
                "FROM bot "+ \
                "LEFT JOIN intervals ON intervals.idinterval = bot.idinterval "+ \
                "WHERE idbot = '"+str(idbot)+"'"
        bots = pd.read_sql(sql=query, con=db.engine)
        if bots['idbot'].count()== 1:
            if bots.iloc[0]['idbot'] != idbot:
                logging.error("Bot::run(idbot="+idbot+") ID invalido", exc_info=False)
                return False
            
            if np.int64(bots.iloc[0]['idestrategia']) != self.VALID_IDESTRATEGIA:
                logging.error("Bot::run(idbot="+str(idbot)+") idestrategia erronea", exc_info=False)
                return False
            
            self.SYMBOL = bots.iloc[0]['base_asset']+bots.iloc[0]['quote_asset']
            self.KLINE_INTERVAL = bots.iloc[0]['binance_interval']
            self.QUOTE_QTY = bots.iloc[0]['quote_qty']

            prms = (bots.iloc[0]['prm_values']).split(',')
            self.LONG_MEDIA_VALUE = int(prms[0])
            self.VELAS_PREVIAS = int(prms[1])
            self.QUOTE_TO_BUY = self.QUOTE_QTY * ( float(prms[2]) / 100 )
            self.idbot = idbot
                    
        else:
            logging.error('Bot::Init - No fue posible iniciar el bot ID: '+str(idbot), exc_info=False)
            return False

        if self.idbot == 0:
            logging.error('Bot::start - Bot ID invalido ', exc_info=False)

        # logging.warning("Start", exc_info=False)
        if kline.update(self.SYMBOL):

            klines = kline.get(self.SYMBOL, self.KLINE_INTERVAL, self.VELAS_PREVIAS)

            signal = signals.adx_alternancia(klines, self.LONG_MEDIA_VALUE)

            symbol_info = fn.getSymbolInfo(self.client, self.SYMBOL)

            avg_price = fn.precioActual(self.client, self.SYMBOL)

            price = round(avg_price, symbol_info['qty_dec_price'])

            base_asset = symbol_info['baseAsset']
            quote_asset = symbol_info['quoteAsset']
            quote_balance = round(float(self.client.get_asset_balance(asset=quote_asset)['free']), 2)
            print('quote_balance',quote_asset,quote_balance)
            asset_balance = round(float(self.client.get_asset_balance(asset=base_asset)['free']), symbol_info['qty_dec_qty'])
            print('asset_balance',base_asset,asset_balance)

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

            new_order = pd.DataFrame([[1,base_asset,quote_asset]],columns=['idbot','base_asset','quote_asset'])
        
            if asset_balance == 0 and signal == 'COMPRA':

                origQty = round(self.QUOTE_TO_BUY/price,symbol_info['qty_dec_qty'])
                new_order['side'] = self.SIDE_BUY
                new_order['origQty'] = origQty
                new_order['orderId'] = ''
                new_order['completed'] = 0
                
                print('comprar',new_order)
                order = self.client.create_order(
                                symbol=self.SYMBOL,
                                side=self.client.SIDE_BUY,
                                type='MARKET',
                                quantity= origQty
                                )
                new_order['orderId'] = order['orderId']
                executedPrice = round(float(order['cummulativeQuoteQty'])/float(order['executedQty']),symbol_info['qty_dec_price'])
                new_order['price'] = executedPrice
                new_order['origQty'] = round(float(order['executedQty']),symbol_info['qty_dec_qty'])
                new_order['completed'] = 1
                
                new_order.to_sql('bot_order', con=db.engine, index=False,if_exists='append')
                emoji = '✅'
                msg_text = self.SYMBOL+" "+self.KLINE_INTERVAL + " COMPRA "+emoji+" "+str(price)+" Exc.Price "+str(executedPrice)
                tb.send_message(chatid, msg_text)
                print(msg_text)
            
            elif asset_balance > 0 and signal == 'VENTA':
                origQty = round((asset_balance),symbol_info['qty_dec_qty'])
                new_order['side'] = self.SIDE_SELL
                new_order['origQty'] = origQty
                new_order['orderId'] = ''
                new_order['completed'] = 0
                
                print('vender',new_order)
                order = self.client.create_order(
                                symbol=self.SYMBOL,
                                side=self.client.SIDE_SELL,
                                type='MARKET',
                                quantity= origQty
                                )
                new_order['orderId'] = order['orderId']
                executedPrice = round(float(order['cummulativeQuoteQty'])/float(order['executedQty']),symbol_info['qty_dec_price'])
                new_order['price'] = executedPrice
                new_order['origQty'] = round(float(order['executedQty']),symbol_info['qty_dec_qty'])
                new_order['completed'] = 1
                
                new_order.to_sql('bot_order', con=db.engine, index=False,if_exists='append')
                emoji = '🔻'
                msg_text = self.SYMBOL+" "+self.KLINE_INTERVAL + " VENTA "+emoji+" "+str(price)+" Exc.Price "+str(executedPrice)
                tb.send_message(chatid, msg_text)
                print(msg_text)



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
            logging.error('Bot::start - No fue posible actualizar las velas', exc_info=False)
