# HCIE Performance Testing with K6

This directory contains performance testing scripts for the HCIE system using K6 load testing tool.

## 🚀 Quick Start

### 1. Start K6 Container
```bash
docker-compose --profile load-testing up -d k6
```

### 2. Run Smoke Test (Basic Connectivity)
```bash
docker-compose exec hcie-load-test k6 run /scripts/smoke-test.js
```

### 3. Run Full Load Test (Realistic Usage)
```bash
docker-compose exec hcie-load-test k6 run /scripts/api-load-test.js
```

### 4. Stop K6 Container
```bash
docker-compose stop k6
```

## 📋 Available Tests

### 🧪 smoke-test.js
**Purpose**: Basic connectivity and health check
- Tests gateway connectivity
- Verifies API endpoints are accessible
- Light load (1-3 users)
- Quick validation (2 minutes)

**Use Case**: Pre-deployment validation, basic health checks

### 🧪 api-load-test.js
**Purpose**: Realistic user load testing
- Simulates complete user journey
- Tests learning endpoints under load
- Medium load (up to 25 users)
- Comprehensive testing (13 minutes)

**Use Case**: Performance validation, load testing before releases

## 📊 Test Scenarios

### Scenario 1: Smoke Test
```bash
# Quick health check
docker-compose exec hcie-load-test k6 run /scripts/smoke-test.js --vus 1 --duration 30s
```

### Scenario 2: Load Test
```bash
# Full load test with custom parameters
docker-compose exec hcie-load-test k6 run /scripts/api-load-test.js --vus 10 --duration 5m
```

### Scenario 3: Stress Test
```bash
# High load stress test
docker-compose exec hcie-load-test k6 run /scripts/api-load-test.js --vus 50 --duration 10m
```

## 🔧 Configuration

### Environment Variables
- `TARGET_URL`: Gateway URL (default: http://gateway)
- `OTEL_EXPORTER_OTLP_ENDPOINT`: OpenTelemetry collector

### Custom Test Parameters
```bash
# Override default options
docker-compose exec hcie-load-test k6 run /scripts/api-load-test.js \
  --vus 20 \
  --duration 10m \
  --out json=results.json
```

## 📈 Monitoring Results

### Grafana Dashboard
Access Grafana at `http://localhost:3000` (admin/admin123) to view:
- Request rates and response times
- Error rates and performance metrics
- OpenTelemetry traces (if configured)

### Dozzle Logs
Access Dozzle at `http://localhost:9999` (admin/admin123) to view:
- Real-time API logs during tests
- Error messages and debugging info
- System resource utilization

## 📊 Metrics & Thresholds

### Performance Targets
- **Response Time**: 95% under 800ms
- **Error Rate**: Under 5%
- **Throughput**: Varies by test type

### Custom Metrics
- `errors`: Custom error rate tracking
- Request timing distributions
- Endpoint-specific performance

## 🎯 Test Data

### Simulated User Behavior
- **Task Requests**: Users asking for learning content
- **Answer Submissions**: Users completing learning activities
- **Dashboard Views**: Users checking progress
- **Think Time**: 2-5 seconds between actions (realistic)

### Test Data Generation
- Random task IDs for testing
- Variable response times (3-13 seconds)
- Random answer correctness (70% correct rate)
- Realistic user engagement patterns

## 🔍 Troubleshooting

### Common Issues

#### Container Not Running
```bash
# Check container status
docker-compose ps | grep k6

# Restart container
docker-compose restart k6
```

#### Gateway Connection Issues
```bash
# Test gateway connectivity
docker-compose exec hcie-load-test curl -I http://gateway/health

# Check network connectivity
docker network ls | grep hcie
```

#### Test Failures
```bash
# Check logs during test
docker-compose logs -f k6

# Verify API endpoints are accessible
curl -I http://localhost:80/health
```

### Performance Issues

#### High Response Times
- Check system resources with `docker stats`
- Monitor API container logs
- Verify database connections

#### Memory Issues
- Reduce virtual users (`--vus`)
- Shorten test duration
- Check container memory limits

## 📝 Custom Tests

### Creating New Tests
1. Create new `.js` file in `performance-tests/`
2. Import K6 modules:
```javascript
import http from 'k6/http';
import { check, sleep } from 'k6';
```
3. Define options and thresholds:
```javascript
export const options = {
  stages: [
    { duration: '2m', target: 10 },
    { duration: '5m', target: 10 },
    { duration: '2m', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'],
  },
};
```
4. Implement test logic
5. Run with: `docker-compose exec hcie-load-test k6 run /scripts/your-test.js`

### Best Practices
- Use realistic think times
- Test complete user journeys
- Monitor system resources
- Set appropriate thresholds
- Log custom metrics for analysis

## 🚨 Important Notes

1. **Authentication**: Tests use basic endpoints - ensure auth system handles anonymous requests appropriately
2. **Data Impact**: Load tests create real learning data - consider using test users or cleanup procedures
3. **Resource Usage**: Monitor system resources during tests to avoid impacting other services
4. **Network**: K6 runs in Docker network - ensure gateway accessibility from container
5. **Environment**: Adjust `TARGET_URL` for different deployment environments

## 📚 Additional Resources

- [K6 Documentation](https://k6.io/docs/)
- [K6 JavaScript API](https://k6.io/docs/javascript-api/)
- [Performance Testing Best Practices](https://k6.io/docs/test-types/performance-testing/)
- [Grafana K6 Integration](https://grafana.com/docs/grafana-cloud/integrations/integration-reference/k6/)
