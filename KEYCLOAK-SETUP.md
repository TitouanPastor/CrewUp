# 🔐 Keycloak Multi-Environment Setup

## Vue d'ensemble

Pour chaque environnement (dev, staging, production), tu dois créer un **client Keycloak séparé** avec des URLs et CORS configurés spécifiquement.

---

## Clients Keycloak à créer

| Environnement | Client ID | Frontend URL | Valid Redirect URIs | Web Origins |
|---------------|-----------|--------------|---------------------|-------------|
| **Dev** | `crewup-dev` | `https://crewup-dev.ltu-m7011e-3.se` | `https://crewup-dev.ltu-m7011e-3.se/*` | `https://crewup-dev.ltu-m7011e-3.se` |
| **Staging** | `crewup-staging` | `https://crewup-staging.ltu-m7011e-3.se` | `https://crewup-staging.ltu-m7011e-3.se/*` | `https://crewup-staging.ltu-m7011e-3.se` |
| **Production** | `crewup-production` | `https://crewup.ltu-m7011e-3.se` | `https://crewup.ltu-m7011e-3.se/*` | `https://crewup.ltu-m7011e-3.se` |

---

## 📝 Instructions de Création (via Keycloak Admin Console)

### 1. Se connecter à Keycloak Admin

```
URL: https://keycloak.ltu-m7011e-3.se/admin
Realm: crewup
```

### 2. Créer le Client DEV

1. **Clients** → **Create client**
2. **General Settings:**
   - Client type: `OpenID Connect`
   - Client ID: `crewup-dev`
   - Name: `CrewUp Development`
   - Description: `Development environment client`
   - Click **Next**

3. **Capability config:**
   - Client authentication: `OFF` (public client)
   - Authorization: `OFF`
   - Authentication flow:
     - ✅ Standard flow
     - ✅ Direct access grants
   - Click **Next**

4. **Login settings:**
   - Root URL: `https://crewup-dev.ltu-m7011e-3.se`
   - Home URL: `https://crewup-dev.ltu-m7011e-3.se`
   - Valid redirect URIs:
     - `https://crewup-dev.ltu-m7011e-3.se/*`
   - Valid post logout redirect URIs:
     - `https://crewup-dev.ltu-m7011e-3.se/*`
   - Web origins:
     - `https://crewup-dev.ltu-m7011e-3.se`
   - Click **Save**

### 3. Créer le Client STAGING

Répète les mêmes étapes avec :
- Client ID: `crewup-staging`
- Name: `CrewUp Staging`
- Description: `Staging environment client`
- Root URL: `https://crewup-staging.ltu-m7011e-3.se`
- Home URL: `https://crewup-staging.ltu-m7011e-3.se`
- Valid redirect URIs: `https://crewup-staging.ltu-m7011e-3.se/*`
- Valid post logout redirect URIs: `https://crewup-staging.ltu-m7011e-3.se/*`
- Web origins: `https://crewup-staging.ltu-m7011e-3.se`

### 4. Créer le Client PRODUCTION

Répète avec :
- Client ID: `crewup-production`
- Name: `CrewUp Production`
- Description: `Production environment client`
- Root URL: `https://crewup.ltu-m7011e-3.se`
- Home URL: `https://crewup.ltu-m7011e-3.se`
- Valid redirect URIs: `https://crewup.ltu-m7011e-3.se/*`
- Valid post logout redirect URIs: `https://crewup.ltu-m7011e-3.se/*`
- Web origins: `https://crewup.ltu-m7011e-3.se`

---

## 🤖 Alternative : Script Automatique (Optionnel)

Si tu veux créer les clients via API au lieu de l'UI :

```bash
# Installer jq si pas déjà fait
sudo apt-get install jq -y  # Linux
brew install jq             # macOS

# Script de création automatique
./keycloak-commands/create-clients.sh
```

<details>
<summary>Voir le script create-clients.sh</summary>

```bash
#!/bin/bash

KEYCLOAK_URL="https://keycloak.ltu-m7011e-3.se"
REALM="crewup"
ADMIN_USER="admin"
ADMIN_PASSWORD="votre_mot_de_passe"

# Get admin token
TOKEN=$(curl -s -X POST "$KEYCLOAK_URL/realms/master/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=$ADMIN_USER" \
  -d "password=$ADMIN_PASSWORD" \
  -d "grant_type=password" \
  -d "client_id=admin-cli" | jq -r '.access_token')

# Function to create client
create_client() {
  local CLIENT_ID=$1
  local ROOT_URL=$2
  local NAME=$3
  
  curl -s -X POST "$KEYCLOAK_URL/admin/realms/$REALM/clients" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
      \"clientId\": \"$CLIENT_ID\",
      \"name\": \"$NAME\",
      \"description\": \"$NAME environment client\",
      \"rootUrl\": \"$ROOT_URL\",
      \"baseUrl\": \"$ROOT_URL\",
      \"enabled\": true,
      \"publicClient\": true,
      \"redirectUris\": [\"$ROOT_URL/*\"],
      \"webOrigins\": [\"$ROOT_URL\"],
      \"standardFlowEnabled\": true,
      \"directAccessGrantsEnabled\": true
    }"
  
  echo "Created client: $CLIENT_ID"
}

# Create clients
create_client "crewup-dev" "https://crewup-dev.ltu-m7011e-3.se" "CrewUp Development"
create_client "crewup-staging" "https://crewup-staging.ltu-m7011e-3.se" "CrewUp Staging"
create_client "crewup-production" "https://crewup.ltu-m7011e-3.se" "CrewUp Production"

echo "✅ All clients created successfully!"
```

</details>

---

## 🔍 Vérification

Après création, vérifie dans **Keycloak Admin Console** → **Clients** :

```bash
# Tu devrais voir 3 nouveaux clients :
✅ crewup-dev
✅ crewup-staging
✅ crewup-production
```

Pour chaque client, vérifie :
- ✅ **Settings** → Client authentication: `OFF`
- ✅ **Settings** → Valid redirect URIs: correcte
- ✅ **Settings** → Web origins: correcte
- ✅ **Credentials** → N/A (public client, pas de secret)

---

## 🧪 Test de Connexion

### Dev
```bash
# Ouvre le frontend dev
https://crewup-dev.ltu-m7011e-3.se

# Vérifie la console navigateur
window.__RUNTIME_CONFIG__
# Doit afficher:
# {
#   VITE_KEYCLOAK_URL: "https://keycloak.ltu-m7011e-3.se",
#   VITE_KEYCLOAK_REALM: "crewup",
#   VITE_KEYCLOAK_CLIENT_ID: "crewup-dev"
# }
```

### Staging
```bash
https://crewup-staging.ltu-m7011e-3.se
# Vérifie VITE_KEYCLOAK_CLIENT_ID === "crewup-staging"
```

### Production
```bash
https://crewup.ltu-m7011e-3.se
# Vérifie VITE_KEYCLOAK_CLIENT_ID === "crewup-production"
```

---

## 🐛 Troubleshooting

### Erreur CORS

**Symptôme:** Console navigateur montre `CORS policy: No 'Access-Control-Allow-Origin'`

**Solution:**
1. Keycloak Admin → Clients → `crewup-{env}`
2. **Settings** tab
3. Vérifie **Web origins** contient bien `https://crewup-{env}.ltu-m7011e-3.se`
4. **Save**

### Erreur "Invalid redirect_uri"

**Symptôme:** Keycloak erreur après login

**Solution:**
1. Keycloak Admin → Clients → `crewup-{env}`
2. **Settings** tab
3. Vérifie **Valid redirect URIs** contient `https://crewup-{env}.ltu-m7011e-3.se/*`
4. **Save**

### Erreur "client_not_found"

**Symptôme:** Logs backend montrent `client_not_found`

**Solution:**
1. Vérifie que le client existe dans Keycloak
2. Vérifie que `environments/{env}/values.yaml` a le bon `keycloak.clientId`
3. Redéploie : `argocd app sync crewup-{env}`

### Variables d'environnement non injectées

**Symptôme:** `window.__RUNTIME_CONFIG__` est `undefined`

**Solution:**
```bash
# Vérifie les logs du pod frontend
kubectl logs -n crewup-{env} -l app=frontend

# Vérifie le fichier config.js généré
kubectl exec -n crewup-{env} -l app=frontend -- cat /usr/share/nginx/html/config.js

# Devrait afficher quelque chose comme :
# window.__RUNTIME_CONFIG__ = {
#   VITE_KEYCLOAK_CLIENT_ID: 'crewup-dev',
#   ...
# };
```

---

## 📚 Résumé

**Avant (problème) :**
- ❌ 1 seul client Keycloak pour tous les environnements
- ❌ Variables hardcodées dans Dockerfile
- ❌ CORS configuré seulement pour prod

**Après (solution) :**
- ✅ 3 clients Keycloak séparés (dev, staging, production)
- ✅ Variables injectées via Helm values.yaml
- ✅ Configuration runtime (pas build-time)
- ✅ CORS et redirects corrects par environnement
- ✅ Facile à maintenir et à déboguer

---

## 🎯 Prochaines Étapes

1. ✅ Créer les 3 clients Keycloak (via UI ou script)
2. ✅ Commit et push les changements de code
3. ✅ Build et deploy vers dev (auto via CI/CD)
4. ✅ Tester l'authentification sur dev
5. ✅ Promouvoir vers staging et tester
6. ✅ Promouvoir vers production

Bon setup ! 🚀
