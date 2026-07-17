from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker,DeclarativeBase
from settings import setting
engine=create_engine(url="postgresql://mysql_4ebh_user:CZQhcUFSYiJIeIwNChx3wMrk2XVeHIqo@dpg-d9cuo7cj42us73fu2pj0-a/mysql_4ebh")

LocalSession=sessionmaker(bind=engine)
class Base(DeclarativeBase):
    pass

def get_db():
    session=LocalSession()
    try:
        yield session
    finally:
        session.close()
        
