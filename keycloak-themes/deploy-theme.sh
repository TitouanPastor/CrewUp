#!/bin/bash
set -e

# Keycloak Theme Deployment Script
# This script extracts a Keycloakify JAR, adds a custom favicon, builds a Docker image, and deploys to Kubernetes

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FAVICON_PATH="${SCRIPT_DIR}/favicon.ico"
EXTRACTED_DIR="${SCRIPT_DIR}/crewup-theme-extracted"
THEME_PATH="theme/keycloakify-starter"
DOCKER_IMAGE="ghcr.io/titouanpastor/keycloak-theme:latest"
HELM_CHART_DIR="${SCRIPT_DIR}/../keycloak-chart"
NAMESPACE="keycloak"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# Check prerequisites
check_prerequisites() {
    info "Checking prerequisites..."
    
    command -v python3 >/dev/null 2>&1 || error "python3 is required but not installed"
    command -v docker >/dev/null 2>&1 || error "docker is required but not installed"
    command -v helm >/dev/null 2>&1 || error "helm is required but not installed"
    command -v kubectl >/dev/null 2>&1 || error "kubectl is required but not installed"
    
    info "All prerequisites satisfied"
}

# Usage information
usage() {
    cat << EOF
Usage: $0 <path-to-jar-file>

This script automates the deployment of a Keycloakify theme to Kubernetes.

Arguments:
    path-to-jar-file    Path to the Keycloakify JAR file (e.g., keycloak-theme-for-kc-22-and-above.jar)

Example:
    $0 ../keycloak-theme/build_keycloak/keycloak-theme-for-kc-22-and-above.jar

What this script does:
    1. Extracts the JAR file contents
    2. Copies the custom favicon from frontend/public/favicon.ico
    3. Builds a Docker image with the extracted theme
    4. Pushes the image to GitHub Container Registry
    5. Deploys to Kubernetes using Helm
    6. Waits for the deployment to complete
    7. Verifies the theme and favicon are correctly mounted

Environment Variables (optional):
    DOCKER_IMAGE        Docker image name (default: ghcr.io/titouanpastor/keycloak-theme:latest)
    NAMESPACE           Kubernetes namespace (default: keycloak)
    SKIP_DOCKER_PUSH    Set to 'true' to skip pushing the Docker image

EOF
    exit 1
}

# Validate arguments
if [ $# -ne 1 ]; then
    error "Missing required argument: path-to-jar-file"
    usage
fi

JAR_FILE="$1"

if [ ! -f "$JAR_FILE" ]; then
    error "JAR file not found: $JAR_FILE"
fi

# Main execution
main() {
    info "Starting Keycloak theme deployment"
    info "JAR file: $JAR_FILE"
    info "Docker image: $DOCKER_IMAGE"
    info "Namespace: $NAMESPACE"
    echo ""
    
    check_prerequisites
    
    # Step 1: Clean and extract JAR
    info "Step 1/7: Extracting JAR file..."
    if [ -d "$EXTRACTED_DIR" ]; then
        warn "Removing existing extracted directory"
        rm -rf "$EXTRACTED_DIR"
    fi
    
    mkdir -p "$EXTRACTED_DIR"
    python3 -m zipfile -e "$JAR_FILE" "$EXTRACTED_DIR"
    
    # Verify extraction
    if [ ! -d "$EXTRACTED_DIR/$THEME_PATH" ]; then
        error "Theme path not found in extracted JAR: $EXTRACTED_DIR/$THEME_PATH"
    fi
    
    info "JAR extracted successfully to: $EXTRACTED_DIR"
    
    # Step 2: Copy favicon
    info "Step 2/7: Copying custom favicon..."
    if [ ! -f "$FAVICON_PATH" ]; then
        error "Favicon not found: $FAVICON_PATH"
    fi
    
    FAVICON_DEST="$EXTRACTED_DIR/$THEME_PATH/login/resources/img/favicon.ico"
    mkdir -p "$(dirname "$FAVICON_DEST")"
    cp "$FAVICON_PATH" "$FAVICON_DEST"
    
    if [ ! -f "$FAVICON_DEST" ]; then
        error "Failed to copy favicon to: $FAVICON_DEST"
    fi
    
    info "Favicon copied successfully"
    
    # Step 3: Build Docker image
    info "Step 3/7: Building Docker image..."
    cd "$SCRIPT_DIR"
    docker build -t "$DOCKER_IMAGE" . || error "Docker build failed"
    info "Docker image built successfully"
    
    # Step 4: Push Docker image
    if [ "${SKIP_DOCKER_PUSH}" != "true" ]; then
        info "Step 4/7: Pushing Docker image to registry..."
        docker push "$DOCKER_IMAGE" || error "Docker push failed"
        info "Docker image pushed successfully"
    else
        warn "Step 4/7: Skipping Docker push (SKIP_DOCKER_PUSH=true)"
    fi
    
    # Step 5: Deploy with Helm
    info "Step 5/7: Deploying to Kubernetes with Helm..."
    cd "$HELM_CHART_DIR"
    helm upgrade --install keycloak . -n "$NAMESPACE" --create-namespace || error "Helm deployment failed"
    info "Helm deployment initiated"
    
    # Force restart to pull new image (since we use 'latest' tag)
    info "Forcing pod restart to pull new image..."
    kubectl -n "$NAMESPACE" rollout restart deployment/keycloak || error "Failed to restart deployment"
    
    # Step 6: Wait for rollout
    info "Step 6/7: Waiting for deployment to complete..."
    kubectl -n "$NAMESPACE" rollout status deployment/keycloak --timeout=5m || error "Rollout failed or timed out"
    info "Deployment completed successfully"

    # small delay to ensure pods are fully ready
    sleep 10
    
    # Step 7: Verify installation
    info "Step 7/7: Verifying theme installation..."
    POD=$(kubectl -n "$NAMESPACE" get pods -l app=keycloak -o jsonpath='{.items[0].metadata.name}')
    
    if [ -z "$POD" ]; then
        error "No Keycloak pod found"
    fi
    
    info "Checking theme directory..."
    kubectl -n "$NAMESPACE" exec -it "$POD" -- ls -la /opt/keycloak/themes/ > /dev/null 2>&1 || error "Theme directory not accessible"
    
    info "Checking favicon..."
    kubectl -n "$NAMESPACE" exec -it "$POD" -- test -f /opt/keycloak/themes/crewup-theme/login/resources/img/favicon.ico || error "Favicon not found in pod"
    
    echo ""
    info "✓ Deployment completed successfully!"
    echo ""
    info "Next steps:"
    echo "  1. Open Keycloak Admin Console: https://keycloak.ltu-m7011e-3.se"
    echo "  2. Navigate to: Realm Settings → Themes → Login Theme"
    echo "  3. Select 'crewup-theme' from the dropdown"
    echo "  4. Click Save"
    echo "  5. Test the login page in incognito mode to see the new theme"
    echo ""
    info "To verify the deployment manually:"
    echo "  kubectl -n $NAMESPACE exec -it $POD -- ls -la /opt/keycloak/themes/crewup-theme/login/resources/img/"
    echo ""
}

# Run main function
main
