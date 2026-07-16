from sqlalchemy import Column, Integer, String, Text, DateTime
from db import Base
#from database import Base
from datetime import datetime


class News_model(Base):
    __tablename__ = 'news'   # table names should be lowercase
    iso_time = '2026-03-04T05:17:22Z'
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text)   # use Text instead of String
    summarised = Column(Text, nullable=False)
    image = Column(String(500))
    url = Column(String(500), unique=True, nullable=False)
    publishedAt = Column(DateTime,nullable=True)
    source = Column(String(200))
   