from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


# Users Table in DB
class Users(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    firstname = Column(String)
    lastname = Column(String)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    phone_number = Column(String)
    address_id = Column(Integer, ForeignKey('address.id'), nullable=True)

    todos = relationship('Todo', back_populates='owner')
    address = relationship('Address', back_populates='user_address')


# Todos Table in DB
class Todo(Base):
    __tablename__ = 'todos'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(String)
    priority = Column(Integer)
    complete = Column(Boolean, default=False)
    owner_id = Column(Integer, ForeignKey('users.id'))

    owner = relationship('Users', back_populates='todos')


class Address(Base):

    __tablename__ = 'address'

    id = Column(Integer, primary_key=True, index=True)
    address1 = Column(String)
    address2 = Column(String)
    city = Column(String)
    state = Column(String)
    zipcode = Column(String)
    country = Column(String)
    apt_num = Column(Integer)

    # make the relation with USers model with address
    user_address = relationship('Users', back_populates='address')







