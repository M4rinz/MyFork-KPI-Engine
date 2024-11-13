# app/models.py

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float, DateTime

Base_db1 = declarative_base()
Base_db2 = declarative_base()

# Define tables for Database 1
class RealTimeData(Base_db1):
    __tablename__ = "RealTimeData"
    id = Column(Integer, primary_key=True, index=True)
    kpi = Column(String, index=True)
    name = Column(String, index=True)
    time = Column(DateTime, index=True)
    value = Column(Float)

# Define tables for Database 2
class HistoricalData(Base_db2):
    __tablename__ = "HistoricalData"
    id = Column(Integer, primary_key=True, index=True)
    # TODO: define columns for HistoricalData
