"""KPI Calculation Engine."""

import json

import requests


from aiokafka import AIOKafkaConsumer

from src.app.models.real_time_kpi import RealTimeKPI
from src.app.models.requests.gui import RealTimeKPIRequest
from src.app.models.responses.gui import RealTimeKPIResponse
from src.app.utils.kafka_admin import delete_kafka_topic


class KPIEngine:
    instance = None

    def __init__(self, topic, port, servers) -> None:
        self._topic = topic
        self._port = port
        self._servers = servers
        self.consumer = self.create_consumer()
        self.websocket = None
        # self.websocket = create_websocket()
        KPIEngine.instance = self
        print(
            "KPI Engine initialized: created consumer. Topic: ",
            topic,
            " Port: ",
            port,
            " Servers: ",
            servers,
        )

    def create_consumer(self):
        def decode_message(message):
            return [
                RealTimeKPI.from_json(json.loads(item))
                for item in json.loads(message.decode("utf-8"))
            ]

        return AIOKafkaConsumer(
            self._topic,
            bootstrap_servers=f"{self._servers}:{self._port}",
            # value_deserializer=decode_message,
            auto_offset_reset="earliest",
        )

    async def start_consumer(self):
        try:
            await self.consumer.start()
            print("Consumer started successfully")
        except Exception as e:
            print(f"Error starting consumer: {e}")
            return {"Error": f"Error starting consumer: {str(e)}"}

    async def consume(self, request: RealTimeKPIRequest, stop_event):
        try:
            print("consuming")
            while not stop_event.is_set():
                # get the last message from the topic
                real_time_kpis = (await self.consumer.getone()).value
                print("Consumed message: ", real_time_kpis)

                # compute real time kpis
                _ = self.compute_real_time(real_time_kpis, request)

                # send the computed result to the GUI via websocket
                # await self.send_real_time_result(real_time_response)

        except Exception as e:
            print("Error in consumer: ", e)
        finally:
            await self.consumer.stop()

    def compute_real_time(
        self, real_time_kpis: list[RealTimeKPI], request: RealTimeKPIRequest
    ) -> RealTimeKPIResponse:
        # add kpis to partial results
        # compute kpi in real time aggregating everything
        pass

    async def send_real_time_result(self, response: RealTimeKPIResponse):
        """
        Sends a real-time result to the GUI via the WebSocket.
        """
        try:
            if not self.websocket:
                raise RuntimeError("WebSocket is not connected.")

            # Convert the response to JSON and send it
            await self.websocket.send(response.to_json())
            print("Sent real-time KPI result to GUI:", response.to_json())
        except Exception as e:
            print(f"Error sending real-time result via WebSocket: {e}")

    async def stop(self):
        try:
            if self.consumer:
                await self.consumer.stop()
                print("Kafka consumer stopped.")

            await delete_kafka_topic(self._topic, f"{self._servers}:{self._topic}")

            if self.websocket:
                await self.websocket.close()
                print("WebSocket connection closed.")

            response = requests.get(
                "http://data-preprocessing-container:8003/real-time/stop",
            )
            response.raise_for_status()

        except Exception as e:
            print(f"Error stopping connections: {e}")
