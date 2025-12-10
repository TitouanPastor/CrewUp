import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';
import { randomIntBetween, randomItem } from 'https://jslib.k6.io/k6-utils/1.4.0/index.js';

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// CUSTOM METRICS
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

const errorRate = new Rate('error_rate');
const apiResponseTime = new Trend('api_response_time');
const requestCounter = new Counter('total_requests');
const scenarioCounters = {
  browser: new Counter('scenario_browser'),
  active: new Counter('scenario_active_user'),
  creator: new Counter('scenario_event_creator'),
  reader: new Counter('scenario_data_reader'),
};

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// CONFIGURATION
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

const BASE_URL = __ENV.BASE_URL || 'https://crewup-staging.ltu-m7011e-3.se';
const MAX_VUS = parseInt(__ENV.MAX_VUS || '50');
const TEST_DURATION = __ENV.TEST_DURATION || '5m';  // Main load phase duration

export const options = {
  stages: [
    { duration: '1m', target: Math.floor(MAX_VUS * 0.2) },   // Warm-up: 20%
    { duration: TEST_DURATION, target: MAX_VUS },            // Load: 100% (configurable)
    { duration: '1m', target: MAX_VUS },                     // Sustain
    { duration: '1m', target: 0 },                           // Cool-down
  ],
  // Note: Total test duration = 3 minutes + TEST_DURATION
  thresholds: {
    // HTTP-level thresholds
    'http_req_duration': ['p(95)<1000', 'p(99)<2000'],       // 95% < 1s, 99% < 2s
    'http_req_failed': ['rate<0.01'],                        // < 1% HTTP failures
    
    // Custom metric thresholds
    'error_rate': ['rate<0.01'],                             // < 1% application errors
    'api_response_time': ['p(95)<800', 'p(99)<1500'],       // API-specific timing
  },
  noConnectionReuse: false,  // Reuse connections (realistic)
  userAgent: 'CrewUp-LoadTest/1.0',
};

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// HELPER FUNCTIONS
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

function makeRequest(url, description) {
  const res = http.get(url);
  const success = check(res, {
    [`${description}: status 200`]: (r) => r.status === 200,
  });
  
  if (!success) {
    errorRate.add(1);
    if (res.status !== 200) {
      console.warn(`⚠️  ${description} returned ${res.status}`);
    }
  } else {
    errorRate.add(0);
  }
  
  apiResponseTime.add(res.timings.duration);
  requestCounter.add(1);
  
  return res;
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// USER SCENARIOS
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

function casualBrowser() {
  scenarioCounters.browser.add(1);
  
  group('Casual Browser', () => {
    makeRequest(`${BASE_URL}/`, 'Homepage');
    sleep(randomIntBetween(2, 5));
    
    makeRequest(`${BASE_URL}/api/v1/events`, 'Browse events');
    sleep(randomIntBetween(3, 7));
    
    makeRequest(`${BASE_URL}/api/v1/users`, 'Browse users');
    sleep(randomIntBetween(2, 4));
  });
}

function activeUser() {
  scenarioCounters.active.add(1);
  
  group('Active User', () => {
    makeRequest(`${BASE_URL}/`, 'Homepage');
    sleep(randomIntBetween(1, 2));
    
    // Browse events
    makeRequest(`${BASE_URL}/api/v1/events`, 'List events');
    sleep(randomIntBetween(2, 4));
    
    // Browse users
    makeRequest(`${BASE_URL}/api/v1/users`, 'List users');
    sleep(randomIntBetween(1, 2));
    
    // Browse events again
    makeRequest(`${BASE_URL}/api/v1/events`, 'List events again');
    sleep(randomIntBetween(2, 3));
  });
}

function eventCreator() {
  scenarioCounters.creator.add(1);
  
  group('Event Creator', () => {
    makeRequest(`${BASE_URL}/`, 'Homepage');
    sleep(1);
    
    // Check existing events multiple times
    makeRequest(`${BASE_URL}/api/v1/events`, 'List events');
    sleep(randomIntBetween(2, 4));
    
    makeRequest(`${BASE_URL}/api/v1/events`, 'List events again');
    sleep(randomIntBetween(1, 3));
    
    // Check users
    makeRequest(`${BASE_URL}/api/v1/users`, 'Browse users');
    sleep(randomIntBetween(2, 3));
  });
}

function dataReader() {
  scenarioCounters.reader.add(1);
  
  group('Data Reader', () => {
    // Rapidly consume multiple endpoints (only 200 endpoints)
    makeRequest(`${BASE_URL}/api/v1/events`, 'Fetch events');
    sleep(0.5);
    
    makeRequest(`${BASE_URL}/api/v1/users`, 'Fetch users');
    sleep(0.5);
    
    // Health checks
    makeRequest(`${BASE_URL}/api/v1/users/health`, 'User health');
    sleep(0.5);
    
    makeRequest(`${BASE_URL}/api/v1/groups/health`, 'Group health');
    sleep(0.5);
    
    makeRequest(`${BASE_URL}/api/v1/events/health`, 'Event health');
    sleep(0.5);
    
    makeRequest(`${BASE_URL}/api/v1/moderation/health`, 'Moderation health');
    sleep(0.5);
    
    makeRequest(`${BASE_URL}/api/v1/safety/health`, 'Safety health');
    sleep(randomIntBetween(1, 2));
  });
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// MAIN TEST FUNCTION
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

export default function () {
  // Weighted scenario distribution (realistic user behavior)
  const scenario = randomItem([
    { weight: 35, name: 'browser' },      // 35% casual browsers
    { weight: 30, name: 'active' },       // 30% active users
    { weight: 20, name: 'creator' },      // 20% event creators
    { weight: 15, name: 'reader' },       // 15% data readers
  ].flatMap(s => Array(s.weight).fill(s.name)));
  
  switch (scenario) {
    case 'browser':
      casualBrowser();
      break;
    case 'active':
      activeUser();
      break;
    case 'creator':
      eventCreator();
      break;
    case 'reader':
      dataReader();
      break;
  }
  
  // Health check validation (occasional)
  if (Math.random() < 0.1) {  // 10% of iterations
    group('Health Checks', () => {
      makeRequest(`${BASE_URL}/api/v1/users/health`, 'User service health');
      makeRequest(`${BASE_URL}/api/v1/groups/health`, 'Group service health');
      makeRequest(`${BASE_URL}/api/v1/events/health`, 'Event service health');
      makeRequest(`${BASE_URL}/api/v1/moderation/health`, 'Moderation service health');
      makeRequest(`${BASE_URL}/api/v1/safety/health`, 'Safety service health');
    });
  }
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// CUSTOM SUMMARY
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

export function handleSummary(data) {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  
  console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log('📊 LOAD TEST SUMMARY');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');
  
  console.log(`Target URL: ${BASE_URL}`);
  console.log(`Max Virtual Users: ${MAX_VUS}`);
  console.log(`Test Duration: ${TEST_DURATION}\n`);
  
  // Request metrics
  const totalRequests = data.metrics.total_requests?.values?.count || 0;
  const httpReqDuration = data.metrics.http_req_duration?.values || {};
  const httpReqFailed = data.metrics.http_req_failed?.values?.rate || 0;
  const errorRateVal = data.metrics.error_rate?.values?.rate || 0;
  
  console.log('📈 Request Metrics:');
  console.log(`   Total Requests: ${totalRequests}`);
  console.log(`   HTTP Failure Rate: ${(httpReqFailed * 100).toFixed(2)}%`);
  console.log(`   Application Error Rate: ${(errorRateVal * 100).toFixed(2)}%`);
  console.log(`   Requests/sec: ${(data.metrics.http_reqs?.values?.rate || 0).toFixed(2)}\n`);
  
  console.log('⏱️  Response Times:');
  console.log(`   P50: ${httpReqDuration.p50?.toFixed(2) || 'N/A'} ms`);
  console.log(`   P95: ${httpReqDuration.p95?.toFixed(2) || 'N/A'} ms`);
  console.log(`   P99: ${httpReqDuration.p99?.toFixed(2) || 'N/A'} ms`);
  console.log(`   Max: ${httpReqDuration.max?.toFixed(2) || 'N/A'} ms\n`);
  
  console.log('👥 Scenario Distribution:');
  console.log(`   Casual Browsers: ${data.metrics.scenario_browser?.values?.count || 0}`);
  console.log(`   Active Users: ${data.metrics.scenario_active_user?.values?.count || 0}`);
  console.log(`   Event Creators: ${data.metrics.scenario_event_creator?.values?.count || 0}`);
  console.log(`   Data Readers: ${data.metrics.scenario_data_reader?.values?.count || 0}\n`);
  
  // Threshold evaluation
  const thresholdsFailed = Object.keys(data.metrics)
    .filter(key => data.metrics[key].thresholds)
    .some(key => Object.values(data.metrics[key].thresholds).some(t => !t.ok));
  
  if (thresholdsFailed) {
    console.log('❌ THRESHOLDS FAILED - System is under stress\n');
  } else {
    console.log('✅ ALL THRESHOLDS PASSED - System is healthy\n');
  }
  
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');
  
  return {
    'stdout': '',  // Already printed above
    [`results/summary-${timestamp}.json`]: JSON.stringify(data, null, 2),
  };
}
