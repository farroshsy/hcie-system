// K6 Load Test Script for Weight Optimization
// Specifically tests the mathematical optimization under load

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

// Custom metrics for weight optimization
const weightOptimizationTime = new Trend('weight_optimization_time');
const jtCalculationTime = new Trend('jt_calculation_time');
const optimizationErrorRate = new Rate('optimization_errors');

const BASE_URL = 'http://api:8000';

export const options = {
  stages: [
    { duration: '1m', target: 5 },    // Warm up with 5 users
    { duration: '3m', target: 20 },   // Load test with 20 users
    { duration: '1m', target: 0 },    // Cool down
  ],
  thresholds: {
    weight_optimization_time: ['p(95)<200'],  // Weight optimization under 200ms
    jt_calculation_time: ['p(95)<100'],       // Jₜ calculation under 100ms
    optimization_errors: ['rate<0.05'],       // Optimization error rate under 5%
  },
};

export default function () {
  const startTime = Date.now();
  
  // Test weight optimization with concurrent learning events
  const concepts = ['k2_algorithms', 'k5_algorithms', 'k8_algorithms'];
  const concept = concepts[Math.floor(Math.random() * concepts.length)];
  
  let learningPayload = JSON.stringify({
    task_id: `weight-test-${concept}-${Math.random().toString(36).substr(2, 9)}`,
    answer: Math.random() > 0.3 ? 'true' : 'false',
    response_time: Math.random() * 15 + 3,
    difficulty: Math.random() * 0.8 + 0.2,
    engagement: Math.random() * 0.4 + 0.6,
  });
  
  let response = http.post(`${BASE_URL}/learning/submit`, learningPayload, {
    headers: {
      'Authorization': 'Bearer test-token',
      'Content-Type': 'application/json',
    },
  });
  
  const endTime = Date.now();
  const responseTime = endTime - startTime;
  
  // Record custom metrics
  weightOptimizationTime.add(responseTime);
  
  let optimizationOk = check(response, {
    'optimization status is 200': (r) => r.status === 200,
    'optimization has mastery change': (r) => {
      const body = r.json();
      return body && typeof body.mastery_change === 'number';
    },
    'optimization has Jₜ value': (r) => {
      const body = r.json();
      return body && typeof body.jt_value === 'number';
    },
    'optimization response time < 500ms': (r) => r.timings.duration < 500,
  });
  
  optimizationErrorRate.add(!optimizationOk);
  
  // Log specific optimization metrics for analysis
  if (optimizationOk && response.json('jt_value')) {
    jtCalculationTime.add(response.timings.duration);
    console.log(`Jₜ value: ${response.json('jt_value')}, Mastery: ${response.json('mastery')}`);
  }
  
  sleep(Math.random() * 2 + 1); // Random pause 1-3 seconds
}

export function handleSummary(data) {
  console.log('Weight Optimization Load Test Summary:');
  console.log(`- Average optimization time: ${data.metrics.weight_optimization_time.avg}ms`);
  console.log(`- 95th percentile: ${data.metrics.weight_optimization_time['p(95)']}ms`);
  console.log(`- Optimization error rate: ${(data.metrics.optimization_errors.rate * 100).toFixed(2)}%`);
  console.log(`- Total requests: ${data.metrics.http_reqs.count}`);
}
