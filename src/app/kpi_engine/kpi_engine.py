"""KPI Calculation Engine."""

import asyncio
import json

import numpy as np
import requests
import websockets
from src.app.kpi_engine.kpi_request import (
    KPIRequest,
    RealTimeRequest,
    RealTimeKPI,
    KPIStreamingRequest,
)
from src.app.kpi_engine.kpi_response import KPIResponse, RealTimeKPIResponse
import src.app.kpi_engine.dynamic_calc as dyn
import src.app.kpi_engine.exceptions as exceptions

from typing import Any

from aiokafka import AIOKafkaConsumer


class KPIEngine:
    instance = None

    def __init__(self, topic, port, servers) -> None:
        self._topic = topic
        self._port = port
        self._servers = servers
        self.consumer = KPIEngine.create_consumer(topic, port, servers)
        self.websocket = None
        # self.websocket = KPIEngine.create_websocket()
        KPIEngine.instance = self
        print(
            "KPI Engine initialized: created consumer. Topic: ",
            topic,
            " Port: ",
            port,
            " Servers: ",
            servers,
        )

    @staticmethod
    def create_consumer(topic, port, servers):
        def decode_message(message):
            return [
                RealTimeKPI.from_json(json.loads(item))
                for item in json.loads(message.decode("utf-8"))
            ]

        return AIOKafkaConsumer(
            topic,
            bootstrap_servers=f"{servers}:{port}",
            value_deserializer=decode_message,
            auto_offset_reset="earliest",
        )

    async def start_consumer(self):
        try:
            await self.consumer.start()
            print("Consumer started successfully")
        except Exception as e:
            print(f"Error starting consumer: {e}")
            return {"Error": f"Error starting consumer: {str(e)}"}

    @staticmethod
    def connect_to_publisher(kpi_streaming_request: KPIStreamingRequest):
        try:
            print("Streaming request: ", kpi_streaming_request.to_json())
            response = requests.post(
                "http://data-preprocessing-container:8003/real-time/start",
                data=kpi_streaming_request.to_json(),
            )
            response.raise_for_status()  # Raise error for non-2xx responses
            return response.json()
        except Exception as e:
            print(f"Error connecting to producer: {e}")
            return {"Error": "Could not connect to producer"}

    @staticmethod
    def create_websocket():
        """
        Establishes a connection to the GUI via WebSocket.
        """
        try:
            websocket_url = "ws://gui-container:8004/kpi-updates"
            websocket = asyncio.run(websockets.connect(websocket_url))
            print("Connected to GUI WebSocket at:", websocket_url)
            return websocket
        except Exception as e:
            print(f"Error connecting to GUI WebSocket: {e}")
            return None

    async def consume(self, request: RealTimeRequest, stop_event):
        try:
            print("consuming")
            while not stop_event.is_set():
                # get the last message from the topic
                real_time_kpis = (await self.consumer.getone()).value
                print("Consumed message: ", real_time_kpis)

                # compute real time kpis
                result = self.compute_real_time(real_time_kpis, request)
                print(result)

                # send the computed result to the GUI via websocket

        except Exception as e:
            print("Error in consumer: ", e)
        finally:
            await self.consumer.stop()

    def compute_real_time(
        self, real_time_kpis: list[RealTimeKPI], request: RealTimeRequest
    ):
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

            if self.websocket:
                await self.websocket.close()
                print("WebSocket connection closed.")

            response = requests.get(
                "http://data-preprocessing-container:8003/real-time/stop",
            )
            response.raise_for_status()

        except Exception as e:
            print(f"Error stopping connections: {e}")

    @staticmethod
    def compute(request: KPIRequest) -> KPIResponse:

        name = request.name
        machines = request.machines
        operations = request.operations

        # validate machines and operations
        if len(machines) != len(operations):
            return KPIResponse(
                message="Invalid number of machines and operations", value=-1
            )

        # get the formula from the KB
        try:
            formulas = get_kpi_formula(name)
        except Exception as e:
            return KPIResponse(message=repr(e), value=-1)

        start_date = request.start_date
        end_date = request.end_date
        aggregation = request.time_aggregation

        # inits the kpi calculation by finding the outermost aggregation and involved aggregation variables
        partial_result = preprocessing(name, formulas)

        try:
            # computes the final matrix that has to be aggregated for mo and time_aggregation
            result = dyn.dynamic_kpi(formulas[name], formulas, partial_result, request)
        except Exception as e:
            return KPIResponse(message=repr(e), value=-1)

        print(result)

        # aggregated on time
        result = dyn.finalize_mo(result, partial_result, request.time_aggregation)

        message = (
            f"The {aggregation} of KPI {name} for machines {machines} with operations {operations} "
            f"from {start_date} to {end_date} is {result}"
        )

        insert_aggregated_kpi(
            request=request,
            kpi_list=formulas.keys(),
            value=result,
        )

        return KPIResponse(message=message, value=result)


def preprocessing(kpi_name: str, formulas_dict: dict[str, Any]) -> dict[str, Any]:
    partial_result = {}
    # get the actual formula of the kpi
    kpi_formula = formulas_dict[kpi_name]
    # get the variables of the aggregation
    search_var = kpi_formula.split("°")
    # split because we always have [ after the last match of the aggregation
    aggregation_variables = search_var[2].split("[")
    partial_result["agg_outer_vars"] = aggregation_variables[0]
    partial_result["agg"] = search_var[1]
    return partial_result


def insert_aggregated_kpi(
    request: KPIRequest,
    kpi_list: list,
    value: np.float64,
):
    insert_query = """
        INSERT INTO aggregated_kpi (name, aggregated_value, begin_datetime, end_datetime, kpi_list, operations, machines, step)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
    """

    data = (
        request.name,
        value.item(),
        str(request.start_date),
        str(request.end_date),
        list(kpi_list),
        request.operations,
        request.machines,
        request.step,
    )

    return requests.post(
        "http://smart-database-container:8002/insert",
        json={"statement": insert_query, "data": data},
        timeout=5,
    )


def get_kpi_formula(name: str) -> dict[str, str]:
    response = requests.get(
        "http://kb-service-container:8001/kpi-formulas", params={"kpi": name}, timeout=5
    )
    if response.status_code != 200:
        raise exceptions.KPIFormulaNotFoundException()
    response = response.json()
    return response["formulas"]


def get_references(name: str) -> list[str]:
    try:
        response = get_kpi_formula(name)
        print(response)
    except exceptions.KPIFormulaNotFoundException() as e:
        print(f"Error getting KPI database references: {e}")
        return []
    # TODO: get the references from the KB
    return ["time_sum"]
