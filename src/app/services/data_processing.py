import requests
from src.app.models.requests.data_processing import KPIStreamingRequest


def connect_to_publisher(kpi_streaming_request: KPIStreamingRequest):
    try:
        response = requests.post(
            "http://data-preprocessing-container:8003/real-time/start",
            data=kpi_streaming_request.to_json(),
        )
        response.raise_for_status()  # Raise error for non-2xx responses
        return response.json()
    except Exception as e:
        print(f"Error connecting to producer: {e}")
        return {"Error": "Could not connect to producer"}
