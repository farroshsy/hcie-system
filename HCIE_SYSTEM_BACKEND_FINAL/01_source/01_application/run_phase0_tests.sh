#!/bin/bash

# Phase 0 End-to-End Test Runner
# Tests the complete event system with real Kafka

set -e

echo "🚀 Starting Phase 0 End-to-End Tests"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker first."
    exit 1
fi

print_status "Docker is running ✓"

# Check if we're in the right directory
if [ ! -f "docker/docker-compose.production.yml" ]; then
    print_error "Please run this script from the HCIE_SYSTEM_BACKENDV2 directory"
    exit 1
fi

print_status "In correct directory ✓"

# Stop any existing containers
print_warning "Stopping existing containers..."
docker-compose -f docker/docker-compose.production.yml down -v

# Clean up any orphaned containers
print_warning "Cleaning up orphaned containers..."
docker system prune -f

# Start the infrastructure
print_status "Starting infrastructure..."
docker-compose -f docker/docker-compose.production.yml up -d postgres redis kafka schema-registry

# Wait for infrastructure to be ready
print_status "Waiting for infrastructure to be ready..."

# Wait for PostgreSQL
print_status "Waiting for PostgreSQL..."
until docker-compose -f docker/docker-compose.production.yml exec -T postgres pg_isready -U hcie_user -d hcie; do
    echo "PostgreSQL is unavailable - sleeping"
    sleep 2
done

# Wait for Redis
print_status "Waiting for Redis..."
until docker-compose -f docker/docker-compose.production.yml exec -T redis redis-cli ping; do
    echo "Redis is unavailable - sleeping"
    sleep 2
done

# Wait for Kafka
print_status "Waiting for Kafka..."
until docker-compose -f docker/docker-compose.production.yml exec -T kafka kafka-broker-api-versions --bootstrap-server localhost:9092; do
    echo "Kafka is unavailable - sleeping"
    sleep 5
done

# Wait for Schema Registry
print_status "Waiting for Schema Registry..."
until curl -f http://localhost:8081/subjects; do
    echo "Schema Registry is unavailable - sleeping"
    sleep 3
done

print_status "Infrastructure is ready ✓"

# Start the application services
print_status "Starting application services..."
docker-compose -f docker/docker-compose.production.yml up -d api outbox-worker auth-consumer

# Wait for API to be ready
print_status "Waiting for API to be ready..."
until curl -f http://localhost:8001/health; do
    echo "API is unavailable - sleeping"
    sleep 5
done

print_status "API is ready ✓"

# Wait for workers to start
print_status "Waiting for workers to start..."
sleep 10

# Show running containers
print_status "Running containers:"
docker-compose -f docker/docker-compose.production.yml ps

echo ""
print_status "System is ready! Running end-to-end tests..."
echo "=================================="

# Run the end-to-end tests
cd ..
python test_e2e_flow.py

# Capture test result
TEST_RESULT=$?

echo ""
echo "=================================="

if [ $TEST_RESULT -eq 0 ]; then
    print_status "🎉 Phase 0 tests PASSED! System is working correctly."
    echo ""
    print_status "Next steps:"
    echo "1. Review test results in e2e_test_results.json"
    echo "2. Check logs: docker-compose -f docker/docker-compose.production.yml logs -f"
    echo "3. Test failure scenarios: docker stop kafka && sleep 30 && docker start kafka"
    echo "4. When ready, proceed to Phase 1 (service separation)"
else
    print_error "❌ Phase 0 tests FAILED! System needs fixes."
    echo ""
    print_warning "Debugging steps:"
    echo "1. Check logs: docker-compose -f docker/docker-compose.production.yml logs -f"
    echo "2. Check Kafka topics: curl http://localhost:8080"
    echo "3. Check outbox table: docker-compose -f docker/docker-compose.production.yml exec postgres psql -U hcie_user -d hcie -c 'SELECT * FROM outbox_event_envelopes LIMIT 5;'"
    echo "4. Check Redis: docker-compose -f docker/docker-compose.production.yml exec redis redis-cli keys '*'"
fi

echo ""
print_status "To stop the system: docker-compose -f docker/docker-compose.production.yml down"

exit $TEST_RESULT
