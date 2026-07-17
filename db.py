from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker,DeclarativeBase
from settings import setting
url=setting.DB_CONNECTION
print("DB_CONNECTION:",url)
print("repr =", repr(url))
engine=create_engine(url=url)

LocalSession=sessionmaker(bind=engine)
class Base(DeclarativeBase):
    pass

def get_db():
    session=LocalSession()
    try:
        yield session
    finally:
        session.close()
        
