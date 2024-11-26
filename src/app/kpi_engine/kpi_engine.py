"""KPI Calculation Engine."""

from src.app.kpi_engine.kpi_request import KPIRequest
from src.app.kpi_engine.kpi_response import KPIResponse
import src.app.kpi_engine.dynamic_calc as dyn
import src.app.kpi_engine.exceptions as exceptions

import KB.kb_interface as kbi


class KPIEngine:
    @staticmethod
    def compute(connection, request: KPIRequest) -> KPIResponse:

        # still to define a way to start the KB on the application start and not on the request
        kbi.start()

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
            result = dyn.dynamic_kpi(
                formulas[name], formulas, partial_result, connection, request
            )
        except Exception as e:
            return KPIResponse(message=repr(e), value=-1)

        # aggregated on time
        result = dyn.finalize_mo(result, partial_result, request.time_aggregation)

        message = (
            f"The {aggregation} of KPI {name} for machines {machines} with operations {operations} "
            f"from {start_date} to {end_date} is {result}"
        )

        print(message)

        insert_aggregated_kpi(
            connection=connection,
            request=request,
            kpi_list=formulas.keys(),
            value=result,
        )

        return KPIResponse(message=message, value=result)


def preprocessing(kpi_name, formulas_dict):

    partial_result = {}
    # get the actual formula of the kpi
    kpi_formula = formulas_dict[kpi_name]
    # get the variables of the aggregation
    search_var = kpi_formula.split("°")
    # split because we always have [ after the last match of the aggregation
    aggregation_variables = search_var[2].split("[")
    partial_result["var"] = aggregation_variables[0]
    partial_result["agg"] = search_var[1]
    return partial_result


def insert_aggregated_kpi(connection, request: KPIRequest, kpi_list: list, value):
    cursor = connection.cursor()

    
   
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

    print(data)

    
    cursor.execute(insert_query, data)

    
    connection.commit()

    
    cursor.close()
    connection.close()



def get_kpi_formula(name: str):
    formulas = kbi.get_formulas(name)
    if formulas is None:
        raise exceptions.InvalidKPINameException()
    return formulas
