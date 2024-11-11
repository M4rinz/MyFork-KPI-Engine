# src/main/kpis/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path(
        "<str:name>/", views.calculate_kpi, name="calculate_kpi"
    ),  # Endpoint for KPI calculation
]
