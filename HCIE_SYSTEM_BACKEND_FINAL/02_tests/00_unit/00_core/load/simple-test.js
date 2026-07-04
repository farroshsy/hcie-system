// Simple K6 Test for HCIE API
// Basic connectivity test

import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '30s', target: 5 },   // Ramp up to 5 users
    { duration: '1m', target: 5 },    // Stay at 5 users
    { duration: '30s', target: 0 },   // Ramp down
  ],
};

const BASE_URL = 'http://api:8000';

export default function () {
  // Simple health check
  let response = http.get(`${BASE_URL}/health`, {
    timeout: '10s',
  });
  
  check(response, {
    'health status is 200': (r) => r.status === 200,
    'health response time < 1000ms': (r) => r.timings.duration < 1000,
  });
  
  sleep(1);
}
