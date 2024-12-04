import os
from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv

load_dotenv()

Base = declarative_base()

class Image(Base):
    __tablename__ = os.getenv("DATABASE_TABLE")

    id = Column(Integer, primary_key=True, index=True)
    image_name = Column(String, index=True)
    file_url = Column(String,)
    prediction = Column(String,)
    confidence = Column(Float,)