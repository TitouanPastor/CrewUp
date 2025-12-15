#!/usr/bin/env bash
set -uo pipefail   # <- enlève -e

mkdir -p results logs
RUN_ID="crewup_$(date +%Y-%m-%d_%H-%M-%S)"
VUS_LIST=(50 100 200 300 400 500)

for vus in "${VUS_LIST[@]}"; do
  echo "===== Testing with ${vus} VUs ====="

  k6 run \
    -e RUN_ID="$RUN_ID" \
    -e MAX_VUS="$vus" \
    -e TEST_DURATION="5m" \
    ./full-scenario-test.js \
    > "logs/${RUN_ID}_vus-${vus}.log" 2>&1

  K6_RC=$?
  echo "k6 exit code: $K6_RC" >> "logs/${RUN_ID}_vus-${vus}.log"

  echo "cleanup..."
  ./cleanup.sh >> "logs/${RUN_ID}_vus-${vus}.log" 2>&1 || true

  echo "sleep 15s..."
  sleep 15
done
