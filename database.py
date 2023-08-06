import local__config as local
import my_logging as mylog
from sqlalchemy import create_engine
import pandas as pd

engine = create_engine("mysql+pymysql://{user}:{pw}@{host}/{db}"
                .format(host=local.LOC_MYSQL_H,
                        user=local.LOC_MYSQL_U,
                        pw=local.LOC_MYSQL_P,
                        db=local.LOC_MYSQL_DB))

try:
    query = "SHOW TABLES"
    bots = pd.read_sql(sql=query, con=engine)
except Exception as e:
    mylog.criticalError(f'database.py - Error de coneccion{e}')
