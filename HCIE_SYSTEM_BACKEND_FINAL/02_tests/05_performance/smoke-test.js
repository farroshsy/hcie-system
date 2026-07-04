// K6 Smoke Test for HCIE System
// Tests basic connectivity and core functionality

import http from 'k6/http';
import { check, sleep } from 'k6';

const BASE_URL = __ENV.TARGET_URL || 'http://gateway';

export const options = {
  stages: [
    { duration: '10s', target: 1 },   // Warm up
    { duration: '30s', target: 3 },   // Light load
    { duration: '10s', target: 0 },   // Cool down
  ],
  thresholds: {
    http_req_duration: ['p(95)<1000'], // 95% under 1s
    http_req_failed: ['rate<0.1'],     // Error rate under 10%
  },
};

export default function () {
  // Test 1: Health check
  let healthResponse = http.get(`${BASE_URL}/health`, {
    timeout: '10s',
  });
  
  check(healthResponse, {
    'health status is 200': (r) => r.status === 200,
    'health response time < 500ms': (r) => r.timings.duration < 500,
  });

  // Test 2: Dashboard endpoint (if available)
  let dashboardResponse = http.get(`${BASE_URL}/dashboard/overview`, {
    timeout: '10s',
  });
  
  check(dashboardResponse, {
    'dashboard responds': (r) => r.status < 500, // Accept 401/403 for auth
    'dashboard response time < 1000ms': (r) => r.timings.duration < 1000,
  });

  sleep(1);
}

export function handleSummary(data) {
  console.log('Smoke Test Summary:');
  console.log(`- Total requests: ${data.metrics.http_reqs.count}`);
  console.log(`- Average response time: ${data.metrics.http_req_duration.avg}ms`);
  console.log(`- 95th percentile: ${data.metrics.http_req_duration['p(95)']}ms`);
  console.log(`- Error rate: ${(data.metrics.http_req_failed.rate * 100).toFixed(2)}%`);
}
