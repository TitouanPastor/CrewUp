import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

// ─────────────────────────────────────────────────────────────
// Custom metrics
// ─────────────────────────────────────────────────────────────
const errorRate = new Rate('errors');

// Per-endpoint metrics
const eventsLatency = new Trend('events_latency');
const usersLatency = new Trend('users_latency');
const groupsLatency = new Trend('groups_latency');
const safetyLatency = new Trend('safety_latency');
const moderationLatency = new Trend('moderation_latency');

const eventsCount = new Counter('events_requests');
const usersCount = new Counter('users_requests');
const groupsCount = new Counter('groups_requests');
const safetyCount = new Counter('safety_requests');
const moderationCount = new Counter('moderation_requests');

// ─────────────────────────────────────────────────────────────
// Env config
// ─────────────────────────────────────────────────────────────
const BASE_URL = __ENV.BASE_URL || 'https://crewup-staging.ltu-m7011e-3.se';

// Step test parameters
const START_VUS = parseInt(__ENV.START_VUS || '400');     // first plateau
const MAX_VUS = parseInt(__ENV.MAX_VUS || '600');         // last plateau
const STEP_VUS = parseInt(__ENV.STEP_VUS || '50');        // increment each step
const RAMP_PER_STEP = __ENV.RAMP_PER_STEP || '30s';       // ramp duration between plateaus
const HOLD_PER_STEP = __ENV.HOLD_PER_STEP || '2m';        // stable measurement per plateau

// Optional: allow your old style too
// If someone runs: -e TARGET_VUS=600 -e RAMP_DURATION=5m
// we keep compatibility by mapping to a single plateau test.
// (If you don't want this, you can remove this block.)
const LEGACY_TARGET = __ENV.TARGET_VUS ? parseInt(__ENV.TARGET_VUS) : null;
const LEGACY_RAMP = __ENV.RAMP_DURATION || null;

// ─────────────────────────────────────────────────────────────
// Build stages
// ─────────────────────────────────────────────────────────────
function buildStepStages() {
  const stages = [];

  // Safety
  const start = Math.max(1, START_VUS);
  const max = Math.max(start, MAX_VUS);
  const step = Math.max(1, STEP_VUS);

  // Warm-up ramp to start
  stages.push({ duration: RAMP_PER_STEP, target: start });
  stages.push({ duration: HOLD_PER_STEP, target: start });

  // Each next plateau
  for (let vus = start + step; vus <= max; vus += step) {
    stages.push({ duration: RAMP_PER_STEP, target: vus });
    stages.push({ duration: HOLD_PER_STEP, target: vus });
  }

  // Cool down
  stages.push({ duration: RAMP_PER_STEP, target: 0 });

  return stages;
}

function buildLegacyStages() {
  const target = LEGACY_TARGET || 200;
  const ramp = LEGACY_RAMP || '5m';
  return [
    { duration: ramp, target },
    { duration: '2m', target },
  ];
}

const stages = LEGACY_TARGET ? buildLegacyStages() : buildStepStages();

// ─────────────────────────────────────────────────────────────
// k6 options
// ─────────────────────────────────────────────────────────────
export const options = {
  stages,
  thresholds: {
    // Loose thresholds: you want to *observe* the break point
    'http_req_duration': ['p(95)<5000'],
    'errors': ['rate<0.1'],

    // Per-endpoint thresholds (loose to observe breaking points)
    'events_latency': ['p(95)<3000'],
    'users_latency': ['p(95)<3000'],
    'groups_latency': ['p(95)<3000'],
    'safety_latency': ['p(95)<3000'],
    'moderation_latency': ['p(95)<3000'],

    // Super utile pour isoler le pain-point
    'http_req_failed{endpoint:events}': ['rate<0.02'], // tolérance un peu plus large pendant stress
  },
};

// ─────────────────────────────────────────────────────────────
// Helper
// ─────────────────────────────────────────────────────────────
function makeRequest(url, name = '', endpoint = '') {
  const res = http.get(url, { tags: { endpoint } });

  const success = check(res, {
    [`${name} status is 200`]: (r) => r.status === 200,
  });

  errorRate.add(!success);
  
  // Track latency per endpoint
  if (endpoint === 'events') {
    eventsLatency.add(res.timings.duration);
    eventsCount.add(1);
  } else if (endpoint === 'users') {
    usersLatency.add(res.timings.duration);
    usersCount.add(1);
  } else if (endpoint === 'groups') {
    groupsLatency.add(res.timings.duration);
    groupsCount.add(1);
  } else if (endpoint === 'safety') {
    safetyLatency.add(res.timings.duration);
    safetyCount.add(1);
  } else if (endpoint === 'moderation') {
    moderationLatency.add(res.timings.duration);
    moderationCount.add(1);
  }
  
  return res;
}

// ─────────────────────────────────────────────────────────────
// Scenario - Health checks only with random sleep
// ─────────────────────────────────────────────────────────────
export default function () {
    // Health checks with endpoint tags
    makeRequest(`${BASE_URL}/api/v1/users/health`, 'Users health', 'users');
    sleep(0.5 + Math.random() * 0.5);

    makeRequest(`${BASE_URL}/api/v1/events/health`, 'Events health', 'events');
    sleep(0.5 + Math.random() * 0.5);

    makeRequest(`${BASE_URL}/api/v1/groups/health`, 'Groups health', 'groups');
    sleep(0.5 + Math.random() * 0.5);

    makeRequest(`${BASE_URL}/api/v1/safety/health`, 'Safety health', 'safety');
    sleep(0.5 + Math.random() * 0.5);

    makeRequest(`${BASE_URL}/api/v1/moderation/health`, 'Moderation health', 'moderation');
    sleep(1 + Math.random() * 1);
}

// ─────────────────────────────────────────────────────────────
// AUTO RECAP (English) - Custom Summary
// ─────────────────────────────────────────────────────────────

function metricValues(data, metricName) {
  const m = data.metrics[metricName];
  return m && m.values ? m.values : null;
}

function fmtMs(v) {
  if (v === null || v === undefined) return 'N/A';
  return `${v.toFixed(2)} ms`;
}

function fmtPct(v) {
  if (v === null || v === undefined) return 'N/A';
  return `${(v * 100).toFixed(2)}%`;
}

function fmtNum(v) {
  if (v === null || v === undefined) return 'N/A';
  return `${v}`;
}

function thresholdFailed(data) {
  return Object.keys(data.metrics)
    .filter((k) => data.metrics[k].thresholds)
    .some((k) => Object.values(data.metrics[k].thresholds).some((t) => !t.ok));
}

function printEndpointBlock(data, endpoint) {
  const durKey = `http_req_duration{endpoint:${endpoint}}`;
  const failKey = `http_req_failed{endpoint:${endpoint}}`;
  const reqsKey = `http_reqs{endpoint:${endpoint}}`;
  
  // Custom metrics
  const customLatencyKey = `${endpoint}_latency`;
  const customCountKey = `${endpoint}_requests`;

  const dur = metricValues(data, durKey);
  const fail = metricValues(data, failKey);
  const reqs = metricValues(data, reqsKey);
  
  // Try custom metrics
  const customLatency = metricValues(data, customLatencyKey);
  const customCount = metricValues(data, customCountKey);

  console.log(`\n📌 Endpoint: ${endpoint}`);
  console.log(`   Requests count: ${fmtNum(customCount?.count || reqs?.count)}`);
  console.log(`   Requests/sec:   ${fmtNum((reqs?.rate || 0).toFixed(2))}`);

  console.log(`   Failure rate:   ${fmtPct(fail?.rate)}`);

  // Use custom latency if available, otherwise tagged http_req_duration
  const latency = customLatency || dur;
  console.log(`   Latency P50:    ${fmtMs(latency?.p50 || latency?.['p(50)'])}`);
  console.log(`   Latency P95:    ${fmtMs(latency?.p95 || latency?.['p(95)'])}`);
  console.log(`   Latency P99:    ${fmtMs(latency?.p99 || latency?.['p(99)'])}`);
  console.log(`   Latency Max:    ${fmtMs(latency?.max)}`);
}

export function handleSummary(data) {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');

  const globalDur = metricValues(data, 'http_req_duration');
  const globalFail = metricValues(data, 'http_req_failed');
  const err = metricValues(data, 'errors');
  const reqs = metricValues(data, 'http_reqs');
  const iters = metricValues(data, 'iterations');
  const vusMax = metricValues(data, 'vus_max');

  const failed = thresholdFailed(data);

  console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log('📊 STEP STRESS TEST - AUTO RECAP');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

  console.log('Test Target:');
  console.log(`   Base URL:        ${__ENV.BASE_URL || 'https://crewup-staging.ltu-m7011e-3.se'}`);
  console.log(`   Start VUs:       ${__ENV.START_VUS || '400'}`);
  console.log(`   Max VUs:         ${__ENV.MAX_VUS || __ENV.TARGET_VUS || '600'}`);
  console.log(`   Step VUs:        ${__ENV.STEP_VUS || '50'}`);
  console.log(`   Ramp/Step:       ${__ENV.RAMP_PER_STEP || __ENV.RAMP_DURATION || '30s'}`);
  console.log(`   Hold/Step:       ${__ENV.HOLD_PER_STEP || '2m'}`);

  if (__ENV.TARGET_VUS) {
    console.log('   Mode:           Legacy (single ramp + hold)');
  } else {
    console.log('   Mode:           Step test (multi-plateau)');
  }

  console.log('\nGlobal Throughput & Load:');
  console.log(`   Total requests: ${fmtNum(reqs?.count)}`);
  console.log(`   Requests/sec:   ${fmtNum(reqs?.rate?.toFixed(2))}`);
  console.log(`   Total iterations: ${fmtNum(iters?.count)}`);
  console.log(`   Max VUs observed: ${fmtNum(vusMax?.value)}`);

  console.log('\nGlobal Reliability:');
  console.log(`   HTTP failure rate:        ${fmtPct(globalFail?.rate)}`);
  console.log(`   Application error rate:   ${fmtPct(err?.rate)}`);

  console.log('\nGlobal Latency (all endpoints):');
  console.log(`   P50: ${fmtMs(globalDur?.p50 || globalDur?.['p(50)'])}`);
  console.log(`   P95: ${fmtMs(globalDur?.p95 || globalDur?.['p(95)'])}`);
  console.log(`   P99: ${fmtMs(globalDur?.p99 || globalDur?.['p(99)'])}`);
  console.log(`   Max: ${fmtMs(globalDur?.max)}`);

  console.log('\nEndpoint Breakdown (tag-based):');
  ['events', 'users', 'groups', 'safety', 'moderation'].forEach((ep) => printEndpointBlock(data, ep));

  console.log('\nThreshold Status:');
  if (failed) {
    console.log('   ❌ One or more thresholds FAILED — system is showing stress.');
  } else {
    console.log('   ✅ All thresholds PASSED — no defined limits breached.');
  }

  console.log('\nInterpretation Hints:');
  console.log('   - If "events" fails before others, your bottleneck is likely in the events service or its DB queries.');
  console.log('   - A drop in Requests/sec while VUs increase is a classic saturation signal.');
  console.log('   - High Max latency with stable P95 suggests a long-tail issue (timeouts, queueing, pool exhaustion).');

  console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

  return {
    'stdout': '', // already printed
    [`results/step-summary-${timestamp}.json`]: JSON.stringify(data, null, 2),
  };
}
