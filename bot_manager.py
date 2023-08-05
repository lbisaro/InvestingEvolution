import bot

#interval: #Interval:  1m 5m 15m 30m 1h 4h 1d

bot1 = bot.Bot(SYMBOL='BTCUSDT', KLINE_INTERVAL='1h',
               VELAS_PREVIAS=50, LONG_MEDIA_VALUE=14)
bot1.start()

bot2 = bot.Bot(SYMBOL='BNBUSDT', KLINE_INTERVAL='1h',
               VELAS_PREVIAS=50, LONG_MEDIA_VALUE=14)
bot2.start()

bot3 = bot.Bot(SYMBOL='ETHUSDT', KLINE_INTERVAL='1h',
               VELAS_PREVIAS=50, LONG_MEDIA_VALUE=14)
bot3.start()

