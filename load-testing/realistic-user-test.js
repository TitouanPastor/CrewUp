import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';
import ws from 'k6/ws';

// ─────────────────────────────────────────────────────────────
// Custom metrics
// ─────────────────────────────────────────────────────────────
const errorRate = new Rate('errors');
const authErrors = new Rate('auth_errors');
const pageLoadTime = new Trend('page_load_time');
const apiCallTime = new Trend('api_call_time');

// HTTP status code counters
const status2xx = new Counter('http_status_2xx');
const status3xx = new Counter('http_status_3xx');
const status4xx = new Counter('http_status_4xx');
const status5xx = new Counter('http_status_5xx');

// ─────────────────────────────────────────────────────────────
// Configuration
// ─────────────────────────────────────────────────────────────
const BASE_URL = __ENV.BASE_URL || 'https://crewup-staging.ltu-m7011e-3.se';
const KEYCLOAK_URL = 'https://keycloak.ltu-m7011e-3.se';
const REALM = 'crewup';
const CLIENT_ID = 'crewup-staging'; // Staging client ID

// Test users
const USERS = [
  { email: 'user1@example.com', password: 'password123' },
  { email: 'user2@example.com', password: 'password123' },
];

// Group IDs (accessible by test users)
const ACCESSIBLE_GROUPS = [
  'd689d225-9b1c-4ca4-951a-5c95843cbb9b',
  '01ff5a47-eca2-4be1-b0c7-a6bf00ec7dc7',
];

// Test config
const MAX_VUS = parseInt(__ENV.MAX_VUS || '50');
const TEST_DURATION = __ENV.TEST_DURATION || '5m';

export const options = {
  stages: [
    { duration: '1m', target: Math.floor(MAX_VUS * 0.3) },  // Warm up
    { duration: TEST_DURATION, target: MAX_VUS },           // Load
    { duration: '1m', target: Math.floor(MAX_VUS * 0.5) },  // Sustain
    { duration: '30s', target: 0 },                         // Cool down
  ],
  thresholds: {
    'http_req_duration': ['p(95)<2000'], // 95% of requests under 2s
    'errors': ['rate<0.05'],             // Less than 5% errors
    'auth_errors': ['rate<0.01'],        // Less than 1% auth errors
  },
};

// ─────────────────────────────────────────────────────────────
// Helper: Get Keycloak token
// ─────────────────────────────────────────────────────────────
function getAuthToken(email, password) {
  const tokenUrl = `${KEYCLOAK_URL}/realms/${REALM}/protocol/openid-connect/token`;
  
  const payload = {
    grant_type: 'password',
    client_id: CLIENT_ID,
    username: email,
    password: password,
  };

  const params = {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
  };

  const res = http.post(tokenUrl, payload, params);
  
  const success = check(res, {
    'auth success': (r) => r.status === 200,
  });

  if (!success) {
    authErrors.add(1);
    console.error(`Auth failed for ${email}: ${res.status}`);
    return null;
  }

  try {
    const data = JSON.parse(res.body);
    return data.access_token;
  } catch (e) {
    authErrors.add(1);
    return null;
  }
}

// ─────────────────────────────────────────────────────────────
// Helper: Make authenticated API call
// ─────────────────────────────────────────────────────────────
function apiCall(method, path, token, body = null) {
  const url = `${BASE_URL}${path}`;
  const params = {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    tags: { type: 'api', endpoint: path },
  };

  let res;
  if (method === 'GET') {
    res = http.get(url, params);
  } else if (method === 'POST') {
    res = http.post(url, body ? JSON.stringify(body) : null, params);
  } else if (method === 'PATCH') {
    res = http.patch(url, body ? JSON.stringify(body) : null, params);
  } else if (method === 'DELETE') {
    res = http.del(url, null, params);
  }

  // Track status codes
  if (res.status >= 200 && res.status < 300) status2xx.add(1);
  else if (res.status >= 300 && res.status < 400) status3xx.add(1);
  else if (res.status >= 400 && res.status < 500) {
    status4xx.add(1);
    // Log 4xx errors for debugging
    console.warn(`4xx Error: ${method} ${path} -> ${res.status}`);
  }
  else if (res.status >= 500) {
    status5xx.add(1);
    console.error(`5xx Error: ${method} ${path} -> ${res.status}`);
  }

  apiCallTime.add(res.timings.duration);
  
  const success = check(res, {
    [`${method} ${path} OK`]: (r) => r.status >= 200 && r.status < 400, // Accept 2xx and 3xx
  });

  errorRate.add(!success);

  return res;
}

// ─────────────────────────────────────────────────────────────
// Helper: Load frontend page
// ─────────────────────────────────────────────────────────────
function loadPage(path, token = null) {
  const url = `${BASE_URL}${path}`;
  const params = token ? {
    headers: { 'Authorization': `Bearer ${token}` },
    tags: { type: 'page' },
  } : { tags: { type: 'page' } };

  const res = http.get(url, params);
  
  // Track status codes
  if (res.status >= 200 && res.status < 300) status2xx.add(1);
  else if (res.status >= 300 && res.status < 400) status3xx.add(1);
  else if (res.status >= 400 && res.status < 500) status4xx.add(1);
  else if (res.status >= 500) status5xx.add(1);
  
  pageLoadTime.add(res.timings.duration);

  const success = check(res, {
    [`page ${path} OK`]: (r) => r.status >= 200 && r.status < 400, // Accept 2xx and 3xx
  });

  errorRate.add(!success);

  return res;
}

// ─────────────────────────────────────────────────────────────
// User Scenarios
// ─────────────────────────────────────────────────────────────

// Scenario 1: Light browser (30%) - Authenticated, just browsing
function lightBrowser() {
  group('Light Browser', function() {
    // Pick random user and authenticate
    const user = USERS[Math.floor(Math.random() * USERS.length)];
    const token = getAuthToken(user.email, user.password);
    
    if (!token) {
      console.error('Failed to authenticate, skipping scenario');
      return;
    }

    // Visit homepage
    loadPage('/', token);
    sleep(2 + Math.random() * 3);

    // Browse events page
    loadPage('/events', token);
    apiCall('GET', '/api/v1/events', token);
    sleep(2 + Math.random() * 2);

    // Maybe check one random event detail
    const eventsRes = apiCall('GET', '/api/v1/events', token);
    sleep(1 + Math.random() * 2);
  });
}

// Scenario 2: Active user (40%) - Authenticated, browsing & interacting
function activeUser() {
  group('Active User', function() {
    // Pick random user
    const user = USERS[Math.floor(Math.random() * USERS.length)];
    const token = getAuthToken(user.email, user.password);
    
    if (!token) {
      console.error('Failed to authenticate, skipping scenario');
      return;
    }

    // Visit homepage (authenticated)
    loadPage('/', token);
    sleep(1 + Math.random() * 2);

    // Check profile
    loadPage('/profile', token);
    apiCall('GET', '/api/v1/users/me', token);
    sleep(1 + Math.random() * 2);

    // Browse events
    loadPage('/events', token);
    apiCall('GET', '/api/v1/events', token);
    sleep(2 + Math.random() * 2);

    // Check my groups
    loadPage('/groups', token);
    apiCall('GET', '/api/v1/groups', token);
    sleep(1 + Math.random() * 2);

    // Check safety alerts (user1 has alerts)
    if (user.email === 'user1@example.com') {
      apiCall('GET', '/api/v1/safety/my-alerts', token);
      sleep(1);
    }
  });
}

// Scenario 3: Group chat user (20%) - Joins group chat, reads messages, SENDS via WebSocket
function groupChatUser() {
  group('Group Chat User', function() {
    const user = USERS[Math.floor(Math.random() * USERS.length)];
    const token = getAuthToken(user.email, user.password);
    
    if (!token) return;

    // Pick random accessible group
    const groupId = ACCESSIBLE_GROUPS[Math.floor(Math.random() * ACCESSIBLE_GROUPS.length)];

    // Visit group chat page (frontend handles WebSocket)
    loadPage(`/groups/${groupId}/chat`, token);
    sleep(1);

    // Load messages via REST API
    apiCall('GET', `/api/v1/groups/${groupId}/messages`, token);
    sleep(1);

    // Connect to WebSocket and send a message
    const wsUrl = `wss://crewup-staging.ltu-m7011e-3.se/api/v1/ws/groups/${groupId}?token=${encodeURIComponent(token)}`;
    
    const wsRes = ws.connect(wsUrl, { tags: { type: 'websocket' } }, function (socket) {
      socket.on('open', function() {
        // Send a chat message (same format as frontend)
        const message = {
          type: 'message',
          content: `Load test message ${Date.now()}`
        };
        socket.send(JSON.stringify(message));
      });

      socket.on('message', function (data) {
        // Message received (server echo with id, user_id, username, timestamp, etc.)
        try {
          const msg = JSON.parse(data);
          check(msg, {
            'WS message has content': (m) => m.content && m.content.length > 0,
            'WS message has user_id': (m) => m.user_id !== undefined,
          });
        } catch (e) {
          // Not JSON or malformed
        }
      });

      socket.on('close', function() {
        // Connection closed normally
      });

      socket.on('error', function (e) {
        console.warn(`WebSocket error: ${e ? e.error() : 'unknown'}`);
      });

      // Keep connection open for 3 seconds to receive broadcast
      socket.setTimeout(function () {
        socket.close();
      }, 3000);
    });

    check(wsRes, {
      'WebSocket connected': (r) => r && r.status === 101,
    });

    sleep(1 + Math.random() * 2);

    // Check group members
    apiCall('GET', `/api/v1/groups/${groupId}/members`, token);
    sleep(1);
    
    // Check group details
    apiCall('GET', `/api/v1/groups/${groupId}`, token);
    sleep(1 + Math.random() * 2);
  });
}

// Scenario 4: Event creator (10%) - Creates/joins events with VALID dates and CORRECT fields
function eventCreator() {
  group('Event Creator', function() {
    const user = USERS[Math.floor(Math.random() * USERS.length)];
    const token = getAuthToken(user.email, user.password);
    
    if (!token) return;

    // Browse events first
    loadPage('/events', token);
    apiCall('GET', '/api/v1/events', token);
    sleep(1 + Math.random() * 2);

    // Create a new event with valid future date (at least 30 min from now)
    const now = new Date();
    const startTime = new Date(now.getTime() + (30 + Math.random() * 120) * 60000); // 30min to 2.5h from now
    const endTime = new Date(startTime.getTime() + (60 + Math.random() * 120) * 60000); // 1h to 3h duration
    
    const newEvent = {
      name: `Load Test Event ${Date.now()}`,
      description: 'Auto-generated event for load testing',
      address: 'Test Location, Luleå',
      event_start: startTime.toISOString(),
      event_end: endTime.toISOString(),
      max_participants: 50,
    };

    const createRes = apiCall('POST', '/api/v1/events', token, newEvent);
    
    if (createRes.status === 201 || createRes.status === 200) {
      try {
        const eventData = JSON.parse(createRes.body);
        const eventId = eventData.id || eventData.event_id;
        
        if (eventId) {
          sleep(1);
          // Get event details
          apiCall('GET', `/api/v1/events/${eventId}`, token);
          sleep(1);
          
          // Check participants
          apiCall('GET', `/api/v1/events/${eventId}/participants`, token);
        }
      } catch (e) {
        // Event created but couldn't parse response
      }
    }

    sleep(2 + Math.random() * 2);
  });
}

// ─────────────────────────────────────────────────────────────
// Main execution
// ─────────────────────────────────────────────────────────────
export default function() {
  const rand = Math.random();

  if (rand < 0.30) {
    // 30% light browsers (authenticated but minimal activity)
    lightBrowser();
  } else if (rand < 0.70) {
    // 40% active users
    activeUser();
  } else if (rand < 0.90) {
    // 20% group chat users
    groupChatUser();
  } else {
    // 10% event creators
    eventCreator();
  }

  sleep(1 + Math.random() * 2);
}

// ─────────────────────────────────────────────────────────────
// Summary
// ─────────────────────────────────────────────────────────────
export function handleSummary(data) {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');

  console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log('📊 REALISTIC USER TEST - SUMMARY');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

  const metrics = data.metrics;

  console.log('Configuration:');
  console.log(`   Max VUs: ${MAX_VUS}`);
  console.log(`   Test Duration: ${TEST_DURATION}`);
  console.log(`   Base URL: ${BASE_URL}\n`);

  console.log('Overall Performance:');
  console.log(`   Total Requests: ${metrics.http_reqs?.values.count || 0}`);
  console.log(`   Requests/sec: ${(metrics.http_reqs?.values.rate || 0).toFixed(2)}`);
  console.log(`   Total Iterations: ${metrics.iterations?.values.count || 0}\n`);

  console.log('Response Times:');
  console.log(`   Avg Page Load: ${(metrics.page_load_time?.values.avg || 0).toFixed(2)} ms`);
  console.log(`   Avg API Call: ${(metrics.api_call_time?.values.avg || 0).toFixed(2)} ms`);
  console.log(`   P95 (all): ${(metrics.http_req_duration?.values['p(95)'] || 0).toFixed(2)} ms`);
  console.log(`   P99 (all): ${(metrics.http_req_duration?.values['p(99)'] || 0).toFixed(2)} ms\n`);

  console.log('Reliability:');
  console.log(`   Error Rate: ${((metrics.errors?.values.rate || 0) * 100).toFixed(2)}%`);
  console.log(`   Auth Error Rate: ${((metrics.auth_errors?.values.rate || 0) * 100).toFixed(2)}%`);
  console.log(`   HTTP Failure Rate: ${((metrics.http_req_failed?.values.rate || 0) * 100).toFixed(2)}%\n`);

  console.log('HTTP Status Codes:');
  const total2xx = metrics.http_status_2xx?.values.count || 0;
  const total3xx = metrics.http_status_3xx?.values.count || 0;
  const total4xx = metrics.http_status_4xx?.values.count || 0;
  const total5xx = metrics.http_status_5xx?.values.count || 0;
  const totalReqs = metrics.http_reqs?.values.count || 1;
  
  console.log(`   2xx Success: ${total2xx} (${((total2xx/totalReqs)*100).toFixed(1)}%)`);
  console.log(`   3xx Redirect: ${total3xx} (${((total3xx/totalReqs)*100).toFixed(1)}%)`);
  console.log(`   4xx Client Error: ${total4xx} (${((total4xx/totalReqs)*100).toFixed(1)}%)`);
  console.log(`   5xx Server Error: ${total5xx} (${((total5xx/totalReqs)*100).toFixed(1)}%)\n`);

  console.log('User Scenarios Distribution:');
  console.log('   30% Light Browsers (authenticated, minimal activity)');
  console.log('   40% Active Users (full browsing: profile, groups, alerts)');
  console.log('   20% Group Chat Users (messages & group interactions)');
  console.log('   10% Event Creators (create & manage events)\n');

  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

  return {
    'stdout': '',
    [`results/realistic-test-${timestamp}.json`]: JSON.stringify(data, null, 2),
  };
}
