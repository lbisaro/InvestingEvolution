import local__config as local
from sqlalchemy import create_engine
from sqlalchemy import insert

# create sqlalchemy engine
engine = create_engine("mysql+pymysql://{user}:{pw}@{host}/{db}"
                        .format(host=local.LOC_MYSQL_H,
                                user=local.LOC_MYSQL_U,
                                pw=local.LOC_MYSQL_P,
                                db=local.LOC_MYSQL_DB))