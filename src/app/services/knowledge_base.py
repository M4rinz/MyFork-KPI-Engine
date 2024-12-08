import requests

from src.app.models import exceptions


def get_kpi_formula(name: str) -> dict[str, str]:
    response = requests.get(
        "http://kb-service-container:8001/kpi-formulas", params={"kpi": name}, timeout=5
    )
    if response.status_code != 200:
        raise exceptions.KPIFormulaNotFoundException()
    response = response.json()
    return response["formulas"]


def get_closest_kpi_formula(name: str) -> dict:
    response = requests.get(
        "http://kb-service-container:8001/kpi-formulas", params={"kpi": name}, timeout=5
    )
    if response.status_code != 200:
        raise exceptions.KPIFormulaNotFoundException()
    return response.json()


def get_closest_instances(name: str) -> dict:
    response = requests.get(
        "http://kb-service-container:8001/class-instances",
        params={"owl_class_label": name},
        timeout=5,
    )
    if response.status_code != 200:
        raise exceptions.KPIFormulaNotFoundException()
    return response.json()
