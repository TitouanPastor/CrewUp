# Keycloak Custom Theme

This directory contains the Docker image configuration for deploying a custom Keycloak theme built with [Keycloakify](https://www.keycloakify.dev/).

## Overview

The theme is extracted from a Keycloakify JAR file and deployed to Kubernetes using an Alpine-based Docker image. The extracted theme files are copied into the Keycloak pod via an initContainer pattern and mounted directly in `/opt/keycloak/themes/`.

## Structure

```
keycloak-themes/
├── Dockerfile                  # Alpine image containing the extracted theme
├── crewup-theme-extracted/     # Extracted theme files (gitignored)
├── deploy-theme.sh             # Automated deployment script
└── README.md                   # This file
```

## Quick Start

Use the automated script to extract, build, and deploy the theme:

```bash
./deploy-theme.sh /path/to/keycloak-theme-for-kc-22-and-above.jar
```

This script will:
1. Extract the JAR contents
2. Copy the favicon from `../frontend/public/favicon.ico`
3. Build and push the Docker image
4. Deploy to Kubernetes via Helm

## Manual Process

### 1. Prerequisites

- Python 3 (for JAR extraction)
- Docker
- Helm 3
- kubectl configured for your cluster

### 2. Build Theme JAR

From the Keycloakify project:

```bash
cd ../keycloak-theme
npm install --legacy-peer-deps
npm run build-keycloak-theme
```

The JAR will be generated in `build_keycloak/keycloak-theme-for-kc-22-and-above.jar`.

### 3. Extract JAR and Add Favicon

```bash
cd ../keycloak-themes

# Extract JAR using Python
python3 -m zipfile -e ../keycloak-theme/build_keycloak/keycloak-theme-for-kc-22-and-above.jar crewup-theme-extracted

# Copy favicon
cp ../frontend/public/favicon.ico crewup-theme-extracted/theme/keycloakify-starter/login/resources/img/favicon.ico
```

### 4. Build Docker Image

```bash
docker build -t ghcr.io/titouanpastor/keycloak-theme:latest .
```

### 5. Push to Registry

```bash
docker push ghcr.io/titouanpastor/keycloak-theme:latest
```

### 6. Deploy with Helm

```bash
cd ../keycloak-chart
helm upgrade --install keycloak . -n keycloak --create-namespace
kubectl -n keycloak rollout status deployment/keycloak
```

## Kubernetes Deployment Details

The theme is deployed using an **initContainer** that copies the extracted theme files:

```yaml
initContainers:
- name: custom-theme
  image: ghcr.io/titouanpastor/keycloak-theme:latest
  imagePullPolicy: Always
  command: [sh, -c]
  args:
    - |
      echo "Copying CrewUp theme to /themes..."
      cp -rv /theme/crewup-theme /themes/
  volumeMounts:
    - name: theme
      mountPath: /themes
```

The Keycloak container mounts the same volume at `/opt/keycloak/themes/`:

```yaml
containers:
- name: keycloak
  volumeMounts:
  - name: theme
    mountPath: /opt/keycloak/themes
```

## Activating the Theme

1. Access Keycloak Admin Console: `https://keycloak.ltu-m7011e-3.se`
2. Select your realm (e.g., `crewup`)
3. Navigate to **Realm Settings** → **Themes** → **Login Theme**
4. Select `crewup-theme` from the dropdown
5. Click **Save**
6. Test the login page in incognito mode to see the new theme and favicon

## Favicon Location

The favicon must be placed at:
```
crewup-theme-extracted/theme/keycloakify-starter/login/resources/img/favicon.ico
```

It will be accessible in Keycloak at:
```
/realms/{realm}/login-actions/resources/{version}/crewup-theme/login/img/favicon.ico
```

## Updating the Theme

To update with new changes:

```bash
# Option 1: Use the automated script
./deploy-theme.sh ../keycloak-theme/build_keycloak/keycloak-theme-for-kc-22-and-above.jar

# Option 2: Manual steps
cd ../keycloak-theme
npm run build-keycloak-theme

cd ../keycloak-themes
rm -rf crewup-theme-extracted
python3 -m zipfile -e ../keycloak-theme/build_keycloak/keycloak-theme-for-kc-22-and-above.jar crewup-theme-extracted
cp ../frontend/public/favicon.ico crewup-theme-extracted/theme/keycloakify-starter/login/resources/img/favicon.ico

docker build -t ghcr.io/titouanpastor/keycloak-theme:latest .
docker push ghcr.io/titouanpastor/keycloak-theme:latest

# Force pod restart to pull new image
kubectl -n keycloak rollout restart deployment/keycloak
```

## Verifying Deployment

Check that the theme is mounted correctly:

```bash
POD=$(kubectl -n keycloak get pods -l app=keycloak -o jsonpath='{.items[0].metadata.name}')

# Verify theme directory
kubectl -n keycloak exec -it $POD -- ls -la /opt/keycloak/themes/

# Verify favicon
kubectl -n keycloak exec -it $POD -- ls -la /opt/keycloak/themes/crewup-theme/login/resources/img/favicon.ico
```

## Technical Details

- **Base Image**: Alpine Linux (minimal footprint)
- **Theme Name**: `crewup-theme` (from `keycloakify-starter`)
- **Theme Location in Image**: `/theme/crewup-theme/`
- **Keycloak Mount Path**: `/opt/keycloak/themes/crewup-theme/`
- **Volume Type**: `emptyDir` (ephemeral, recreated on pod restart)
- **Theme Framework**: Keycloakify v10+ (React + TailwindCSS + ShadCN UI)
- **Favicon Format**: ICO/PNG (130KB, transparent background)

## Troubleshooting

### Theme not appearing in dropdown

1. Check pod logs: `kubectl -n keycloak logs -l app=keycloak --tail=100`
2. Verify theme is mounted: `kubectl -n keycloak exec -it $POD -- ls /opt/keycloak/themes/`
3. Restart Keycloak: `kubectl -n keycloak rollout restart deployment/keycloak`

### Favicon not showing

1. Clear browser cache or test in incognito mode
2. Verify favicon exists: `kubectl -n keycloak exec -it $POD -- ls -la /opt/keycloak/themes/crewup-theme/login/resources/img/favicon.ico`
3. Check browser DevTools → Network tab for favicon request (should be 200, not 404)

### Old theme still showing

1. Make sure you selected `crewup-theme` in Realm Settings → Themes → Login Theme
2. Clear Keycloak cache: `kubectl -n keycloak delete pod -l app=keycloak`
3. Hard refresh the login page: Ctrl+Shift+R (Windows/Linux) or Cmd+Shift+R (Mac)

## Resources

- [Keycloakify Documentation](https://www.keycloakify.dev/)
- [Keycloak Themes Guide](https://www.keycloak.org/docs/latest/server_development/#_themes)
- [Template Repository](https://github.com/nima70/keycloakify-tailwind-shadcn)
- [CrewUp Project](https://github.com/TitouanPastor/CrewUp)