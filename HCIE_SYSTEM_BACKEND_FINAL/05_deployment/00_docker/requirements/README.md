# HCIE System Requirements

## Overview

This directory contains organized requirement files for different environments.

## Files

- **base.txt** - Core dependencies needed for all environments
- **development.txt** - Development tools and debugging utilities
- **production.txt** - Production-optimized dependencies with monitoring
- **testing.txt** - Testing framework and utilities

## Usage

### Development
```bash
pip install -r config/requirements/development.txt
```

### Production
```bash
pip install -r config/requirements/production.txt
```

### Testing
```bash
pip install -r config/requirements/testing.txt
```

### Docker
The Dockerfile uses `base.txt` for the container image to keep it minimal.

## Environment-Specific Packages

### Development Only
- pytest, black, flake8, mypy
- ipython, jupyter
- sphinx (documentation)

### Production Only
- prometheus-client, sentry-sdk
- gunicorn, orjson
- cryptography, python-jose
- segment-analytics

### Testing Only
- pytest-asyncio, pytest-cov, pytest-mock
- pytest-postgresql, pytest-redis
- factory-boy, faker
- locust (performance testing)
