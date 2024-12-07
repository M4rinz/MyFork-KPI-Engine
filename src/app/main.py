# app/main.py
import os

from fastapi import FastAPI, HTTPException
#from src.app.kpi_engine.kpi_engine import KPIEngine
#from src.app.kpi_engine.kpi_request import KPIRequest
#from src.app.kpi_engine.kpi_response import KPIResponse
from app.kpi_engine.kpi_engine import KPIEngine
from app.kpi_engine.kpi_request import KPIRequest
from app.kpi_engine.kpi_response import KPIResponse
import uvicorn


app = FastAPI()


def start():
    """Starts the FastAPI application using Uvicorn.

    :param None: This function takes no parameters.
    :raises RuntimeError: If the server fails to start.
    :return: None
    :rtype: None
    """

    host = "127.0.0.1"
    if os.getenv("RUNNING_IN_DOCKER"):
        host = "0.0.0.0"
    uvicorn.run("src.app.main:app", host=host, port=8008, reload=True)


@app.get("/")
def read_root():
    """Handles the root GET endpoint.
    This endpoint returns a welcome message to confirm that the service is running.

    :param None: This function takes no parameters.
    :return: A dictionary containing a welcome message.
    :rtype: dict
    """

    return {"message": "Welcome to the KPI Engine!"}


@app.get("/health/")
def health_check():
    """Handles the health check GET endpoint.
    This endpoint is used to verify the health and availability of the service.

    :param None: This function takes no parameters.
    :return: A dictionary indicating the service status with a key "status" set to "ok".
    :rtype: dict
    """

    return {"status": "ok"}


@app.post("/kpi/")
async def get_kpi(
    request: KPIRequest,
) -> KPIResponse:
    """Handles the KPI calculation POST endpoint.
    This endpoint accepts a request payload containing parameters for KPI computation and returns the computed KPI response. It handles errors gracefully, returning appropriate HTTP status codes for different failure scenarios.

    :param request: The request payload containing the parameters for KPI computation.
    :type request: KPIRequest
    :raises HTTPException: If the input data is invalid (404) or an unexpected error occurs (500).
    :return: The computed KPI response.
    :rtype: KPIResponse
    """
    try:
        return KPIEngine.compute(request)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Internal Server Error")
