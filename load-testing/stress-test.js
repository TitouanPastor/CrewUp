import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

// Custom metrics
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

// Test configuration
const TARGET_VUS = __ENV.TARGET_VUS || '200'; // Maximum users to reach
const RAMP_DURATION = __ENV.RAMP_DURATION || '10m'; // Time to reach target

export const options = {
    stages: [
        { duration: RAMP_DURATION, target: parseInt(TARGET_VUS) }, // Ramp up to target
        { duration: '2m', target: parseInt(TARGET_VUS) },          // Hold at target
    ],
    thresholds: {
        // No strict thresholds - we want to see when it breaks
        'http_req_duration': ['p(95)<5000'], // Warning if p95 > 5s
        'errors': ['rate<0.1'],              // Warning if >10% errors
        
        // Per-endpoint thresholds (loose to observe breaking points)
        'events_latency': ['p(95)<3000'],
        'users_latency': ['p(95)<3000'],
        'groups_latency': ['p(95)<3000'],
        'safety_latency': ['p(95)<3000'],
        'moderation_latency': ['p(95)<3000'],
    },
};

const BASE_URL = 'https://crewup-staging.ltu-m7011e-3.se';

// Helper function to make requests and track errors + latency per endpoint
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

// Stress test scenario - simple but effective
export default function () {
    // Test homepage
    makeRequest(BASE_URL, 'Homepage');
    sleep(0.5 + Math.random() * 0.5);

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
