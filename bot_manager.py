import database as db
import bot
import my_logging as mylog

import pandas as pd
import numpy as np

import functions as fn





"""TODO
Actualizar las velas de los bots activos (SELECT distinct SYMBOL)
    
Agregar filtros en el loop:
    Ordenar por idusuario
    Solo Bots y Usuarios activos
    Conectar a Binance una unica vez por usuario

"""

whereIn = fn.get_interval_actual()

#try:
#Busca los Bots registrados en la DB
query = "SELECT * FROM bot WHERE idinterval in ("+whereIn+")"
bots = pd.read_sql(sql=query, con=db.engine)
if bots['idbot'].count() > 0:
    for i in bots.index:
        idbot = bots.loc[i]['idbot']
        
        #Si el bot listado coincide con la estrategia, lo ejecuta
        if np.int64(bots.loc[i]['idestrategia']) == 1:
            BOT = bot.Bot()
            BOT.run(idbot)
            del BOT

#except Exception as e:
#    mylog.criticalError(f'bot_manager.py - No fue posible acceder a la lista de bots {e}')
    


