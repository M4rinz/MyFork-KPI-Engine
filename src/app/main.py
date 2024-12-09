# app/main.py
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from src.app.api.router import api_router
from src.app.api.endpoints.real_time import shutdown_event

app = FastAPI()
# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


def start():
    host = "127.0.0.1"
    if os.getenv("RUNNING_IN_DOCKER"):
        host = "0.0.0.0"
    uvicorn.run("src.app.main:app", host=host, port=8008, reload=True)


@app.on_event("shutdown")
async def shutdown():
    await shutdown_event()


@app.get("/")
def read_root():
    return {"Message": "Welcome to the KPI Engine!"}


@app.get("/health/")
def health_check():
    return {"Status": "ok"}
