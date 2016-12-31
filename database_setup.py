from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
import datetime
Base = declarative_base()
engine = create_engine('sqlite:///catalogmenu.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))

class Category(Base):
    __tablename__ = 'category'
    id = Column(Integer, primary_key = True)
    name = Column(String(50), nullable = False)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        item = session.query(CItem).filter_by(categories_id = self.id).all()
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'id': self.id,
            'item': [i.serialize for i in item],
        }


class CItem(Base):
    __tablename__ = 'citem'
    id = Column(Integer, primary_key = True)
    name = Column(String(250), nullable = False)
    description = Column(String(50), nullable = False)
    time = Column(DateTime, default=datetime.datetime.now(), onupdate=datetime.datetime.now())
    categories_id = Column(Integer, ForeignKey('category.id'))
    catalog = relationship(Category)
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
        }


engine = create_engine('sqlite:///catalogmenu.db')
Base.metadata.create_all(engine)
