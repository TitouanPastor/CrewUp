# Safety Service - Corrections et Améliorations

## Résumé des changements

Le service safety a été entièrement corrigé et aligné sur les autres services (event, group, user) pour fonctionner correctement en local et sur Kubernetes.

## Changements principaux

### 1. Configuration (`app/config.py`)
- ✅ Migration de `pydantic_settings.BaseSettings` vers le pattern `Config` statique utilisé par les autres services
- ✅ Ajout de la méthode `get_database_url()` pour supporter à la fois DATABASE_URL et les variables POSTGRES_* individuelles
- ✅ Configuration CORS harmonisée avec liste au lieu de string
- ✅ URLs des services (GROUP_SERVICE_URL, EVENT_SERVICE_URL) correctement configurées

### 2. Base de données (`app/db/`)
- ✅ Correction de `database.py` pour utiliser `config.get_database_url()`
- ✅ Support SQLite pour les tests (détection automatique et configuration adaptée)
- ✅ Modèles (`models.py`) avec type UUID compatible SQLite et PostgreSQL
- ✅ Suppression de ARRAY(Text) qui n'est pas compatible SQLite

### 3. Logging (`app/utils/logging.py`)
- ✅ Migration vers logging JSON structuré avec `python-json-logger`
- ✅ Aligné sur le pattern des autres services

### 4. Exceptions (`app/utils/exceptions.py`)
- ✅ Ajout des exception handlers standards: `validation_exception_handler`, `database_exception_handler`, `generic_exception_handler`
- ✅ Ajout des exceptions personnalisées: `NotFoundException`, `BadRequestException`, `ForbiddenException`, `UnauthorizedException`
- ✅ Remplacement de `SafetyException` par les exceptions appropriées

### 5. Routes (`app/routers/`)
- ✅ Consolidation dans `__init__.py` (suppression de `alerts.py` redondant)
- ✅ Export correct de `alerts_router`
- ✅ Correction de l'URL du broadcast vers le service group: `/api/v1/groups/internal/broadcast/{group_id}`
- ✅ Utilisation des bonnes exceptions

### 6. Modèles Pydantic (`app/models/`)
- ✅ Suppression de `alert.py` redondant
- ✅ Modèles dans `__init__.py` avec tous les champs nécessaires
- ✅ `SafetyAlertCreate`, `SafetyAlertResponse`, `SafetyAlertListResponse`, `ResolveAlertRequest`, `AlertBroadcast`

### 7. Middleware d'authentification (`app/middleware/auth.py`)
- ✅ Correction de l'import: `HTTPAuthorizationCredentials` au lieu de `HTTPAuthCredential`
- ✅ Utilisation de `config.KEYCLOAK_SERVER_URL` au lieu de `config.keycloak_server_url`

### 8. Application principale (`app/main.py`)
- ✅ Ajout des exception handlers
- ✅ Startup event avec gestion du log de l'URL de base de données (compatible SQLite et PostgreSQL)
- ✅ Configuration CORS correcte avec liste

### 9. Tests
- ✅ Tests simplifiés et fonctionnels avec `app.dependency_overrides`
- ✅ Mock de `get_current_user` via dependency injection (plus besoin de patch)
- ✅ Correction des URLs des endpoints: `/api/v1/alerts`
- ✅ Ajout du fichier `.env.test`
- ✅ 5 tests de base qui passent : health check, création, liste, récupération, résolution

**Note importante sur les tests :** Les tests utilisent `app.dependency_overrides` dans le conftest pour mocker l'authentification. C'est la bonne pratique recommandée par FastAPI au lieu d'utiliser `patch()`. Cela évite les erreurs de connexion à Keycloak pendant les tests.

### 10. Helm / Kubernetes
- ✅ Correction de l'Ingress: route `/api/v1/alerts` au lieu de `/api/v1/safety`
- ✅ Service déjà configuré dans `values.yaml`

### 11. Docker
- ✅ `docker-compose.yaml` déjà configuré sur le port 8004
- ✅ Variables d'environnement correctes (GROUP_SERVICE_URL, EVENT_SERVICE_URL)

## Dépendances ajoutées

- `python-json-logger==2.0.7` pour le logging structuré

## URLs et Endpoints

### En local (docker-compose)
- Service: `http://localhost:8004`
- API Docs: `http://localhost:8004/api/v1/alerts/docs`
- Health: `http://localhost:8004/health`

### Sur Kubernetes
- Via Ingress: `https://crewup.ltu-m7011e-3.se/api/v1/alerts`
- Docs: `https://crewup.ltu-m7011e-3.se/api/v1/alerts/docs`

## Endpoints principaux

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| POST | `/api/v1/alerts` | Créer une alerte de sécurité |
| GET | `/api/v1/alerts` | Lister les alertes (avec filtres) |
| GET | `/api/v1/alerts/{id}` | Récupérer une alerte spécifique |
| PATCH | `/api/v1/alerts/{id}/resolve` | Résoudre une alerte |
| DELETE | `/api/v1/alerts/{id}` | Supprimer une alerte |

## Comment tester

### En local avec docker-compose
```bash
# Démarrer le service
docker-compose up --build -d safety

# Voir les logs
docker-compose logs -f safety

# Accéder à la doc Swagger
firefox http://localhost:8004/api/v1/alerts/docs
```

### Tests unitaires
```bash
cd safety
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest tests/ -v

# Avec couverture
pytest tests/ --cov=app --cov-report=html
```

**Note :** Les tests utilisent SQLite en mémoire et mockent l'authentification via `app.dependency_overrides`. Pas besoin de base de données PostgreSQL pour les tests unitaires.

### Sur Kubernetes
Le service est déjà configuré dans le Helm chart. Il sera déployé automatiquement lors du déploiement de l'application.

## Fonctionnalités

### Création d'alerte
- L'utilisateur doit être authentifié
- L'utilisateur doit être membre du groupe
- L'événement associé au groupe doit être en cours (entre event_start et event_end)
- L'alerte est broadcastée via WebSocket à tous les membres du groupe

### Types d'alertes
- `help` : Demande d'aide
- `emergency` : Urgence
- `other` : Autre

### Résolution d'alerte
- Tout membre peut résoudre une alerte
- L'alerte est marquée avec `resolved_at` et `resolved_by_user_id`

## Notes techniques

### Intégration avec le service Group
Le service safety communique avec le service group pour broadcaster les alertes via WebSocket. L'endpoint utilisé est:
```
POST /api/v1/groups/internal/broadcast/{group_id}
```

### Base de données
Les tables utilisées (partagées avec les autres services):
- `users` : Utilisateurs (lecture seule)
- `events` : Événements (lecture seule)
- `groups` : Groupes (lecture seule)
- `group_members` : Membres des groupes (lecture seule)
- `safety_alerts` : Alertes de sécurité (gérée par ce service)

### Variables d'environnement

```bash
# Base de données
DATABASE_URL=postgresql://user:pass@host:port/db
# OU
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=crewup
POSTGRES_PASSWORD=crewup_dev_password
POSTGRES_DB=crewup

# Keycloak
KEYCLOAK_SERVER_URL=https://keycloak.ltu-m7011e-3.se
KEYCLOAK_REALM=crewup
KEYCLOAK_CLIENT_ID=crewup-frontend

# Services
GROUP_SERVICE_URL=http://localhost:8002
EVENT_SERVICE_URL=http://localhost:8001

# CORS
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# Logging
LOG_LEVEL=INFO
```

## Prochaines étapes possibles

- [ ] Ajouter plus de tests (tests négatifs, edge cases, etc.)
- [ ] Ajouter des tests d'intégration avec la vraie base de données PostgreSQL
- [ ] Ajouter des métriques Prometheus
- [ ] Ajouter des notifications push en plus des WebSockets
- [ ] Gérer les permissions (seuls les admins peuvent résoudre certaines alertes)
- [ ] Remplacer `datetime.utcnow()` par `datetime.now(timezone.utc)` pour éviter les deprecation warnings

## Solution au problème d'authentification dans les tests

Le problème principal était que les tests essayaient de contacter Keycloak pour vérifier les tokens, ce qui échouait avec une erreur réseau. 

**Solution :** Utiliser `app.dependency_overrides` dans le conftest pour remplacer la fonction `get_current_user` par un mock qui retourne directement les données de l'utilisateur de test. C'est la méthode recommandée par FastAPI.

```python
# Dans conftest.py
def override_get_current_user():
    return mock_current_user

app.dependency_overrides[get_current_user] = override_get_current_user
```

Cette approche est bien meilleure que d'utiliser `patch()` car elle s'intègre naturellement avec le système de dépendances de FastAPI.
