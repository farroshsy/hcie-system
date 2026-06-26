#!/bin/bash

# Production Infrastructure Setup Script
# Sets up Kafka, Schema Registry, Debezium, and Monitoring

echo "=== HCIE Production Infrastructure Setup ==="

# Create network if it doesn't exist
docker network create hcie-net 2>/dev/null || echo "Network hcie-net already exists"

# Start production infrastructure
echo "Starting production infrastructure..."
docker-compose -f docker-compose.production.yml up -d

# Wait for services to be ready
echo "Waiting for services to start..."
sleep 30

# Check if services are running
echo "Checking service health..."
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Setup Debezium connector
echo "Setting up Debezium connector..."
sleep 10

# Register the Debezium connector
curl -X POST -H "Content-Type: application/json" \
  http://localhost:8083/connectors \
  -d @../monitoring/debezium-connector.json

echo "=== Setup Complete ==="
echo "Services available at:"
echo "  - API: http://localhost:8001"
echo "  - Kafka UI: http://localhost:8080"
echo "  - Schema Registry: http://localhost:8081"
echo "  - Kafka Connect: http://localhost:8083"
echo "  - Prometheus: http://localhost:9090"
echo "  - Grafana: http://localhost:3000 (admin/admin)"
echo ""
echo "=== Monitoring Endpoints ==="
echo "  - API Metrics: http://localhost:8001/metrics"
echo "  - Prometheus: http://localhost:9090"
echo "  - Grafana Dashboards: http://localhost:3000"
echo ""
echo "=== Kafka Topics ==="
echo "  - hcie.tasks"
echo "  - hcie.submissions" 
echo "  - hcie.mastery"
echo "  - postgres.public.interactions (CDC)"
echo "  - postgres.public.users (CDC)"
echo "  - postgres.public.concepts (CDC)"
