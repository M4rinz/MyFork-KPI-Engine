# app/main.py
import asyncio
import os

from aiokafka.admin import AIOKafkaAdminClient
from fastapi import FastAPI, HTTPException
from src.app.kpi_engine.kpi_engine import KPIEngine, get_references
from src.app.kpi_engine.kpi_request import (
    KPIRequest,
    RealTimeRequest,
    KPIStreamingRequest,
)
from src.app.kpi_engine.kpi_response import KPIResponse, RealTimeResponse
import uvicorn

from threading import Event


KAFKA_TOPIC_NAME = os.getenv("KAFKA_TOPIC_NAME")
KAFKA_SERVER = os.getenv("KAFKA_SERVER")
KAFKA_PORT = os.getenv("KAFKA_PORT")

app = FastAPI()

stop_event = Event()
consumer_task = None
kpi_engine = None


async def delete_kafka_topic(topic_name, bootstrap_servers):
    """Delete a Kafka topic."""
    admin_client = AIOKafkaAdminClient(bootstrap_servers=bootstrap_servers)
    await admin_client.start()
    try:
        await admin_client.delete_topics([topic_name])
        print(f"Topic '{topic_name}' deleted successfully.")
    except Exception as e:
        print(f"Error deleting topic '{topic_name}': {e}")


def start():
    host = "127.0.0.1"
    if os.getenv("RUNNING_IN_DOCKER"):
        host = "0.0.0.0"
    uvicorn.run("src.app.main:app", host=host, port=8008, reload=True)


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event to stop the consumer."""
    global stop_event
    stop_event.set()  # Signal the task to stop
    if consumer_task and not consumer_task.done():
        await consumer_task  # Wait for the task to finish
    await delete_kafka_topic(KAFKA_TOPIC_NAME, f"{KAFKA_SERVER}:{KAFKA_PORT}")


@app.get("/")
def read_root():
    return {"message": "Welcome to the KPI Engine!"}


@app.get("/health/")
def health_check():
    return {"status": "ok"}


@app.post("/kpi/")
async def get_kpi(
    request: KPIRequest,
) -> KPIResponse:
    try:
        return KPIEngine.compute(request)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Internal Server Error")


@app.post("/real-time/start")
async def real_time_session(
    request: RealTimeRequest,
) -> RealTimeResponse:
    global consumer_task, stop_event, kpi_engine

    if consumer_task and not consumer_task.done():
        return RealTimeResponse(
            message="A real-time session is already running.", status=400
        )

    stop_event.clear()

    kpis = get_references(request.name)

    kpi_streaming_request = KPIStreamingRequest(
        kpis=kpis,
        machines=request.machines,
        operations=request.operations,
    )
    kpi_engine = KPIEngine(KAFKA_TOPIC_NAME, KAFKA_PORT, KAFKA_SERVER)

    data_preprocessing_response = KPIEngine.connect_to_publisher(kpi_streaming_request)
    print(
        "Data Preprocessing Response on connection trial:", data_preprocessing_response
    )

    try:
        # Start the consumer and wait until it's ready
        await kpi_engine.consumer.start()
        print("Consumer started successfully")
    except Exception as e:
        print(f"Error starting consumer: {e}")
        return RealTimeResponse(
            message=f"Error starting consumer: {str(e)}", status=500
        )

    consumer_task = asyncio.create_task(kpi_engine.consume(request, stop_event))

    return RealTimeResponse(message="Real-time session started", status=200)


@app.get("/real-time/stop")
async def stop_consumer() -> RealTimeResponse:
    """Stop the Kafka consumer."""
    global stop_event, consumer_task

    if consumer_task is None or kpi_engine is None:
        return RealTimeResponse(message="The consumer has not started yet.", status=400)

    if consumer_task.done():
        return RealTimeResponse(message="The consumer has already stopped.", status=400)

    stop_event.set()  # Signal the task to stop

    # Process the last element of the consumer
    await consumer_task

    # Close all connections
    await kpi_engine.stop()

    return RealTimeResponse(
        message="Real-time session successfully stopped", status=200
    )
