FROM python:3.10

# Configure Poetry
ENV POETRY_VERSION=1.8.4
ENV POETRY_HOME=/opt/poetry
ENV POETRY_CACHE_DIR="/root/.cache/pypoetry"
ENV POETRY_VIRTUALENVS_CREATE=false
# For having consistent imports
ENV PYTHONPATH=/kpi_engine/src

# Upgrade pip
RUN pip install --upgrade pip

# Install Poetry
RUN pip install poetry==${POETRY_VERSION}

# Set the working directory
WORKDIR /kpi_engine

# Copy dependency files and installclear dependencies
COPY poetry.lock pyproject.toml /kpi_engine/

# Install dependencies
RUN poetry install --no-dev --no-root

# Copy the rest of the application code
COPY ./src/ /kpi_engine/src

# Copy local .env file for DB connection
COPY .env /kpi_engine/

COPY KB /kpi_engine/KB

# Expose port 8000
EXPOSE 8000

# Run the application
CMD ["poetry", "run", "start"]
