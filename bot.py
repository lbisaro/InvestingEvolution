import local__config as local
import functions as fn
import database as db
import time
import kline
import local__signals as signals
from sqlalchemy import insert

import pandas as pd
from datetime import datetime, timedelta
import telebot
from binance.client import Client
import logging

# Configura el logging
logging.basicConfig(filename='bot.log', filemode='a',
                    format='%(asctime)s %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
# logging.warning("Inicio", exc_info=False)

# Conectar con Telegram
chatid = local.LOC_TLGRM_CHATID
tb = telebot.TeleBot(local.LOC_TLGRM_TK)

# tb.send_message(chatid, "Mensaje ✅ uno 🔻 dos ")
# tb.send_message(chatid, '*Bold* _Italic_ __Underline__', parse_mode="MarkdownV2")
# exit()


class Bot:
    def __init__(self, SYMBOL, KLINE_INTERVAL, VELAS_PREVIAS, LONG_MEDIA_VALUE):
        self.SYMBOL = SYMBOL
        self.KLINE_INTERVAL = KLINE_INTERVAL
        self.VELAS_PREVIAS = VELAS_PREVIAS
        self.LONG_MEDIA_VALUE = LONG_MEDIA_VALUE

    SIDE_BUY = 0
    SIDE_SELL = 1

    # Conectar Binance
    client = Client(local.LOC_BNC_AK, local.LOC_BNC_SK,
                    testnet=local.LOC_BNC_TESNET)
    # logging.warning("Inicio", exc_info=False)

    def start(self):

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

                quote_to_buy = 100
                origQty = round(quote_to_buy/price,symbol_info['qty_dec_qty'])
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
                new_order['price'] = round(float(order['cummulativeQuoteQty'])/float(order['executedQty']),symbol_info['qty_dec_price'])
                new_order['qty'] = round(order['executedQty'],symbol_info['qty_dec_qty'])
                if order['status'] == 'FILLED':
                    new_order['completed'] = 1
                
                new_order.to_sql('bot_order', con=db.engine, index=False,
                        if_exists='append')
                
                new_order.to_sql('bot_order', con=db.engine, index=False,if_exists='append')
                emoji = '✅'
                msg_text = 'Test '+self.SYMBOL+" "+self.KLINE_INTERVAL + " COMPRA "+emoji+" Actual Price "+str(price)+" Excecuted Price "+new_order['price']
                tb.send_message(chatid, msg_text)
                
                print('compra',new_order)
            
            elif asset_balance > 0 and signal == 'VENTA':
                origQty = round((asset_balance*0.1),symbol_info['qty_dec_qty'])
                new_order['side'] = self.SIDE_SELL
                new_order['origQty'] = origQty
                new_order['orderId'] = ''
                new_order['completed'] = 0
                
                print('vender',new_order)
                order = self.client.create_order(
                                symbol=self.SYMBOL,
                                side=self.client.SIDE_BUY,
                                type='MARKET',
                                quantity= origQty
                                )
                new_order['orderId'] = order['orderId']
                new_order['price'] = round(float(order['cummulativeQuoteQty'])/float(order['executedQty']),symbol_info['qty_dec_price'])
                new_order['qty'] = round(order['executedQty'],symbol_info['qty_dec_qty'])
                if order['status'] == 'FILLED':
                    new_order['completed'] = 1
                
                new_order.to_sql('bot_order', con=db.engine, index=False,
                        if_exists='append')
                
                new_order.to_sql('bot_order', con=db.engine, index=False,if_exists='append')
                emoji = '🔻'
                msg_text = 'Test '+self.SYMBOL+" "+self.KLINE_INTERVAL + " VENTA "+emoji+" Actual Price "+str(price)+" Excecuted Price "+new_order['price']
                tb.send_message(chatid, msg_text)
                print('venta',new_order)


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
