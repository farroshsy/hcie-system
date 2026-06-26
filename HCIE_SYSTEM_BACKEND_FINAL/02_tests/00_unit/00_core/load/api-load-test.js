// K6 Load Test Script for HCIE API
// Tests the critical endpoints with realistic user scenarios

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');

// Test configuration
export const options = {
  stages: [
    { duration: '2m', target: 10 },   // Ramp up to 10 users
    { duration: '5m', target: 10 },   // Stay at 10 users
    { duration: '2m', target: 50 },   // Ramp up to 50 users
    { duration: '5m', target: 50 },   // Stay at 50 users
    { duration: '2m', target: 0 },    // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'], // 95% of requests under 500ms
    http_req_failed: ['rate<0.1'],     // Error rate under 10%
    errors: ['rate<0.1'],              // Custom error rate under 10%
  },
};

const BASE_URL = 'http://api:8000';

export function setup() {
  // Setup code - create test users if needed
  console.log('Starting HCIE API load test');
}

export default function () {
  // Test 1: Dashboard Endpoint (READ mode)
  let dashboardResponse = http.get(`${BASE_URL}/dashboard/overview`, {
    headers: {
      'Authorization': 'Bearer test-token',
      'Content-Type': 'application/json',
    },
  });
  
  let dashboardOk = check(dashboardResponse, {
    'dashboard status is 200': (r) => r.status === 200,
    'dashboard response time < 500ms': (r) => r.timings.duration < 500,
    'dashboard has mastery data': (r) => r.json('mastery') !== undefined,
  });
  
  errorRate.add(!dashboardOk);

  // Test 2: Learning Endpoint (WRITE mode)
  let learningPayload = JSON.stringify({
    task_id: 'test-task-' + Math.random().toString(36).substr(2, 9),
    answer: 'true',
    response_time: Math.random() * 10 + 5,
  });
  
  let learningResponse = http.post(`${BASE_URL}/learning/submit`, learningPayload, {
    headers: {
      'Authorization': 'Bearer test-token',
      'Content-Type': 'application/json',
    },
  });
  
  let learningOk = check(learningResponse, {
    'learning status is 200': (r) => r.status === 200,
    'learning response time < 1000ms': (r) => r.timings.duration < 1000,
    'learning has feedback': (r) => r.json('feedback') !== undefined,
  });
  
  errorRate.add(!learningOk);

  // Test 3: Next Task Endpoint
  let taskResponse = http.get(`${BASE_URL}/learning/next-task`, {
    headers: {
      'Authorization': 'Bearer test-token',
      'Content-Type': 'application/json',
    },
  });
  
  let taskOk = check(taskResponse, {
    'task status is 200': (r) => r.status === 200,
    'task response time < 300ms': (r) => r.timings.duration < 300,
    'task has task_id': (r) => r.json('task_id') !== undefined,
  });
  
  errorRate.add(!taskOk);

  // Brief pause between iterations
  sleep(1);
}

export function teardown() {
  // Cleanup code
  console.log('Load test completed');
}
