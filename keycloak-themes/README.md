# Keycloak Custom Theme

This directory contains the Docker image configuration for deploying a custom Keycloak theme built with [Keycloakify](https://www.keycloakify.dev/).

## Overview

The theme is packaged as a JAR file and deployed to Kubernetes using an Alpine-based Docker image. The theme files are copied into the Keycloak pod via an initContainer pattern.

## Structure

```
keycloak-themes/
├── Dockerfile           # Alpine image containing the theme JAR
├── crewup-theme.jar    # Built theme JAR from Keycloakify
└── README.md           # This file
```

## Building the Theme

### 1. Prerequisites

- Node.js 20+ and npm
- Maven 3.8+
- Docker

### 2. Clone and Setup Keycloakify Project

```bash
git clone https://github.com/nima70/keycloakify-tailwind-shadcn.git keycloak-theme
cd keycloak-theme
npm install --legacy-peer-deps
```

### 3. Customize Theme

Edit `src/styles/global.css` to match your brand colors:

```css
:root {
  --primary: 213 94% 68%;        /* Your primary color */
  --background: 0 0% 98%;         /* Background color */
  --radius: 0.75rem;              /* Border radius */
}
```

### 4. Build Theme JAR

```bash
npm run build-keycloak-theme
```

The JAR file will be generated in `build_keycloak/keycloak-theme-for-kc-22-and-above.jar`.

### 5. Copy JAR to Docker Context

```bash
cp keycloak-theme/build_keycloak/keycloak-theme-for-kc-22-and-above.jar keycloak-themes/crewup-theme.jar
```

## Docker Image

### Build and Push

```bash
cd keycloak-themes

# Build the image
docker build -t ghcr.io/YOUR_USERNAME/keycloak-theme:latest .

# Login to GitHub Container Registry
echo "YOUR_GITHUB_TOKEN" | docker login ghcr.io -u YOUR_USERNAME --password-stdin

# Push the image
docker push ghcr.io/YOUR_USERNAME/keycloak-theme:latest
```

### Make Package Public

1. Go to https://github.com/YOUR_USERNAME?tab=packages
2. Select the `keycloak-theme` package
3. Package settings → Change visibility → Public

## Kubernetes Deployment

The theme is deployed using an **initContainer** in the Keycloak deployment:

```yaml
initContainers:
- name: custom-theme
  image: ghcr.io/YOUR_USERNAME/keycloak-theme:latest
  imagePullPolicy: Always
  command: [sh, -c]
  args:
    - |
      echo "Copying theme..."
      cp -v /theme/*.jar /providers/
  volumeMounts:
    - name: theme
      mountPath: /providers
```

The theme JAR is copied to a shared `emptyDir` volume mounted at `/opt/keycloak/providers` in the Keycloak container.

### Deploy

```bash
cd keycloak-chart
helm upgrade keycloak . -n keycloak
```

## Activating the Theme

1. Access Keycloak Admin Console
2. Select your realm
3. Navigate to **Realm Settings** → **Themes**
4. Set **Login Theme** to `keycloakify-starter`
5. Save changes

## Updating the Theme

To update the theme with new changes:

```bash
# 1. Modify theme in keycloak-theme/src/
# 2. Rebuild JAR
cd keycloak-theme
npm run build-keycloak-theme

# 3. Update Docker image
cp build_keycloak/keycloak-theme-for-kc-22-and-above.jar ../keycloak-themes/crewup-theme.jar
cd ../keycloak-themes
docker build -t ghcr.io/YOUR_USERNAME/keycloak-theme:latest .
docker push ghcr.io/YOUR_USERNAME/keycloak-theme:latest

# 4. Force pod restart to pull new image
kubectl delete pod -n keycloak -l app=keycloak
```

## Technical Details

- **Base Image**: Alpine Linux (minimal footprint)
- **Theme Location in Image**: `/theme/crewup-theme.jar`
- **Keycloak Provider Path**: `/opt/keycloak/providers/`
- **Volume Type**: `emptyDir` (ephemeral, recreated on pod restart)
- **Theme Framework**: Keycloakify v10.0.5 (React + TailwindCSS + ShadCN UI)

## Resources

- [Keycloakify Documentation](https://www.keycloakify.dev/)
- [Keycloak Themes Guide](https://www.keycloak.org/docs/latest/server_development/#_themes)
- [Template Repository](https://github.com/nima70/keycloakify-tailwind-shadcn)
