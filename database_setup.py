import datetime

from sqlalchemy import Column, ForeignKey, Interger, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

class Categories(Base):
    __tablename__ = 'categories'
    id = Column(Interger, primary_key = True)
    name = Column(String(50), nullable = False)

class Item(Base):
    __tablename__ = 'item'
    id = Column(Interger, primary_key = True)
    name = Column(String(50), nullable = False)
    description = Column(String(50), nullable = False)
    time = Column(Datetime, onupdate= datetime.datetime.now)
    categories_id = Column(Interger, ForeignKey('Categories.id'))
    catalog = relationship(Categories)

engine = create_engine('sqlite:///catalogmenu.db')
Base.metadata.create_all(engine)
