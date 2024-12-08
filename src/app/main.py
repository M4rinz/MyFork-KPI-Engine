# app/main.py
import os
from fastapi import FastAPI
import uvicorn
from src.app.api.router import api_router
from src.app.api.endpoints.real_time import shutdown_event

app = FastAPI()
app.include_router(api_router)


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


@app.on_event("shutdown")
async def shutdown():
    await shutdown_event()


@app.get("/")
def read_root():
    """Handles the root GET endpoint.
    This endpoint returns a welcome message to confirm that the service is running.

    :param None: This function takes no parameters.
    :return: A dictionary containing a welcome message.
    :rtype: dict
    """

    return {"Message": "Welcome to the KPI Engine!"}


@app.get("/health/")
def health_check():
    return {"Status": "ok"}
