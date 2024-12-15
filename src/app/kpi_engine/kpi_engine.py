"""KPI Calculation Engine."""

import json
from datetime import datetime

import requests
import numpy as np
import numexpr as ne

from aiokafka import AIOKafkaConsumer
from fastapi import WebSocket

from src.app.models.real_time_kpi import RealTimeKPI
from src.app.models.requests.gui import RealTimeKPIRequest
from src.app.models.responses.gui import RealTimeKPIResponse
from src.app.utils.kafka_admin import delete_kafka_topic


class KPIEngine:
    instance = None

    def __init__(self, topic, port, servers, evaluable_formula_info) -> None:
        self._topic = topic
        self._port = port
        self._servers = servers
        self.consumer = self.create_consumer()
        self.partial_result = {}
        self.evaluable_formula_info = evaluable_formula_info
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
            value_deserializer=decode_message,
            auto_offset_reset="earliest",
            enable_auto_commit=True,
        )

    async def start_consumer(self):
        try:
            await self.consumer.start()
        except Exception as e:
            print(f"Error starting consumer: {e}")
            return {"Error": f"Error starting consumer: {str(e)}"}

    async def consume(
        self, websocket: WebSocket, request: RealTimeKPIRequest, stop_event
    ):
        try:
            print("Consuming messages...")
            while not stop_event.is_set():
                # get the last message from the topic
                real_time_kpis = (await self.consumer.getone()).value

                # compute real time kpis
                response = self.compute_real_time(real_time_kpis, request)

                # send the computed result to the GUI via websocket
                await websocket.send_json(response.to_json())

        except Exception as e:
            print("Error in consumer: ", e)
        finally:
            await self.consumer.stop()

    def compute_real_time(
        self, real_time_kpis: list[RealTimeKPI], request: RealTimeKPIRequest
    ) -> RealTimeKPIResponse:

        special=bool(self.evaluable_formula_info["particular"])
        # Convert real_time_kpis to numpy arrays
        for kpi in real_time_kpis:
            complete_name = f"{kpi.kpi}_{kpi.column}"
            if special:
                complete_name += f"_{kpi.operation}"
            if complete_name not in self.partial_result:
                self.partial_result[complete_name] = np.empty((0, len(kpi.values)))
            self.partial_result[complete_name] = np.vstack(
                [self.partial_result[complete_name], kpi.values]
            )


        # Set globals for involved KPIs
        involved_kpis = self.partial_result.keys()
        for base_kpi in involved_kpis:
            if not special:
                globals()[base_kpi] = self.partial_result[base_kpi]
            else:
                # if it is particular we made the aggregation inside and not outside
                aggregation = self.evaluable_formula_info["agg"]
                globals()[base_kpi] = getattr(np, aggregation)(self.partial_result[base_kpi], axis=1)

        # Evaluate the formula
        formula = self.evaluable_formula_info["formula"]
        results = ne.evaluate(formula)

        # Aggregate the result
        out=results
        #we chech if it is particular so we make the final aggregation
        if not special:
            aggregation = self.evaluable_formula_info["agg"]
            out = getattr(np, aggregation)(results, axis=1)

        time_aggregation = request.time_aggregation
        value = getattr(np, time_aggregation)(out)

        response = RealTimeKPIResponse(label=str(datetime.now()), value=value)

        return response

    async def stop(self):
        try:
            if self.consumer:
                await self.consumer.stop()

            response = requests.get(
                "http://data-preprocessing-container:8003/real-time/stop",
            )
            response.raise_for_status()

            await delete_kafka_topic(self._topic, f"{self._servers}:{self._port}")

        except Exception as e:
            print(f"Error stopping connections: {e}")
