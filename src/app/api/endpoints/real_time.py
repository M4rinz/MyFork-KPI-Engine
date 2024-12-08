# src/app/endpoints/real_time.py

import asyncio
from fastapi import APIRouter
from threading import Event
import os

from src.app.kpi_engine.kpi_engine import KPIEngine
from src.app.kpi_engine.regexp import prepare_for_real_time
from src.app.models.requests.data_processing import KPIStreamingRequest
from src.app.models.requests.gui import RealTimeKPIRequest
from src.app.models.responses.gui import RealTimeResponse
from src.app.services.data_processing import connect_to_publisher
from src.app.utils.kafka_admin import delete_kafka_topic

router = APIRouter()

stop_event = Event()
consumer_task = None
kpi_engine = None

KAFKA_TOPIC_NAME = os.getenv("KAFKA_TOPIC_NAME")
KAFKA_SERVER = os.getenv("KAFKA_SERVER")
KAFKA_PORT = os.getenv("KAFKA_PORT")


@router.post("/start", response_model=RealTimeResponse)
async def real_time_session(request: RealTimeKPIRequest) -> RealTimeResponse:
    global consumer_task, stop_event, kpi_engine

    if consumer_task and not consumer_task.done():
        return RealTimeResponse(
            message="A real-time session is already running.", status=400
        )

    stop_event.clear()

    involved_kpis, evaluable_formula = prepare_for_real_time(request.name)

    print("Involved KPIs:", involved_kpis)
    print("Evaluable Formula:", evaluable_formula)

    kpi_streaming_request = KPIStreamingRequest(
        kpis=involved_kpis,
        machines=request.machines,
        operations=request.operations,
    )
    kpi_engine = KPIEngine(KAFKA_TOPIC_NAME, KAFKA_PORT, KAFKA_SERVER)

    data_preprocessing_response = connect_to_publisher(kpi_streaming_request)
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


@router.get("/stop", response_model=RealTimeResponse)
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


async def shutdown_event():
    """Shutdown event to stop the consumer."""
    global stop_event
    stop_event.set()  # Signal the task to stop
    if consumer_task and not consumer_task.done():
        await consumer_task  # Wait for the task to finish
    await delete_kafka_topic(KAFKA_TOPIC_NAME, f"{KAFKA_SERVER}:{KAFKA_PORT}")
