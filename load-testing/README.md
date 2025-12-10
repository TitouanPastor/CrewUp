# CrewUp Load Testing

Professional load testing suite for the CrewUp microservices platform using k6.

## 📋 Overview

This suite performs comprehensive load testing with **authenticated users** and realistic scenarios including WebSocket messaging, event/group creation, and safety alerts.

### Test Scripts

1. **`full-scenario-test.js`** ⭐ (RECOMMENDED) - Complete user simulation with Keycloak auth
2. **`realistic-user-test.js`** - Authenticated user journeys
3. **`step-stress-test.js`** - Gradual capacity testing
4. **`load-test.js`** - Basic load testing (public endpoints only)
5. **`cleanup.sh`** - Database cleanup script

## 🚀 Quick Start

### Run Complete Load Test

```bash
# 1. Run full scenario test (100 VUs, 2 minutes)
k6 run -e MAX_VUS=100 -e TEST_DURATION=2m ./full-scenario-test.js

# 2. Review results in console output

# 3. Clean up test data
./cleanup.sh
```

### Capacity Study

```bash
# Test at increasing load levels
for vus in 50 100 200; do
  echo "Testing with $vus VUs..."
  k6 run -e MAX_VUS=$vus -e TEST_DURATION=5m ./full-scenario-test.js
  ./cleanup.sh
  sleep 30
done
```

## 📊 Test Scripts Details

### 1. `full-scenario-test.js` ⭐ RECOMMENDED

**Realistic end-to-end testing with authentication and WebSocket support.**

**Features**:
- ✅ Keycloak JWT authentication
- ✅ WebSocket chat messaging
- ✅ Event creation (start time: +31min)
- ✅ Group creation (with event association)
- ✅ Safety alert creation
- ✅ Realistic user distribution

**User Scenarios**:
- 40% Casual Browsers (homepage, browse events/users)
- 35% Active Users (join events, check groups, profile)
- 15% Chat Users (WebSocket messages via `/api/v1/ws/groups/{groupId}`)
- 5% Group Creators (create events + groups)
- 3% Safety Alert Creators (medical alerts)
- 2% Event Creators (standalone events)

**Usage**:
```bash
# Default: 50 VUs, 5 minutes
k6 run ./full-scenario-test.js

# Custom load
k6 run -e MAX_VUS=100 -e TEST_DURATION=2m ./full-scenario-test.js
```

**Metrics**:
- Events Created
- Groups Joined/Created
- Messages Sent (WebSocket)
- Safety Alerts Created
- Response Times (P95, P99)
- Error Rates by status code

---

### 2. `realistic-user-test.js`

**Authenticated user journeys with Keycloak integration.**

### Prerequisites

```bash
# Install k6 (if not already installed)
sudo gpg -k
sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
sudo apt-get update
sudo apt-get install k6
```

### Basic Usage

```bash
# Run with default settings (50 virtual users, 5 minutes)
k6 run load-test.js

# Run with custom number of users
k6 run -e MAX_VUS=100 load-test.js

# Run with custom duration
k6 run -e MAX_VUS=200 -e TEST_DURATION=10m load-test.js

# Run against different environment
k6 run -e BASE_URL=https://crewup-production.example.com -e MAX_VUS=150 load-test.js
```

## 📊 Test Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `MAX_VUS` | `50` | Maximum number of virtual users (concurrent connections) |
| `TEST_DURATION` | `5m` | Duration of sustained load phase (total test = 3m + TEST_DURATION) |
| `BASE_URL` | `https://crewup-staging.ltu-m7011e-3.se` | Target system URL |

### Test Stages

The test follows a realistic load profile:

```
1. Warm-up:     1 minute  - Ramp to 20% of MAX_VUS
2. Load:        TEST_DURATION - Sustain 100% of MAX_VUS (configurable, default 5m)
3. Sustain:     1 minute  - Maintain 100% of MAX_VUS
4. Cool-down:   1 minute  - Ramp down to 0
```

**Total test duration: 3 minutes + TEST_DURATION** (default: 8 minutes)

## 👥 User Scenarios

The test simulates 4 realistic user behavior patterns with weighted distribution:

### 1. Casual Browser (35%)
- Views homepage
- Browses events list
- Browses groups list
- Long think times (2-7 seconds)

### 2. Active User (30%)
- Views homepage
- Lists and views specific events
- Lists and views specific groups
- Checks ratings
- Medium think times (1-4 seconds)

### 3. Event Creator (20%)
- Checks existing events for inspiration
- Views multiple event details
- Browses groups
- Checks safety alerts
- Medium think times (1-4 seconds)

### 4. Data Reader (15%)
- Rapidly fetches data from all endpoints
- Short think times (0.5-2 seconds)
- Simulates API consumers or data aggregators

### 5. Health Monitor (10% probability)
- Validates all 6 service health endpoints
- Runs occasionally during any scenario

## 📈 Success Criteria

### HTTP Thresholds
- **P95 Response Time:** < 1000ms (95% of requests)
- **P99 Response Time:** < 2000ms (99% of requests)
- **HTTP Failure Rate:** < 1% (network/server errors)

### Application Thresholds
- **Application Error Rate:** < 1% (non-200 responses)
- **API Response Time P95:** < 800ms
- **API Response Time P99:** < 1500ms

### Breaking Point Indicators
- ❌ Error rate exceeds 5%
- ❌ P95 response time exceeds 2000ms
- ❌ Request failures due to "no route to host" or "i/o timeout"
- ❌ Service pods crashing (check with `kubectl get pods`)

## 📊 Metrics Explained

### Custom Metrics

| Metric | Description |
|--------|-------------|
| `error_rate` | Percentage of requests that returned non-200 status |
| `api_response_time` | End-to-end API response duration |
| `total_requests` | Total number of HTTP requests made |
| `scenario_browser` | Count of casual browser iterations |
| `scenario_active_user` | Count of active user iterations |
| `scenario_event_creator` | Count of event creator iterations |
| `scenario_data_reader` | Count of data reader iterations |

### Standard k6 Metrics

- `http_req_duration` - Total request time (DNS + TCP + TLS + Wait + Download)
- `http_req_failed` - Rate of failed HTTP requests
- `http_reqs` - Total HTTP requests and rate (RPS)
- `vus` - Current number of active virtual users
- `vus_max` - Maximum number of virtual users reached

## 🔍 Interpreting Results

### Healthy System
```
✅ ALL THRESHOLDS PASSED - System is healthy

HTTP Failure Rate: 0.00%
Application Error Rate: 0.00%
P95 Response Time: 450ms
P99 Response Time: 780ms
```

### System Under Stress
```
❌ THRESHOLDS FAILED - System is under stress

HTTP Failure Rate: 2.35%
Application Error Rate: 1.80%
P95 Response Time: 1850ms
P99 Response Time: 3200ms
```

**Recommended Actions:**
- Check pod resource usage: `kubectl top pods -n crewup-staging`
- Review pod logs: `kubectl logs -n crewup-staging <pod-name>`
- Monitor during test: `./monitor.sh` (in separate terminal)
- Consider horizontal pod autoscaling (HPA)
- Increase Ingress controller replicas

### System Failure
```
❌ THRESHOLDS FAILED - System is under stress

HTTP Failure Rate: 71.23%
Application Error Rate: 68.45%
Errors: "dial: i/o timeout", "no route to host"
```

**Critical Issues Detected:**
- Network/Ingress saturation
- Service connection exhaustion
- Pod crashes or OOMKill events

**Immediate Actions:**
1. Stop the test (`Ctrl+C`)
2. Check pod status: `kubectl get pods -n crewup-staging`
3. Check Ingress logs: `kubectl logs -n kube-system -l app.kubernetes.io/name=traefik`
4. Review resource limits in Helm values
5. Implement rate limiting

## 🎯 Recommended Test Scenarios

### Capacity Planning

Test different load levels to find optimal capacity:

```bash
# Light load
k6 run -e MAX_VUS=25 load-test.js

# Normal load  
k6 run -e MAX_VUS=50 load-test.js

# Heavy load
k6 run -e MAX_VUS=100 load-test.js

# Peak load
k6 run -e MAX_VUS=150 load-test.js

# Stress test (find breaking point)
k6 run -e MAX_VUS=200 load-test.js
k6 run -e MAX_VUS=300 load-test.js
k6 run -e MAX_VUS=500 load-test.js
```

### Endurance Testing

Test system stability over extended periods:

```bash
# 30-minute sustained load
k6 run -e MAX_VUS=50 -e TEST_DURATION=30m load-test.js

# 1-hour stability test
k6 run -e MAX_VUS=75 -e TEST_DURATION=1h load-test.js
```

### Performance Regression

Compare results before/after changes:

```bash
# Baseline (before changes)
k6 run -e MAX_VUS=100 load-test.js > baseline.txt

# After deployment
k6 run -e MAX_VUS=100 load-test.js > after-deployment.txt

# Compare response times and error rates
diff baseline.txt after-deployment.txt
```

## 📁 Output Files

Test results are saved to `results/` directory:

```
results/
├── summary-2025-12-09T16-30-45-123Z.json  # Full test metrics
├── summary-2025-12-09T17-15-22-456Z.json
└── ...
```

Each file contains:
- Complete metrics data
- Threshold evaluation results
- Percentile distributions
- Custom metric values

## 🛠️ Monitoring During Tests

### Real-time Kubernetes Monitoring

Run in a separate terminal while test is running:

```bash
# Watch pod status
watch kubectl get pods -n crewup-staging

# Monitor resource usage
watch kubectl top pods -n crewup-staging

# Follow pod logs (example: event service)
kubectl logs -n crewup-staging -l app=event -f

# Check Ingress traffic
kubectl logs -n kube-system -l app.kubernetes.io/name=traefik -f
```

### Using the Monitoring Script

```bash
# Run automated monitoring during test
./monitor.sh
```

This will display:
- Pod status and restarts
- CPU and memory usage
- Request rates
- Error rates

## 🏗️ System Architecture

CrewUp is a microservices-based platform with the following components:

```
┌─────────────┐
│   Browser   │
└──────┬──────┘
       │
       ↓
┌─────────────┐
│   Ingress   │ (Traefik)
└──────┬──────┘
       │
       ├───→ Frontend (Static SPA)
       │
       ├───→ Event Service
       ├───→ Group Service  
       ├───→ Rating Service
       ├───→ Safety Service
       ├───→ User Service
       └───→ Moderation Service
             │
             ↓
       ┌─────────────┐
       │  PostgreSQL │
       └─────────────┘
```

### Known Bottlenecks

Based on previous testing:

1. **Ingress Controller** - Primary bottleneck at ~200 concurrent users
2. **Database Connections** - Connection pool exhaustion under heavy load
3. **Network I/O** - Connection timeouts at extreme load (500+ users)

## 📚 Additional Tools

### Validate Endpoints

Before running load tests, validate which endpoints return 200:

```bash
./validate-endpoints.sh
```

This script tests all endpoints and shows:
- ✓ 200 OK (safe for load testing)
- ↻ 302 Redirect (requires authentication)
- ✗ 4xx/5xx Errors (service issues)

### Example Output

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ SAFE ENDPOINTS FOR LOAD TESTING (no auth required):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  - GET / (homepage)
  - GET /api/*/health (all health checks)
  - GET /api/event/events
  - GET /api/group/groups
  - GET /api/user/users
  - GET /api/rating/ratings
  - GET /api/safety/alerts
  - GET /api/moderation/reports
```

## 🎓 Academic Research

This load testing suite was developed for academic research at Luleå University of Technology (M7011E course) to evaluate:

1. **System Capacity** - Maximum sustainable concurrent users
2. **Performance Characteristics** - Response time distributions under various loads
3. **Breaking Point Analysis** - Failure modes and bottleneck identification
4. **Scalability Assessment** - Effectiveness of horizontal scaling strategies

### Research Findings

Key findings from load testing CrewUp (December 2025):

- **Safe Capacity:** ~140 concurrent users (with 30% safety margin)
- **Breaking Point:** ~200 concurrent users (71% error rate beyond this)
- **Primary Bottleneck:** Ingress controller (network saturation)
- **Secondary Bottleneck:** Database connection pooling
- **Failure Mode:** "no route to host" and "i/o timeout" errors

**Recommendations:**
1. Implement Horizontal Pod Autoscaling (HPA)
2. Increase Ingress controller replicas (2-3 replicas)
3. Add rate limiting (100 req/min per IP)
4. Optimize database connection pools
5. Consider CDN for static assets

## 📄 License

MIT License - See repository root for details.

## 👥 Contributors

- CrewUp Team
- Luleå University of Technology (M7011E)

## 🔗 Related Documentation

- [k6 Documentation](https://k6.io/docs/)
- [Kubernetes Best Practices](https://kubernetes.io/docs/concepts/)
- [Microservices Performance Patterns](https://microservices.io/)
