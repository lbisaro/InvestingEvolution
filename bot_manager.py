import bot

import time

#interval: #Interval:  1m 5m 15m 30m 1h 4h 1d

bot1 = bot.Bot(SYMBOL='BTCUSDT', KLINE_INTERVAL='1m',
               VELAS_PREVIAS=50, LONG_MEDIA_VALUE=14)
bot1.start()



