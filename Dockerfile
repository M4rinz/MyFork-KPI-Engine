FROM python:3.10

# Configure Poetry
ENV POETRY_VERSION=1.8.4
ENV POETRY_HOME=/opt/poetry
ENV POETRY_CACHE_DIR="/root/.cache/pypoetry"
ENV POETRY_VIRTUALENVS_CREATE=false

# Install Poetry
RUN pip install poetry==${POETRY_VERSION}

# Set the working directory
WORKDIR /kpi_engine


# Copy dependency files and install dependencies
COPY poetry.lock pyproject.toml /kpi_engine/


RUN poetry install --no-dev --no-root

# Copy the rest of the application code
COPY ./src/ /kpi_engine/

# Expose port 8000
EXPOSE 8000

# Run the application
CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
