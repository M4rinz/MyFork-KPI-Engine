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

        # in self dobbiamo mettere i risulati parziali
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
        if response is None:
            # here i get the reference from the KB with the other method
            response= get_closest_kpi_formula(name)
            response= response['formulas']

        #funzione che ritorna la formula pulita 
        formulas,operazioni = clean_placeholders(input_formulas)
        #i take the first key
        formula_name = next(iter(my_dict))
        formula = formulas[formula_name]
        # torna un dizionario dove la chiave 'formula' ha la formula trasformata, agg è l'aggregazione mo da 
        # applicare e operazioni che sara sempre una stringa vuota tranne se nella formula ci sono idle working o offline
        result = transform_formula(formula,formulas,operazioni)

        # prende la lista di occorenze di kpi nella formula da mandare al gruppo 3
        involved_kpi=extract_names(result['formula'])
        
    except exceptions.KPIFormulaNotFoundException() as e:
        print(f"Error getting KPI database references: {e}")
        return []
    # TODO: get the references from the KB as a list

    # return involved_kpi,result
    return ["time_sum"],result #adesso ritona questa lista perchè gruppo 3 non pronto


#formula = formulas[formula_name]
# formulas ==dizionario
def transform_formula(formula, formulas,operatIWO):

    result={}

    #substitution of the R references with their formula
    formula = re.sub(r'R°(\w+)', lambda match: f"{formulas[match.group(1)]}", formula)
    formula = re.sub(r'D°(\w+)', r'\1', formula)

    
    #looking for all the aggregations and remove them
    formula=''.join(formula.split())
    result['formula']=formula
    result['operations_f']=operatIWO
    result=remove_agg(result)

    # then if in the formula there are pairwise operation then transform in a parsable formula
    result['formula'] = transform_expression_recursive(result['formula'])
    return result

# this clean the formulas that we get from the KB
def clean_placeholders(formulas):
    cleaned_formulas = {}
    operations = []

    # Itera attraverso ogni formula per la pulizia
    for key, formula in formulas.items():
        
        # Cerca e rimuovi i placeholder specifici
        if '°T°m°idle°' in formula:
            operations.append('idle')
            formula = formula.replace('°T°m°idle°', '')

        if '°T°m°working°' in formula:
            operations.append('working')
            formula = formula.replace('°T°m°working°', '')

        if '°T°m°offline°' in formula:
            operations.append('offline')
            formula = formula.replace('°T°m°offline°', '')

        if '°T°M°idle°' in formula:
            operations.append('idle')
            formula = formula.replace('°T°M°idle°', '')

        if '°T°M°working°' in formula:
            operations.append('working')
            formula = formula.replace('°T°M°working°', '')

        if '°T°M°offline°' in formula:
            operations.append('offline')
            formula = formula.replace('°T°M°offline°', '')

        # Rimuovi gli altri placeholder
        formula = re.sub(r'°t°m°o°', '', formula)
        formula = re.sub(r'°T°m°o°', '', formula)

        # Salva la formula pulita
        cleaned_formulas[key] = formula.strip()

    return cleaned_formulas, operations


# we remouve the aggregations
def remove_agg(result):

    formula=result['formula']

    formula = re.sub(r'°t', '', formula)
    formula = re.sub(r'°mo', '', formula)
    formula = re.sub(r'A°m', 'A°M', formula)
    formula = re.sub(r'°m', '', formula)

    indice=float('inf')

    agg_functions = ['A°sum[', 'A°Mean[', 'A°max[', 'A°Min[', 'A°var[', 'A°std[']
    first_aggregation = None  # Variabile per salvare la prima aggregazione trovata

    while any(agg_func in formula for agg_func in agg_functions):
        # Trova la posizione di apertura della prima occorrenza di una funzione di aggregazione
        for agg_func in agg_functions:
            start_index = formula.find(agg_func)
            if start_index != -1:
                # Salva il nome della prima aggregazione trovata
                if first_aggregation is None or start_index < indice:
                    indice=start_index
                    first_aggregation = agg_func.strip('A°[').lower()  # Salva il nome in minuscolo
                break
        
        # We interrup immediatly if we don't find anything
        if start_index == -1:
            break
        
        # we initialize a counter for the [ and ] in particular we increase if we find a [ and decrease if ] so we 
        # delete the aggregation and the corrisponding []
        depth = 1
        end_index = start_index + len(agg_func)
        
        # Here the implementation of the logic explained before
        for i, char in enumerate(formula[start_index + len(agg_func):]):
            if char == '[':
                depth += 1
            elif char == ']':
                depth -= 1
            
            if depth == 0:
                end_index = start_index + len(agg_func) + i
                break
        
        # here we check if the ] is the last char of the formula then we return a new expression that star from
        #  the next char after A°aggr[ and end at the last char before the ] and we have two cases :
        # the first if the ] is at the end of the expression
        # the second if th ] is in the middle of the expression
        if (len(formula)-1) == end_index:
            formula = formula[:start_index] + formula[start_index + len(agg_func):end_index]
        else:
            formula = formula[:start_index] + formula[start_index + len(agg_func):end_index] + formula[end_index+1:]
        
        # remove extra space
        formula = ''.join(formula.split())


    result['formula']=formula
    result['agg']=first_aggregation
    return result



def transform_expression_recursive(expression):

    # Map of the possible operator that we can find
    operator_map = ['S°/', 'S°*', 'S°+', 'S°-', 'S°**']

    #we check for the possible S° operator and we start from the outer one
    while any(op in expression for op in operator_map):
        for op in operator_map:
            start_index = expression.find(op + '[')
            print(start_index)
            if start_index != -1:
                break

        # if we don't find an operator    
        if start_index == -1:
            break

        # we initialize a counter for the  []parentesis in increase the counter by one if we find [ and decrease
        # by one if we find a ] so when we find a ; and counter ==1 we sobstitute it with the operator and then
        # we put () instead []
        depth = 1
        end_index = start_index + len(op) + 1  # Dopo l'apertura della parentesi quadra
        semicolon_index = None

        for i, char in enumerate(expression[start_index + len(op) + 1:], start=start_index + len(op) + 1):
            if char == '[':
                depth += 1
            elif char == ']':
                depth -= 1
            elif char == ';' and depth == 1:
                semicolon_index = i
            
            if depth == 0:
                end_index = i
                break

        # sobstitute the most internal block with the operator
        if semicolon_index is not None:
            # substitute the ; with the operator
            expression = (
                expression[:start_index] +
                '(' +
                expression[start_index + len(op) + 1:semicolon_index] +
                f' {op[2]} ' +  # Usa il simbolo dell'operatore
                expression[semicolon_index + 1:end_index] +
                ')' +
                expression[end_index + 1:]
            )

    # if there is a 100 then clean it
    expression = expression.replace('C°100°', '100')
    return expression.strip()


def extract_names(expression):
    # Pattern to find valide namesi: letters, numbers and underscore
    pattern = re.compile(r'\b[a-zA-Z_]\w*\b')  # we don't mach pure numbers
    names = pattern.findall(expression)

    # we exclude the 100 value
    filtered_names = [name for name in names if name != "100"]
    return filtered_names
