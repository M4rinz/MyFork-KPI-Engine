# app/models.py

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float, DateTime, ARRAY

KPI_DB = declarative_base()


class RealTimeData(KPI_DB):
    __tablename__ = "real_time_data"
    time = Column(DateTime, primary_key=True, index=True)
    asset_id = Column(String, primary_key=True, index=True)
    name = Column(String, index=True)
    kpi = Column(String, primary_key=True, index=True)
    sum = Column(Float)
    avg = Column(Float)
    max = Column(Float)
    min = Column(Float)
    operation = Column(String)


class AggregatedKPI(KPI_DB):
    __tablename__ = "aggregated_kpi"
    id = Column(Integer, primary_key=True, index=True)
    kpi_list = Column(ARRAY(String))
    name = Column(String, index=True)
    value = Column(Float)
    begin = Column(DateTime, index=True)
    end = Column(DateTime, index=True)
    machines = Column(ARRAY(String))
    operations = Column(ARRAY(String))
    step = Column(Integer)
