from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker,DeclarativeBase
from settings import setting
engine=create_engine(url=setting.DB_CONNECTION)

LocalSession=sessionmaker(bind=engine)
class Base(DeclarativeBase):
    pass

def get_db():
    session=LocalSession()
    try:
        yield session
    finally:
        session.close()
        
