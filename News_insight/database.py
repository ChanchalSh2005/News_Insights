from sqlalchemy import create_engine   #engine creation for communication with our appliaction 
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base


URL_DATABASE = "postgresql://neondb_owner:npg_S3xz9PrYBUTe@ep-dawn-tooth-annej652-pooler.c-6.us-east-1.aws.neon.tech/news?sslmode=require&channel_binding=require"

engine=create_engine(URL_DATABASE)

SessionLocal=sessionmaker(autocommit=False,autoflush=False,bind=engine)

Base=declarative_base()

def get_db():
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()