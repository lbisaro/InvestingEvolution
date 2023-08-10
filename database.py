import local__config as local
import my_logging as mylog
import mysql.connector
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

db = mysql.connector.connect(
  host=local.LOC_MYSQL_H,
  user=local.LOC_MYSQL_U,
  password=local.LOC_MYSQL_P,
  database=local.LOC_MYSQL_DB
)

cursor = db.cursor()