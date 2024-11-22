# app/db.py
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# Database URLs for each database
DB_URL = (
    f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
)

# Create SQLAlchemy engines for each database
DB_engine = create_engine(DB_URL)

# Create session factories for each database
SessionLocal_aggregated_kpi_data = sessionmaker(
    autocommit=False, autoflush=False, bind=DB_engine
)


# Dependency to provide database sessions in endpoints
def get_kpi_db():
    db = SessionLocal_aggregated_kpi_data()
    try:
        yield db
    finally:
        db.close()
