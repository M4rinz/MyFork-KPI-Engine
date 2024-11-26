from sqlalchemy import create_engine
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

# Database URLs for each database
DB_URL = (
    f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
)


# Define your SQLAlchemy engine
engine = create_engine(DB_URL)  # Use your specific database connection string

with engine.connect() as connection:
    # Execute a raw SQL query
    raw_query_statement = f"""
    SELECT avg, time, asset_id, operation
    FROM real_time_data
    WHERE operation IN ('idle', 'working')
    AND name in ('Large Capacity Cutting Machine 1', 'Large Capacity Cutting Machine 2')
    AND time BETWEEN '2024-05-02T00:00:00' AND '2024-05-20T00:00:00';
    """

    # Execute the query using SQLAlchemy engine
    dataframe = pd.read_sql_query(raw_query_statement, connection)
    print(dataframe.head())
