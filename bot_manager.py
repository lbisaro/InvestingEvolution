import database as db
import bot
import my_logging as mylog

import pandas as pd
import numpy as np


"""

Agregar filtros en el loop:
    Ordenar por idusuario
    Solo Bots activos
    Actualizar las velas de los bots activos (SELECT distinct SYMBOL)
    Conectar a Binance una unica vez por usuario

"""

try:
    query = "SELECT * FROM bot "
    bots = pd.read_sql(sql=query, con=db.engine)
    if bots['idbot'].count() > 0:
        idbot = bots.iloc[0]['idbot']

        
        if np.int64(bots.iloc[0]['idestrategia']) == 1:
            BOT = bot.Bot()
            BOT.run(idbot)
            del BOT

except Exception as e:
    mylog.criticalError(f'bot_manager.py - {e}')
    


