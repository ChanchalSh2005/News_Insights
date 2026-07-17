from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker,DeclarativeBase
from settings import setting
import os
user = os.getenv("MYSQLUSER")
password = os.getenv("MYSQLPASSWORD")
host = os.getenv("MYSQLHOST")
port = os.getenv("MYSQLPORT")
database = os.getenv("MYSQLDATABASE")
DATABASE_URL = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"


LocalSession=sessionmaker(bind=engine)
class Base(DeclarativeBase):
    pass

def get_db():
    session=LocalSession()
    try:
        yield session
    finally:
        session.close()
        
