FROM python:3.10

# Configure Poetry
ENV POETRY_VERSION=1.8.4
ENV POETRY_HOME=/opt/poetry
# Poetry cache directory: it should be accessible by non-root users
ENV POETRY_CACHE_DIR="/kpi_engine/.cache/pypoetry"
ENV POETRY_VIRTUALENVS_CREATE=false
# For having consistent imports
ENV PYTHONPATH=/kpi_engine/src
ENV RUNNING_IN_DOCKER=True


# Upgrade pip
RUN pip install --upgrade pip

# Install Poetry
RUN pip install poetry==${POETRY_VERSION}

# Create a non-root user for security reasons (trivy - DS002)
RUN groupadd -r appgroup && useradd -r -g appgroup KPIEngineAdmin

# Create the application directory
RUN mkdir -p /kpi_engine/.cache/pypoetry && \
    chown -R KPIEngineAdmin:appgroup /kpi_engine

# Set the working directory
WORKDIR /kpi_engine

# Copy dependency files and installclear dependencies
COPY poetry.lock pyproject.toml /kpi_engine/

# Install dependencies
RUN poetry install

# Copy the rest of the application code
COPY src/ /kpi_engine/src

# Change ownership of the application code
RUN chown -R KPIEngineAdmin:appgroup /kpi_engine

# Expose port 8008
EXPOSE 8008

# Set the non-root user password
RUN echo "KPIEngineAdmin:password" | chpasswd

# Change to non-root user
USER KPIEngineAdmin

# Run the application
CMD ["poetry", "run", "start"]

# Periodic healthcheck to ensure the container is running
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8008/health || exit 1
