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

// Action counters
const eventsCreated = new Counter('events_created');
const groupsJoined = new Counter('groups_joined');
const messagesSent = new Counter('messages_sent');
const alertsCreated = new Counter('alerts_created');

// ─────────────────────────────────────────────────────────────
// Configuration
// ─────────────────────────────────────────────────────────────
const BASE_URL = __ENV.BASE_URL || 'https://crewup-staging.ltu-m7011e-3.se';
const KEYCLOAK_URL = 'https://keycloak.ltu-m7011e-3.se';
const REALM = 'crewup';
const CLIENT_ID = 'crewup-staging';

// Test users
const USERS = [
  { email: 'user1@example.com', password: 'password123' },
  { email: 'user2@example.com', password: 'password123' },
];

// Shared state for created resources (populated during test)
const createdEvents = [];
const createdGroups = [];
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
    'http_req_duration': ['p(95)<3000'],
    'errors': ['rate<0.05'],
    'auth_errors': ['rate<0.01'],
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
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  };

  const res = http.post(tokenUrl, payload, params);
  
  const success = check(res, {
    'auth success': (r) => r.status === 200,
  });

  if (!success) {
    authErrors.add(1);
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
// Helper: API call with error tracking
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
    console.warn(`❌ 4xx Error: ${method} ${path} returned ${res.status} - ${res.body ? res.body.substring(0, 100) : 'no body'}`);
  }
  else if (res.status >= 500) {
    status5xx.add(1);
    console.error(`🔥 5xx Error: ${method} ${path} returned ${res.status} - ${res.body ? res.body.substring(0, 100) : 'no body'}`);
  }

  apiCallTime.add(res.timings.duration);
  
  const success = check(res, {
    [`${method} ${path} OK`]: (r) => r.status >= 200 && r.status < 400,
  });

  errorRate.add(!success);
  return res;
}

// ─────────────────────────────────────────────────────────────
// Helper: Load page
// ─────────────────────────────────────────────────────────────
function loadPage(path, token = null) {
  const url = `${BASE_URL}${path}`;
  const params = token ? {
    headers: { 'Authorization': `Bearer ${token}` },
    tags: { type: 'page' },
  } : { tags: { type: 'page' } };

  const res = http.get(url, params);
  
  if (res.status >= 200 && res.status < 300) status2xx.add(1);
  else if (res.status >= 300 && res.status < 400) status3xx.add(1);
  else if (res.status >= 400 && res.status < 500) status4xx.add(1);
  else if (res.status >= 500) status5xx.add(1);
  
  pageLoadTime.add(res.timings.duration);

  const success = check(res, {
    [`page ${path} OK`]: (r) => r.status >= 200 && r.status < 400,
  });

  errorRate.add(!success);
  return res;
}

// ─────────────────────────────────────────────────────────────
// Scenario 1: Casual browser (40%) - Browse, no heavy actions
// ─────────────────────────────────────────────────────────────
function casualBrowser() {
  group('Casual Browser', function() {
    const user = USERS[Math.floor(Math.random() * USERS.length)];
    const token = getAuthToken(user.email, user.password);
    if (!token) return;

    loadPage('/', token);
    sleep(2 + Math.random() * 3);

    loadPage('/events', token);
    apiCall('GET', '/api/v1/events', token);
    sleep(2 + Math.random() * 2);

    // Maybe check profile
    if (Math.random() < 0.3) {
      loadPage('/profile', token);
      apiCall('GET', '/api/v1/users/me', token);
      sleep(1 + Math.random() * 2);
    }
  });
}

// ─────────────────────────────────────────────────────────────
// Scenario 2: Active user (35%) - Browse, join events, check groups
// ─────────────────────────────────────────────────────────────
function activeUser() {
  group('Active User', function() {
    const user = USERS[Math.floor(Math.random() * USERS.length)];
    const token = getAuthToken(user.email, user.password);
    if (!token) return;

    loadPage('/', token);
    sleep(1 + Math.random() * 2);

    // Browse events and maybe join one
    loadPage('/events', token);
    const eventsRes = apiCall('GET', '/api/v1/events', token);
    sleep(1);

    if (eventsRes.status === 200 && Math.random() < 0.3) {
      try {
        const events = JSON.parse(eventsRes.body);
        if (events.length > 0) {
          const randomEvent = events[Math.floor(Math.random() * events.length)];
          const eventId = randomEvent.id || randomEvent.event_id;
          if (eventId) {
            apiCall('POST', `/api/v1/events/${eventId}/join`, token);
            sleep(1);
          }
        }
      } catch (e) {}
    }

    sleep(1 + Math.random() * 2);

    // Check groups
    loadPage('/groups', token);
    apiCall('GET', '/api/v1/groups', token);
    sleep(1 + Math.random() * 2);

    // Check profile + safety alerts
    loadPage('/profile', token);
    apiCall('GET', '/api/v1/users/me', token);
    if (user.email === 'user1@example.com') {
      apiCall('GET', '/api/v1/safety/my-alerts', token);
    }
    sleep(1);
  });
}

// ─────────────────────────────────────────────────────────────
// Scenario 3: Chat user (15%) - Join chat, send messages
// ─────────────────────────────────────────────────────────────
function chatUser() {
  group('Chat User', function() {
    const user = USERS[Math.floor(Math.random() * USERS.length)];
    const token = getAuthToken(user.email, user.password);
    if (!token) return;

    const groupId = ACCESSIBLE_GROUPS[Math.floor(Math.random() * ACCESSIBLE_GROUPS.length)];

    loadPage(`/groups/${groupId}/chat`, token);
    sleep(1);

    apiCall('GET', `/api/v1/groups/${groupId}/messages`, token);
    sleep(1);

    // Send message via WebSocket
    const wsUrl = `wss://crewup-staging.ltu-m7011e-3.se/api/v1/ws/groups/${groupId}?token=${encodeURIComponent(token)}`;
    
    const wsRes = ws.connect(wsUrl, { tags: { type: 'websocket' } }, function (socket) {
      socket.on('open', function() {
        const message = {
          type: 'message',
          content: `Load Test Chat ${Date.now()}`
        };
        socket.send(JSON.stringify(message));
        messagesSent.add(1);
      });

      socket.on('message', function (data) {
        try {
          const msg = JSON.parse(data);
          check(msg, {
            'WS message OK': (m) => m.content !== undefined,
          });
        } catch (e) {}
      });

      socket.on('error', function (e) {
        // Ignore WS errors
      });

      socket.setTimeout(function () {
        socket.close();
      }, 2000);
    });

    sleep(2 + Math.random() * 2);
  });
}

// ─────────────────────────────────────────────────────────────
// Scenario 4: Group creator (5%) - Create event then group
// ─────────────────────────────────────────────────────────────
function groupCreator() {
  group('Group Creator', function() {
    const user = USERS[Math.floor(Math.random() * USERS.length)];
    const token = getAuthToken(user.email, user.password);
    if (!token) return;

    loadPage('/events', token);
    sleep(1);

    // First create an event (groups need event_id)
    const now = new Date();
    const startTime = new Date(now.getTime() + 31 * 60000);
    const endTime = new Date(startTime.getTime() + (60 + Math.random() * 180) * 60000);
    
    const newEvent = {
      name: `Load Test Event ${Date.now()}`,
      description: 'Event for group creation',
      address: 'Luleå University of Technology, Sweden',
      event_start: startTime.toISOString(),
      event_end: endTime.toISOString(),
      max_participants: 20 + Math.floor(Math.random() * 80),
    };

    const eventRes = apiCall('POST', '/api/v1/events', token, newEvent);
    
    if (eventRes.status === 201 || eventRes.status === 200) {
      eventsCreated.add(1);
      try {
        const eventData = JSON.parse(eventRes.body);
        const eventId = eventData.id || eventData.event_id;
        
        if (eventId) {
          createdEvents.push(eventId);
          sleep(1);

          // Now create a group for this event
          const newGroup = {
            name: `Load Test Group ${Date.now()}`,
            description: 'Auto-generated group for load testing',
            event_id: eventId,
          };

          const createRes = apiCall('POST', '/api/v1/groups', token, newGroup);
          
          if (createRes.status === 201 || createRes.status === 200) {
            groupsJoined.add(1);
            try {
              const groupData = JSON.parse(createRes.body);
              const groupId = groupData.id || groupData.group_id;
              if (groupId) {
                createdGroups.push(groupId);
                sleep(1);
                apiCall('GET', `/api/v1/groups/${groupId}`, token);
              }
            } catch (e) {}
          }
        }
      } catch (e) {}
    }

    sleep(2 + Math.random() * 2);
  });
}

// ─────────────────────────────────────────────────────────────
// Scenario 5: Safety alert creator (3%) - Create safety alerts
// ─────────────────────────────────────────────────────────────
function safetyAlertCreator() {
  group('Safety Alert Creator', function() {
    const user = USERS[Math.floor(Math.random() * USERS.length)];
    const token = getAuthToken(user.email, user.password);
    if (!token) return;

    loadPage('/profile', token);
    sleep(1);

    // Create a safety alert
    const groupId = ACCESSIBLE_GROUPS[Math.floor(Math.random() * ACCESSIBLE_GROUPS.length)];
    const alert = {
      alert_type: 'medical',
      group_id: groupId,
      message: `Load Test Alert ${Date.now()}`,
      latitude: 65.5848,
      longitude: 22.1547,
    };

    const alertRes = apiCall('POST', '/api/v1/safety', token, alert);
    
    if (alertRes.status === 201 || alertRes.status === 200) {
      alertsCreated.add(1);
    }

    sleep(2 + Math.random() * 2);
  });
}

// ─────────────────────────────────────────────────────────────
// Scenario 6: Event creator (2%) - Create realistic events
// ─────────────────────────────────────────────────────────────
function eventCreator() {
  group('Event Creator', function() {
    const user = USERS[Math.floor(Math.random() * USERS.length)];
    const token = getAuthToken(user.email, user.password);
    if (!token) return;

    loadPage('/events', token);
    apiCall('GET', '/api/v1/events', token);
    sleep(1);

    const now = new Date();
    // Create events that start in 31 minutes (minimum required)
    const startTime = new Date(now.getTime() + 31 * 60000);
    const endTime = new Date(startTime.getTime() + (60 + Math.random() * 180) * 60000);
    
    const newEvent = {
      name: `Load Test Event ${Date.now()}`,
      description: 'Auto-generated event for load testing',
      address: 'Luleå University of Technology, Sweden',
      event_start: startTime.toISOString(),
      event_end: endTime.toISOString(),
      max_participants: 20 + Math.floor(Math.random() * 80),
    };

    const createRes = apiCall('POST', '/api/v1/events', token, newEvent);
    
    if (createRes.status === 201 || createRes.status === 200) {
      eventsCreated.add(1);
      try {
        const eventData = JSON.parse(createRes.body);
        const eventId = eventData.id || eventData.event_id;
        if (eventId) {
          createdEvents.push(eventId);
          sleep(1);
          apiCall('GET', `/api/v1/events/${eventId}`, token);
        }
      } catch (e) {}
    }

    sleep(2 + Math.random() * 2);
  });
}

// ─────────────────────────────────────────────────────────────
// Main execution
// ─────────────────────────────────────────────────────────────
export default function() {
  const rand = Math.random();

  if (rand < 0.40) {
    casualBrowser();      // 40%
  } else if (rand < 0.75) {
    activeUser();         // 35%
  } else if (rand < 0.90) {
    chatUser();           // 15%
  } else if (rand < 0.93) {
    groupCreator();       // 3%
  } else if (rand < 0.96) {
    safetyAlertCreator(); // 3%
  } else if (rand < 0.97) {
    eventCreator();       // 1%
  } else {
    casualBrowser();      // fallback (~3%)
  }

  sleep(1 + Math.random() * 2);
}

// ─────────────────────────────────────────────────────────────
// Summary
// ─────────────────────────────────────────────────────────────
export function handleSummary(data) {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');

  console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log('📊 FULL SCENARIO TEST - SUMMARY');
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

  console.log('User Actions:');
  console.log(`   Events Created: ${metrics.events_created?.values.count || 0}`);
  console.log(`   Groups Joined/Created: ${metrics.groups_joined?.values.count || 0}`);
  console.log(`   Messages Sent: ${metrics.messages_sent?.values.count || 0}`);
  console.log(`   Safety Alerts: ${metrics.alerts_created?.values.count || 0}\n`);

  console.log('User Scenarios Distribution:');
  console.log('   43% Casual Browsers');
  console.log('   35% Active Users (join events, check groups)');
  console.log('   15% Chat Users (send messages via WebSocket)');
  console.log('    3% Group Creators');
  console.log('    3% Safety Alert Creators');
  console.log('    1% Event Creators\n');

  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

  return {
    'stdout': '',
    [`results/full-scenario-${timestamp}.json`]: JSON.stringify(data, null, 2),
  };
}
