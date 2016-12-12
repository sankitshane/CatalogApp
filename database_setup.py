import datetime

from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

class Categories(Base):
    __tablename__ = 'categories'
    id = Column(Integer, primary_key = True)
    name = Column(String(50), nullable = False)

class Item(Base):
    __tablename__ = 'item'
    id = Column(Integer, primary_key = True)
    name = Column(String(50), nullable = False)
    description = Column(String(50), nullable = False)
    time = Column(DateTime, onupdate= datetime.datetime.now)
    categories_id = Column(Integer, ForeignKey('categories.id'))
    catalog = relationship(Categories)

engine = create_engine('sqlite:///catalogmenu.db')
Base.metadata.create_all(engine)
