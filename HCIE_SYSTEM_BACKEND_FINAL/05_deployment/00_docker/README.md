# HCIE System Docker Configuration

## Overview

This directory contains all Docker-related files for the HCIE System.

## Files

- **Dockerfile** - Main container definition
- **docker-compose.yml** - Default development setup
- **docker-compose.dev.yml** - Development environment
- **docker-compose.prod.yml** - Production environment
- **.dockerignore** - Files to exclude from container

## Usage

### Development
```bash
# Start development environment
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose -f docker-compose.dev.yml logs -f api

# Stop environment
docker-compose -f docker-compose.dev.yml down
```

### Production
```bash
# Start production environment
docker-compose -f docker-compose.prod.yml up -d

# Scale API services
docker-compose -f docker-compose.prod.yml up -d --scale api=3

# Stop environment
docker-compose -f docker-compose.prod.yml down
```

### Default (Current Setup)
```bash
# Start default setup
docker-compose up -d

# Rebuild API container
docker-compose up -d --build api

# View all services
docker-compose ps
```

## Environment Variables

The system automatically detects environment via `ENVIRONMENT` variable:

- `development` - Uses development settings
- `production` - Uses production settings  
- `testing` - Uses testing settings
- `docker` - Uses Docker settings (default)

## Service Architecture

### API Service
- **Development**: Hot reload with `--reload`
- **Production**: Gunicorn with multiple workers
- **Ports**: 8001 (dev), 8000 (prod)

### Database Services
- **Redis**: In-memory caching and session storage
- **PostgreSQL**: Primary data storage
- **Kafka**: Event streaming (Redpanda)

### Development Tools
- **Adminer**: Database admin UI (port 8081)
- **Nginx**: Load balancer (production only)

## Volumes

- **Development**: `*_dev_data` volumes
- **Production**: `*_prod_data` volumes
- **Persistent**: All data survives container restarts

## Networking

All services communicate via the `hcie-net` bridge network.
Service names are used for inter-service communication:
- `api` - HCIE API service
- `redis` - Redis cache
- `postgres` - PostgreSQL database
- `kafka` - Kafka/Redpanda broker

## Health Checks

The API container includes a health check that tests:
- `/health` endpoint
- Database connectivity
- Service availability

## Security

- Non-root user (`hcie`) in containers
- Minimal base image (`python:3.9-slim`)
- Environment-specific configurations
- Resource limits in production
