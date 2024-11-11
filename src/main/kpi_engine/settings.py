# src/main/kpi_engine/settings.py

import os
from pathlib import Path

# Base directory of the project
BASE_DIR = Path(__file__).resolve(strict=True).parent.parent

# Security settings
# TODO: Generate a random key for the SECRET_KEY
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "TODO:GENERATE_RANDOM_KEY")
DEBUG = os.getenv("DJANGO_DEBUG", "True") == "True"
ALLOWED_HOSTS = ["*"]

# Database settings (PostgreSQL)
# TODO: Adjust the database settings as needed
DATABASES = {
    "historical_data": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": os.getenv("HISTORICAL_DATA_NAME", "HISTORICAL_DATA"),
        "USER": os.getenv("HISTORICAL_DATA_USER", "username"),
        "PASSWORD": os.getenv("HISTORICAL_DATA_PASSWORD", "password"),
        "HOST": os.getenv("HISTORICAL_DATA_HOST", "localhost"),
        "PORT": os.getenv("HISTORICAL_DATA_PORT", "5432"),
    },
    "real_time_data": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": os.getenv("REAL_TIME_DATA_NAME", "REAL_TIME_DATA"),
        "USER": os.getenv("REAL_TIME_DATA_USER", "username"),
        "PASSWORD": os.getenv("REAL_TIME_DATA_PASSWORD", "password"),
        "HOST": os.getenv("REAL_TIME_DATA_HOST", "localhost"),
        "PORT": os.getenv("REAL_TIME_DATA_PORT", "5432"),
    },
}

# Installed apps (it is not an Admin application)
INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "kpi-engine",  # The name of my app
    "rest_framework",
]

# Middleware settings (standard for Django)
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# URL configuration
ROOT_URLCONF = "kpi_engine.urls"

# NO Templates settings since we are building an API
# ----

# WSGI and ASGI application
WSGI_APPLICATION = "kpi_engine.wsgi.application"
ASGI_APPLICATION = "kpi_engine.asgi.application"
