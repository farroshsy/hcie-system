FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    docker-compose \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install requests

# Copy healer code
COPY healer.py /app/healer.py

# Set working directory
WORKDIR /app

# Run the healer
CMD ["python", "healer.py"]
