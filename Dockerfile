FROM python:3.10

# Configure Poetry
ENV POETRY_VERSION=1.8.4
ENV POETRY_HOME=/opt/poetry
ENV POETRY_VENV=/opt/poetry-venv
ENV POETRY_CACHE_DIR=/opt/.cache

# Install poetry separated from system interpreter
RUN python3 -m venv $POETRY_VENV \
    && $POETRY_VENV/bin/pip install -U pip setuptools \
    && $POETRY_VENV/bin/pip install poetry==${POETRY_VERSION}

# Add `poetry` to PATH
ENV PATH="${PATH}:${POETRY_VENV}/bin"

# Set the working directory to the root of the project (where poetry.lock and pyproject.toml are located)
WORKDIR /kpi-engine

# Copy poetry lock and pyproject toml files into the container's working directory
COPY poetry.lock pyproject.toml /kpi_engine/

# Install dependencies (this uses poetry.lock and pyproject.toml)
RUN poetry install

# Copy the rest of the application code from the src directory into the container
COPY ./src/main/kpi_engine /kpi_engine/

# Command to run the application
CMD ["poetry", "run", "python", "app.py"]
