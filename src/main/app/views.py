""" Views to handle API requests."""

from django.http import JsonResponse
from .services.kpi_engine import KPIEngine
from .services.kpi_request import KPIRequest

from django.views.decorators.http import require_GET
from datetime import datetime


@require_GET
def calculate_kpi(request, name):

    machine = request.GET.get("machine")
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")

    # Validate date format (YYYY-MM-DD)
    try:
        if start_date:
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
        if end_date:
            end_date = datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        return JsonResponse(
            {"error": "Invalid date format. Use YYYY-MM-DD."}, status=400
        )

    details = KPIRequest(name, machine, start_date, end_date)
    result = KPIEngine.compute(details=details)

    return JsonResponse(result)
