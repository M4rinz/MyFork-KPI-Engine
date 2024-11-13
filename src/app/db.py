# app/db.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Database URLs (replace with actual connection strings)
DATABASE_URL_1 = "postgresql://user:password@db1_host:5432/db1"
DATABASE_URL_2 = "postgresql://user:password@db2_host:5432/db2"

# Create SQLAlchemy engines for each database
engine_historical_data = create_engine(DATABASE_URL_1)
engine_real_time_data = create_engine(DATABASE_URL_2)

# Create session factories for each database
SessionLocal_historical_data = sessionmaker(autocommit=False, autoflush=False, bind=engine_historical_data)
SessionLocal_real_time_data = sessionmaker(autocommit=False, autoflush=False, bind=engine_real_time_data)

# Dependency to provide database sessions in endpoints
def get_historical_data():
    db = SessionLocal_historical_data()
    try:
        yield db
    finally:
        db.close()

def get_real_time_data():
    db = SessionLocal_real_time_data()
    try:
        yield db
    finally:
        db.close()
