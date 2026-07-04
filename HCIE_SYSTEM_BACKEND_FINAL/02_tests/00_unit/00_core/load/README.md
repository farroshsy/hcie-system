# HCIE Load Testing with K6

This directory contains load testing scripts for the HCIE system using K6.

## 🚀 Quick Start

### 1. Start K6 (with load testing profile)
```bash
docker-compose --profile load-testing up -d k6
```

### 2. Run Basic API Load Test
```bash
docker-compose exec k6 k6 run /scripts/api-load-test.js
```

### 3. Run Weight Optimization Test
```bash
docker-compose exec k6 k6 run /scripts/weight-optimization-test.js
```

### 4. Stop K6
```bash
docker-compose stop k6
```

## 📋 Available Tests

### 1. `api-load-test.js`
**Purpose**: Tests all major API endpoints under load
- Dashboard endpoint (READ mode)
- Learning endpoint (WRITE mode)
- Next task endpoint
- Concurrent user simulation

**Load Pattern**:
- 2m: Ramp up to 10 users
- 5m: Stay at 10 users
- 2m: Ramp up to 50 users
- 5m: Stay at 50 users
- 2m: Ramp down

**Thresholds**:
- 95% of requests < 500ms
- Error rate < 10%

### 2. `weight-optimization-test.js`
**Purpose**: Specifically tests the mathematical weight optimization under load
- Focuses on Jₜ calculation performance
- Tests Σ⁻¹μ optimization stability
- Monitors ensemble variance calculations

**Load Pattern**:
- 1m: Warm up with 5 users
- 3m: Load test with 20 users
- 1m: Cool down

**Thresholds**:
- Weight optimization < 200ms (95th percentile)
- Jₜ calculation < 100ms (95th percentile)
- Optimization error rate < 5%

## 📊 Metrics Collection

K6 is configured to send metrics to Prometheus:
- URL: `http://prometheus:9090/api/v1/write`
- Custom metrics for optimization performance
- Error rate tracking
- Response time distributions

## 🔧 Configuration

### Environment Variables
- `K6_PROMETHEUS_RW_SERVER_URL`: Prometheus write endpoint
- `BASE_URL`: API endpoint (http://api:8000)

### Test Data
- Uses randomized concept IDs from K-12 CS framework
- Simulates realistic user interactions
- Tests both correct and incorrect answers
- Variable response times and engagement levels

## 📈 Monitoring Results

### Grafana Dashboard
Access Grafana at `http://localhost:3000` (admin/admin123) to view:
- Request rates and response times
- Error rates and thresholds
- Custom optimization metrics
- System resource utilization

### Dozzle Logs
Access Dozzle at `http://localhost:9999` (admin/admin123) to view:
- Real-time API logs
- Weight optimization calculations
- Error messages and debugging info

## 🎯 Test Scenarios

### Scenario 1: Normal Load
- Simulates typical user behavior
- Mix of READ and WRITE operations
- Realistic think times between requests

### Scenario 2: Stress Test
- High concurrency (50+ users)
- Rapid successive requests
- Tests system limits and degradation

### Scenario 3: Mathematical Load
- Focus on weight optimization performance
- Tests Jₜ calculation stability
- Validates ensemble variance calculations

## 🚨 Important Notes

1. **Authentication**: Tests use `Bearer test-token` - ensure auth system handles this
2. **Data Impact**: Load tests create real learning data - consider using test users
3. **Resource Usage**: Monitor system resources during tests
4. **Network**: K6 runs in Docker network - ensure API accessibility

## 📝 Customization

### Adding New Tests
1. Create new `.js` file in `tests/load/`
2. Follow existing patterns for metrics and thresholds
3. Test with `docker-compose exec k6 k6 run /scripts/your-test.js`

### Modifying Load Patterns
Edit the `stages` configuration in each script:
```javascript
stages: [
  { duration: '2m', target: 10 },   // 2 minutes, ramp to 10 users
  { duration: '5m', target: 50 },   // 5 minutes, stay at 50 users
],
```

### Custom Metrics
Add custom metrics for specific measurements:
```javascript
import { Trend, Rate } from 'k6/metrics';
const customMetric = new Trend('custom_metric_name');
```
