import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String, Float, DateTime, Boolean, Text, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

###### DB SETTINGS ######
DB_USER= "dashboard"
DB_PASS= "Eatq~465"
DB_HOST= "localhost"
DB_PORT= "3306"
DATABASE= "dashboard"
#########################

Base = declarative_base()
class User(Base):
    __tablename__ = 'auth_user'
    id = Column(Integer, primary_key=True)
    username = Column(String(255))
    is_active = Column(Boolean)

class Profile(Base):
    __tablename__ = 'dashboard_profile'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    max_trades_per_coin = Column(Integer)
    auto_close_timer = Column(String(255))

class Account(Base):
    __tablename__ = 'dashboard_accounts'
    id = Column(Integer, primary_key=True)
    user_name = Column(String(255))
    type = Column(String(255))
    api_key = Column(String(255))
    api_secret = Column(String(255))
    name = Column(String(255))
    active = Column(Boolean)

class Channel(Base):
    __tablename__ = 'dashboard_channels'
    id = Column(Integer, primary_key=True)
    user_name = Column(String(255))
    code = Column(String(255))
    risk_percent = Column(Float)
    allowed_percent = Column(Float)
    active = Column(Boolean)

class Signal(Base):
    __tablename__ = 'signals'
    id = Column(Integer, primary_key=True)
    pair = Column(String(255))
    buy_price = Column(String(255))
    stop_loss = Column(String(255))
    tp1 = Column(String(255))
    tp2 = Column(String(255))
    tp3 = Column(String(255))
    tp4 = Column(String(255))
    channel = Column(String(255))
    note = Column(String(1024))

class Trade(Base):
    __tablename__ = 'trades'
    id = Column(Integer, primary_key=True)
    signal_id = Column(Integer)
    user_name = Column(String(255))
    channel = Column(String(255))
    response = Column(Text)

class ProcessedTarget(Base):
    __tablename__ = 'processed_targets'
    id = Column(Integer, primary_key=True)
    user_name = Column(String(255))
    trade_id = Column(String(255))
    step_id = Column(String(255))


#connect_string= "sqlite:///db.sqlite3"
#engine = create_engine(connect_string)

connect_string = 'mysql+pymysql://{}:{}@{}:{}/{}?charset=utf8mb4'.format(DB_USER, DB_PASS, DB_HOST, DB_PORT, DATABASE)
engine = create_engine(connect_string, pool_size=500, max_overflow=0)
Base.metadata.create_all(engine)
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)