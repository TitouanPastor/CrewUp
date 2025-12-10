#!/bin/bash

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CrewUp Load Test Monitor
# Real-time monitoring of system metrics during load testing
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

NAMESPACE="${NAMESPACE:-crewup-staging}"
REFRESH_INTERVAL="${REFRESH_INTERVAL:-5}"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 CrewUp Load Test Monitor"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Namespace: $NAMESPACE"
echo "Refresh Interval: ${REFRESH_INTERVAL}s"
echo "Press Ctrl+C to stop"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if namespace exists
if ! kubectl get namespace "$NAMESPACE" &>/dev/null; then
    echo -e "${RED}❌ Namespace '$NAMESPACE' not found${NC}"
    exit 1
fi

# Function to get pod status with color coding
get_pod_status() {
    local status=$1
    case $status in
        Running)
            echo -e "${GREEN}●${NC} $status"
            ;;
        Pending)
            echo -e "${YELLOW}◐${NC} $status"
            ;;
        Failed|Error|CrashLoopBackOff)
            echo -e "${RED}✗${NC} $status"
            ;;
        *)
            echo "○ $status"
            ;;
    esac
}

# Function to display metrics
display_metrics() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}📊 Metrics at $timestamp${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
    
    # Pod Status
    echo -e "${YELLOW}🔧 Pod Status:${NC}"
    printf "%-30s %-15s %-10s %s\n" "NAME" "STATUS" "RESTARTS" "AGE"
    printf "%-30s %-15s %-10s %s\n" "────────────────────────────" "──────────" "────────" "───"
    
    kubectl get pods -n "$NAMESPACE" --no-headers 2>/dev/null | while read -r line; do
        name=$(echo "$line" | awk '{print $1}')
        ready=$(echo "$line" | awk '{print $2}')
        status=$(echo "$line" | awk '{print $3}')
        restarts=$(echo "$line" | awk '{print $4}')
        age=$(echo "$line" | awk '{print $5}')
        
        status_colored=$(get_pod_status "$status")
        
        # Highlight high restart counts
        if [ "$restarts" -gt 5 ]; then
            restarts="${RED}$restarts${NC}"
        elif [ "$restarts" -gt 0 ]; then
            restarts="${YELLOW}$restarts${NC}"
        fi
        
        printf "%-30s %-25s %-18s %s\n" "$name" "$status_colored" "$restarts" "$age"
    done
    
    # Resource Usage
    echo -e "\n${YELLOW}💻 Resource Usage:${NC}"
    
    if kubectl top pods -n "$NAMESPACE" &>/dev/null; then
        printf "%-30s %-15s %s\n" "NAME" "CPU" "MEMORY"
        printf "%-30s %-15s %s\n" "────────────────────────────" "──────────" "──────────"
        
        kubectl top pods -n "$NAMESPACE" --no-headers 2>/dev/null | while read -r line; do
            name=$(echo "$line" | awk '{print $1}')
            cpu=$(echo "$line" | awk '{print $2}')
            memory=$(echo "$line" | awk '{print $3}')
            
            # Color code high CPU usage (>500m = 50%)
            cpu_num=$(echo "$cpu" | sed 's/m//')
            if [ "$cpu_num" -gt 800 ]; then
                cpu="${RED}$cpu${NC}"
            elif [ "$cpu_num" -gt 500 ]; then
                cpu="${YELLOW}$cpu${NC}"
            fi
            
            # Color code high memory usage (>500Mi)
            memory_num=$(echo "$memory" | sed 's/Mi//')
            if [ "$memory_num" -gt 800 ]; then
                memory="${RED}$memory${NC}"
            elif [ "$memory_num" -gt 500 ]; then
                memory="${YELLOW}$memory${NC}"
            fi
            
            printf "%-30s %-23s %s\n" "$name" "$cpu" "$memory"
        done
    else
        echo "  ⚠️  metrics-server not available - install with:"
        echo "  kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml"
    fi
    
    # Recent Events (warnings and errors only)
    echo -e "\n${YELLOW}📋 Recent Events (Warnings/Errors):${NC}"
    events=$(kubectl get events -n "$NAMESPACE" --sort-by='.lastTimestamp' --field-selector type!=Normal 2>/dev/null | tail -n 5)
    
    if [ -z "$events" ] || [ "$(echo "$events" | wc -l)" -le 1 ]; then
        echo -e "  ${GREEN}✓${NC} No recent warnings or errors"
    else
        echo "$events" | tail -n +2 | while read -r line; do
            echo "  $line"
        done
    fi
    
    # Ingress Status
    echo -e "\n${YELLOW}🌐 Ingress Controller (Traefik):${NC}"
    traefik_pods=$(kubectl get pods -n kube-system -l app.kubernetes.io/name=traefik --no-headers 2>/dev/null | wc -l)
    if [ "$traefik_pods" -gt 0 ]; then
        kubectl get pods -n kube-system -l app.kubernetes.io/name=traefik --no-headers 2>/dev/null | while read -r line; do
            name=$(echo "$line" | awk '{print $1}')
            status=$(echo "$line" | awk '{print $3}')
            status_colored=$(get_pod_status "$status")
            echo "  $name: $status_colored"
        done
        
        # Get Traefik resource usage if metrics-server is available
        if kubectl top pods -n kube-system &>/dev/null; then
            kubectl top pods -n kube-system -l app.kubernetes.io/name=traefik --no-headers 2>/dev/null | while read -r line; do
                name=$(echo "$line" | awk '{print $1}')
                cpu=$(echo "$line" | awk '{print $2}')
                memory=$(echo "$line" | awk '{print $3}')
                echo "  └─ CPU: $cpu, Memory: $memory"
            done
        fi
    else
        echo "  ⚠️  No Traefik pods found"
    fi
    
    echo ""
}

# Main monitoring loop
while true; do
    clear
    display_metrics
    sleep "$REFRESH_INTERVAL"
done
