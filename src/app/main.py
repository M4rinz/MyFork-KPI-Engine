# app/main.py

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from src.app.db import get_historical_data, get_real_time_data
from src.app.kpi_engine.kpi_engine import KPIEngine
from src.app.kpi_engine.kpi_request import KPIRequest
from src.app.kpi_engine.kpi_response import KPIResponse

app = FastAPI()

@app.post("/kpi/")
async def get_kpi(
        request: KPIRequest,
        db1: Session = Depends(get_historical_data),
        db2: Session = Depends(get_real_time_data)
) -> KPIResponse:
    """
    Endpoint to get a calculated KPI by item_id using data from two databases.
    """
    try:
        return KPIEngine.compute(db1, db2, request)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")
