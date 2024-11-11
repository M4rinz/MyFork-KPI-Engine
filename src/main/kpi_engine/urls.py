# src/main/app/kpi_engine/urls.py

from django.urls import path, include

urlpatterns = [
    # delegate to the app application
    path("kpi/", include("app.urls")),
]
