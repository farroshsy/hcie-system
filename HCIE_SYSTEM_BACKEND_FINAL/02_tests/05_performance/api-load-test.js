// K6 API Load Test for HCIE System
// Tests the learning API endpoints under realistic load

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

const BASE_URL = __ENV.TARGET_URL || 'http://gateway';
const errorRate = new Rate('errors');
const authErrorRate = new Rate('auth_errors');

export const options = {
  stages: [
    { duration: '1m', target: 5 },    // Ramp up to 5 users
    { duration: '3m', target: 15 },   // Ramp up to 15 users
    { duration: '5m', target: 25 },   // Ramp up to 25 users
    { duration: '3m', target: 15 },   // Scale down to 15 users
    { duration: '1m', target: 0 },    // Cool down
  ],
  thresholds: {
    http_req_duration: ['p(95)<800'],  // 95% under 800ms
    http_req_failed: ['rate<0.10'],     // Allow 10% auth failures
    errors: ['rate<0.05'],              // Custom errors under 5%
    auth_errors: ['rate<0.10'],         // Custom auth errors under 10%
  },
};

export default function () {
  // Test 1: Get next task (simulates user requesting content)
  let taskResponse = http.get(`${BASE_URL}/learning/next-task`, {
    headers: {
      'Content-Type': 'application/json',
      'User-Agent': 'k6-load-test',
    },
    timeout: '10s',
  });
  
  let taskOk = check(taskResponse, {
    'task request status is 200': (r) => r.status === 200,
    'task response time < 500ms': (r) => r.timings.duration < 500,
  });
  
  // Track auth errors separately
  let taskAuthError = taskResponse.status === 401 || taskResponse.status === 403;
  authErrorRate.add(taskAuthError);
  
  // Only count as real error if not auth-related
  errorRate.add(!taskOk && !taskAuthError);

  // Test 2: Submit answer (simulates user learning interaction)
  if (taskOk && taskResponse.status === 200) {
    const taskData = taskResponse.json();
    const taskId = taskData.task_id || `test-task-${Math.random().toString(36).substr(2, 9)}`;
    
    let submitResponse = http.post(`${BASE_URL}/learning/submit`, JSON.stringify({
      task_id: taskId,
      answer: Math.random() > 0.3 ? 'true' : 'false',
      response_time: Math.random() * 10 + 3,
    }), {
      headers: {
        'Content-Type': 'application/json',
        'User-Agent': 'k6-load-test',
      },
      timeout: '10s',
    });
    
    let submitOk = check(submitResponse, {
      'submit status is 200': (r) => r.status === 200,
      'submit response time < 1000ms': (r) => r.timings.duration < 1000,
      'submit has feedback': (r) => r.json('feedback') !== undefined,
    });
    
    // Track auth errors separately
    let submitAuthError = submitResponse.status === 401 || submitResponse.status === 403;
    authErrorRate.add(submitAuthError);
    
    // Only count as real error if not auth-related
    errorRate.add(!submitOk && !submitAuthError);
  }

  // Test 3: Dashboard check (simulates user viewing progress)
  let dashboardResponse = http.get(`${BASE_URL}/dashboard/overview`, {
    headers: {
      'Content-Type': 'application/json',
      'User-Agent': 'k6-load-test',
    },
    timeout: '10s',
  });
  
  let dashboardOk = check(dashboardResponse, {
    'dashboard status is 200': (r) => r.status === 200,
    'dashboard response time < 800ms': (r) => r.timings.duration < 800,
  });
  
  // Track auth errors separately
  let dashboardAuthError = dashboardResponse.status === 401 || dashboardResponse.status === 403;
  authErrorRate.add(dashboardAuthError);
  
  // Only count as real error if not auth-related
  errorRate.add(!dashboardOk && !dashboardAuthError);

  // Realistic think time between user actions
  sleep(Math.random() * 3 + 2); // 2-5 seconds
}

export function handleSummary(data) {
  console.log('API Load Test Summary:');
  console.log(`- Total requests: ${data.metrics.http_reqs.count}`);
  console.log(`- Average response time: ${data.metrics.http_req_duration.avg}ms`);
  console.log(`- 95th percentile: ${data.metrics.http_req_duration['p(95)']}ms`);
  console.log(`- HTTP Error rate: ${(data.metrics.http_req_failed.rate * 100).toFixed(2)}%`);
  console.log(`- Auth Error rate: ${(data.metrics.auth_errors.rate * 100).toFixed(2)}%`);
  console.log(`- Custom error rate: ${(data.metrics.errors.rate * 100).toFixed(2)}%`);
}
