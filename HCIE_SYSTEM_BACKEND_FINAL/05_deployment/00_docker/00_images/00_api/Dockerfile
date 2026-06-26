# HCIE Real System V2 Dockerfile
# Production-ready container with all dependencies

FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    librdkafka-dev \
    iputils-ping \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY config/requirements/base.txt requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# This command installs the actual OTel instrumentation hooks for your libs
RUN opentelemetry-bootstrap -a install

# Copy application code
COPY app /app/app
COPY infrastructure /app/infrastructure
COPY config /app/config
COPY core /app/core
COPY experiments /app/experiments
COPY storage /app/storage
COPY messaging /app/messaging
COPY migrations /app/migrations
COPY alembic.ini /app/alembic.ini

# Create non-root user for security and add to docker group socket access
RUN useradd -m -u 1000 hcie && \
    # Using 'groupadd -f' to handle cases where the group ID might already exist
    groupadd -f -g 999 docker && \
    usermod -aG docker hcie && \
    chown -R hcie:hcie /app

# Switch to non-root user for production
# USER hcie
# TODO: Fix Docker socket permissions for non-root user

# Expose ports
EXPOSE 8000 8501

# Health check - removed from base image, added per-service in docker-compose.yml
# Worker containers don't have HTTP servers, so they shouldn't use this healthcheck

# Updated Command to use OpenTelemetry Auto-Instrumentation
CMD ["opentelemetry-instrument", \
     "--service_name", "hcie-api", \
     "--exporter_otlp_endpoint", "http://otel-collector:4317", \
     "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]