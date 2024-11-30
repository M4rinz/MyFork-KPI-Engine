# app/main.py
import os

from fastapi import FastAPI, Depends, HTTPException
from src.app.db import get_connection
from src.app.kpi_engine.kpi_engine import KPIEngine
from src.app.kpi_engine.kpi_request import KPIRequest
from src.app.kpi_engine.kpi_response import KPIResponse
import uvicorn


app = FastAPI()


def start():
    host = "127.0.0.1"
    if os.getenv("RUNNING_IN_DOCKER"):
        host = "0.0.0.0"
    uvicorn.run("src.app.main:app", host=host, port=8008, reload=True)


@app.get("/")
def read_root():
    return {"message": "Welcome to the KPI Engine!"}


@app.get("/health/")
def health_check():
    return {"status": "ok"}


@app.post("/kpi/")
async def get_kpi(
    request: KPIRequest,
    db=Depends(get_connection),
) -> KPIResponse:
    try:
        return KPIEngine.compute(db, request)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Internal Server Error")
