import datetime

from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))

class Categories(Base):
    __tablename__ = 'categories'
    id = Column(Integer, primary_key = True)
    name = Column(String(50), nullable = False)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'id': self.id,
        }


class CatItem(Base):
    __tablename__ = 'item'
    id = Column(Integer, primary_key = True)
    name = Column(String(50), nullable = False)
    description = Column(String(50), nullable = False)
    time = Column(DateTime, default=datetime.datetime.now(), onupdate=datetime.datetime.now())
    categories_id = Column(Integer, ForeignKey('categories.id'))
    catalog = relationship(Categories)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'description': self.description,
            'id': self.id,
            'category ID': self.categories_id,
            'created/updated time': self.time,
        }


engine = create_engine('sqlite:///catalogmenu.db')
Base.metadata.create_all(engine)
