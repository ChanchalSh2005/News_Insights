from sqlalchemy import create_engine   #engine creation for communication with our appliaction 
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base


URL_DATABASE = "mysql+pymysql://root:Chanchal%40123@localhost:3306/inshorts_db"

engine=create_engine(URL_DATABASE)

SessionLocal=sessionmaker(autocommit=False,autoflush=False,bind=engine)

Base=declarative_base()

def get_db():
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()