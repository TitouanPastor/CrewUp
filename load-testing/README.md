# Load Testing

Performance testing suite for CrewUp using [k6](https://k6.io/).

## Quick Start

```bash
# Install k6
sudo apt-get install k6

# Run full scenario test (50 VUs, 5 min)
k6 run ./full-scenario-test.js

# Custom load
k6 run -e MAX_VUS=100 -e TEST_DURATION=2m ./full-scenario-test.js

# Cleanup test data after
./cleanup.sh
```

## Test Scripts

| Script | Description |
|--------|-------------|
| `full-scenario-test.js` | ⭐ Complete simulation with auth, WebSocket, events, groups |
| `realistic-user-test.js` | User journey simulation |
| `stress-test.js` | Find breaking points |
| `cleanup.sh` | Remove test data from database |

## User Scenarios Distribution

- 40% Casual Browsers (browse events/groups)
- 35% Active Users (join events, view profiles)
- 15% Chat Users (WebSocket messaging)
- 5% Group Creators (create events + groups)
- 3% Safety Alert Creators
- 2% Event Creators

## Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `MAX_VUS` | 50 | Concurrent virtual users |
| `TEST_DURATION` | 5m | Sustained load duration |
| `BASE_URL` | `https://crewup-staging.ltu-m7011e-3.se` | Target URL |

## Performance Analysis Results

Tests conducted on staging environment with Traefik Ingress.

### Throughput vs Latency

| VUs | Throughput (rps) | P95 Latency | Error Rate |
|-----|------------------|-------------|------------|
| 50 | ~32 | <1s | 0% |
| 100 | ~48 | <1.2s | 0% |
| 200 | ~63 | <1.6s | 0% |
| 300 | ~73 | ~6.9s | ~0.5% |
| 400 | ~67 | >10s | ~1.6% |
| 500 | ~67 | >10s | ~2.9% |

### Key Findings

1. **Optimal Range**: System performs well up to **~200 VUs**
   - Linear throughput scaling
   - P95 latency under 1.6s
   - Zero errors

2. **Saturation Point**: **300 VUs**
   - Peak throughput (~73 rps)
   - Latency spike to 6.9s
   - First errors appear

3. **Overload Zone**: **400+ VUs**
   - Throughput plateaus/degrades
   - P95 latency exceeds 10s
   - Request failures increase (timeouts on `/api/v1/events`)

### Bottleneck Identified

Primary bottleneck: Event Service under high write load
- Timeouts occur on event creation endpoints
- Database connection pool saturation suspected

### Recommendations

- Scale Event Service horizontally (increase replicas)
- Implement connection pooling (PgBouncer)
- Add caching for read-heavy endpoints
- Consider async event creation for high load

## Results Storage

Test results are saved in `results/` directory:
- JSON files with full metrics
- CSV summaries for analysis
- Merged reports for multi-run comparisons
