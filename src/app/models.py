# app/models.py

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float, DateTime

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


class AggregatedKPI(KPI_DB):
    __tablename__ = "aggregated_kpi"
    id = Column(Integer, primary_key=True, index=True)
    aggregated_kpi_name = Column(String, index=True)
    value = Column(Float)
    begin = Column(DateTime, index=True)
    end = Column(DateTime, index=True)
    asset_id = Column(String, index=True)
