# Configuration des Tests Automatisés avec GitHub Actions

## 🎯 Vue d'Ensemble

Ce projet utilise GitHub Actions pour exécuter automatiquement tous les tests lors de chaque Pull Request. Les tests doivent passer avant de pouvoir merger sur la branche `main`.

### Architecture Intelligente

Le système de tests s'adapte automatiquement à l'environnement :

- **GitHub Actions (CI)** : Utilise PostgreSQL service container, tests unitaires uniquement
- **Local** : Peut utiliser votre DB locale/Docker, tests unitaires OU complets

## 🏗️ Architecture

### Base de Données de Test

#### Sur GitHub Actions (CI)
PostgreSQL 15 en service container :
```yaml
services:
  postgres:
    image: postgres:15
    env:
      POSTGRES_DB: crewup_test
      POSTGRES_USER: crewup_test
      POSTGRES_PASSWORD: test_password_123
```

**Avantages** :
- ✅ Sécurisé (pas d'exposition internet)
- ✅ Gratuit
- ✅ Isolation complète entre chaque exécution
- ✅ Même schéma que production
- ✅ Pas de maintenance infrastructure

#### En Local
Utilisez votre propre base de données :
- PostgreSQL local
- PostgreSQL dans Docker
- Base de données dev/staging (avec précaution)

### Configuration de la DB pour les Tests

Chaque service peut override `DATABASE_URL` via `.env.test` :

```bash
# .env.test (exemple)
DATABASE_URL=postgresql://user:pass@localhost:5432/my_test_db
```

**Si `.env.test` n'existe pas** : Le script utilise la valeur par défaut ou celle de GitHub Actions.

## 🚀 Utilisation

### Tests Locaux

#### Option 1 : Tests Unitaires Uniquement (Recommandé)

```bash
cd event
./run_tests.sh unit
```

Avantages :
- ✅ Rapide
- ✅ Pas besoin de services externes (Keycloak, etc.)
- ✅ Fonctionne hors ligne

#### Option 2 : Tests Complets (Unitaires + Intégration)

Prérequis :
1. Service en cours d'exécution
2. `.env.test` configuré
3. Keycloak accessible (pour certains tests)

```bash
# 1. Démarrer le service
cd event
uvicorn app.main:app --port 8001

# 2. Dans un autre terminal - lancer les tests
./run_tests.sh all
```

#### Option 3 : Tests avec votre DB Docker Locale

```bash
# 1. Démarrer PostgreSQL en Docker
docker run -d \
  --name test-postgres \
  -e POSTGRES_DB=crewup_test \
  -e POSTGRES_USER=crewup_test \
  -e POSTGRES_PASSWORD=test123 \
  -p 5432:5432 \
  postgres:15

# 2. Appliquer le schéma
psql postgresql://crewup_test:test123@localhost:5432/crewup_test -f helm/crewup/config/schema.sql

# 3. Créer .env.test
cat > event/.env.test << EOF
DATABASE_URL=postgresql://crewup_test:test123@localhost:5432/crewup_test
TESTING=true
EOF

# 4. Lancer les tests unitaires
cd event
./run_tests.sh unit
```

### Chaque Service

```bash
# Event Service
cd event && ./run_tests.sh

# Group Service
cd group && ./run_tests.sh

# Safety Service
cd safety && ./run_tests.sh

# User Service
cd user && ./run_tests.sh

# Rating Service
cd rating && ./run_tests.sh
```

### Créer une Pull Request

```bash
# 1. Créer une branche
git checkout -b feature/ma-fonctionnalite

# 2. Développer et commiter
git add .
git commit -m "feat: nouvelle fonctionnalité"

# 3. Pousser
git push origin feature/ma-fonctionnalite

# 4. Créer la PR sur GitHub
# Les tests s'exécutent automatiquement !
```

Les tests sur GitHub Actions :
- ✅ Utilisent automatiquement la DB de test PostgreSQL
- ✅ Lancent UNIQUEMENT les tests unitaires (rapides)
- ✅ Ignorent les tests d'intégration (qui nécessitent Keycloak, etc.)
- ✅ Appliquent le schéma SQL complet automatiquement

### Vérifier les Tests

1. Allez sur votre Pull Request
2. Scrollez à "Checks"
3. Cliquez sur "Test Summary" pour voir les détails
4. Chaque service testé apparaît séparément

## 📋 Variables d'Environnement

### Automatique sur GitHub Actions

```env
DATABASE_URL=postgresql://crewup_test:test_password_123@localhost:5432/crewup_test
TEST_DATABASE_URL=postgresql://crewup_test:test_password_123@localhost:5432/crewup_test
TESTING=true
CI=true
```

### Configuration Locale (`.env.test`)

Créez `.env.test` pour override les valeurs par défaut :

```bash
# Copier l'exemple
cp .env.test.example .env.test

# Éditer avec vos valeurs
DATABASE_URL=postgresql://votre_user:votre_pass@localhost:5432/votre_db
```

**Important** : `.env.test` est dans `.gitignore` (ne sera jamais commité).

## 🔄 Workflow de Tests

### Détection Automatique

Les scripts `run_tests.sh` détectent automatiquement l'environnement :

```bash
# Sur GitHub Actions (CI=true)
./run_tests.sh  # → Lance unit tests uniquement

# En local sans .env.test
./run_tests.sh  # → Lance unit tests avec DB par défaut

# En local avec .env.test + service running
./run_tests.sh  # → Lance unit + integration tests

# Force unit tests only
./run_tests.sh unit

# Force integration tests
./run_tests.sh integration
```

### Schéma de Décision

```
run_tests.sh appelé
    │
    ├─ CI=true ? 
    │   └─ YES → Tests unitaires uniquement
    │
    └─ NO (local)
        │
        ├─ .env.test existe ET service running ?
        │   └─ YES → Tests complets (unit + integration)
        │
        └─ NO → Tests unitaires uniquement
```

## 📋 Configuration de Protection de Branche

Pour **exiger** que les tests passent avant le merge :

1. Allez dans **Settings** → **Branches**
2. Ajoutez une règle pour `main`
3. Cochez :
   - ✅ **Require a pull request before merging**
   - ✅ **Require status checks to pass before merging**
     - Sélectionnez : **Test Summary**
   - ✅ **Do not allow bypassing the above settings**

Voir le guide détaillé : `.github/BRANCH_PROTECTION_SETUP.md`

## 🧪 Structure des Tests

### Event Service
```
event/
├── tests/
│   ├── test_api.py                    # Tests API généraux ✅ UNIT
│   ├── test_routes_comprehensive.py   # Tests routes complètes ✅ UNIT
│   ├── test_auth.py                   # Tests authentification ✅ UNIT
│   ├── test_events_coverage.py        # Tests événements ✅ UNIT
│   ├── test_exceptions.py             # Tests erreurs ✅ UNIT
│   └── test_integration.py            # Tests intégration DB ⚠️ INTEGRATION (ignoré sur CI)
├── run_tests.sh                       # Script intelligent
└── .env.test.example                  # Template de configuration
```

### Group Service
```
group/
├── tests/
│   ├── test_api.py                    # ✅ UNIT
│   └── test_integration.py            # ⚠️ INTEGRATION (ignoré sur CI)
├── run_tests.sh
└── .env.test.example
```

### Safety Service
```
safety/
├── tests/
│   ├── test_api.py                    # ✅ UNIT
│   ├── test_alerts.py                 # ✅ UNIT
│   ├── test_edge_cases.py             # ✅ UNIT
│   └── test_integration_auth.py       # ⚠️ INTEGRATION (ignoré sur CI)
├── run_tests.sh
└── .env.test.example
```

### User Service
```
user/
├── tests/
│   └── test_users.py                  # ✅ UNIT (utilise PostgreSQL)
├── run_tests.sh
└── .env.test.example
```

### Rating Service
```
rating/
├── tests/
│   └── test_basic.py                  # ✅ UNIT (minimal)
└── run_tests.sh
```

### Légende
- ✅ **UNIT** : Tests exécutés sur GitHub Actions
- ⚠️ **INTEGRATION** : Tests ignorés sur CI (nécessitent services externes)

## 🔧 Variables d'Environnement de Test

### GitHub Actions (Automatique)

```env
DATABASE_URL=postgresql://crewup_test:test_password_123@localhost:5432/crewup_test
TEST_DATABASE_URL=postgresql://crewup_test:test_password_123@localhost:5432/crewup_test
TESTING=true
CI=true
```

### Local (`.env.test`)

Créez `.env.test` dans chaque service pour override :

```env
# Obligatoire - votre base de données locale
DATABASE_URL=postgresql://user:pass@localhost:5432/db

# Pour tests d'intégration uniquement (optionnel)
KEYCLOAK_SERVER_URL=https://keycloak.ltu-m7011e-3.se
KEYCLOAK_REALM=crewup
KEYCLOAK_CLIENT_ID=crewup-test
TEST_USER1_EMAIL=user1@example.com
TEST_USER1_PASSWORD=password123
```

**Astuce** : Utilisez `.env.test.example` comme template :
```bash
cp .env.test.example .env.test
# Puis éditez .env.test avec vos valeurs
```

## 📊 Rapports de Coverage

Les rapports de coverage HTML sont automatiquement générés et disponibles en artifacts :

1. Allez dans l'onglet **Actions**
2. Cliquez sur le workflow terminé
3. Scrollez jusqu'à **Artifacts**
4. Téléchargez `coverage-<service>`

## 🐛 Dépannage

### Les tests échouent localement mais pas sur GitHub

```bash
# 1. Vérifiez votre .env.test
cat .env.test

# 2. Testez avec la même DB que CI
docker run -d --name test-postgres \
  -e POSTGRES_DB=crewup_test \
  -e POSTGRES_USER=crewup_test \
  -e POSTGRES_PASSWORD=test_password_123 \
  -p 5432:5432 \
  postgres:15

# 3. Appliquez le schéma
psql postgresql://crewup_test:test_password_123@localhost:5432/crewup_test \
  -f helm/crewup/config/schema.sql

# 4. Mettez à jour .env.test
echo "DATABASE_URL=postgresql://crewup_test:test_password_123@localhost:5432/crewup_test" > .env.test

# 5. Relancez les tests
./run_tests.sh unit
```

### Les tests échouent sur GitHub mais pas localement

Vérifiez que vos tests n'ont pas de dépendances externes :
- ❌ Pas d'appels à Keycloak
- ❌ Pas d'appels HTTP entre services
- ❌ Pas de fichiers locaux spécifiques
- ✅ Utilisez des mocks pour l'authentification
- ✅ Utilisez la DB fournie par GitHub Actions

### Service ne trouve pas la DB

```bash
# Vérifiez que DATABASE_URL est bien défini
cd event
python -c "import os; print(os.getenv('DATABASE_URL'))"

# Testez la connexion
psql "$DATABASE_URL" -c "SELECT 1"
```

### Tests d'intégration ignorés sur CI

C'est **normal** ! Les tests d'intégration nécessitent :
- Services externes (Keycloak, autres microservices)
- Configuration complexe
- Temps d'exécution long

Sur CI, seuls les tests **unitaires** sont exécutés :
- Rapides
- Isolés
- Sans dépendances externes

### Forcer les tests unitaires en local

```bash
# Si vous voulez simuler l'environnement CI
CI=true ./run_tests.sh

# Ou explicitement
./run_tests.sh unit
```

### Voir exactement quels tests sont exécutés

```bash
# Mode verbose avec liste des tests
pytest tests/ -v --collect-only

# Voir quels tests seraient ignorés
pytest tests/ -v --collect-only --ignore=tests/test_integration.py
```

## 🎯 Bonnes Pratiques

### Avant de Commiter

```bash
# Lancez les tests localement
./run_tests.sh

# Vérifiez le coverage
open htmlcov/index.html
```

### Écrire de Nouveaux Tests

```python
# tests/test_mon_feature.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_mon_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/mon-endpoint")
        assert response.status_code == 200
```

### Tests avec DB

```python
@pytest.fixture
async def db_session():
    """Fixture pour avoir une session DB"""
    from app.database import get_db
    db = next(get_db())
    yield db
    db.close()

async def test_create_user(db_session):
    # Votre test avec DB
    pass
```

## 📚 Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [PostgreSQL Service Containers](https://docs.github.com/en/actions/using-containerized-services/creating-postgresql-service-containers)
- [Pytest Documentation](https://docs.pytest.org/)
- [Branch Protection Rules](.github/BRANCH_PROTECTION_SETUP.md)

## ❓ Questions Fréquentes

### Pourquoi ne pas utiliser une DB accessible depuis internet ?

**Sécurité** : Exposer une base de données sur internet, même avec mot de passe, est un risque. Les service containers sont plus sûrs, gratuits et plus simples.

### Peut-on tester localement avec Docker ?

Oui ! Voir la section "Tests avec votre DB Docker Locale" ci-dessus.

### Comment ajouter un nouveau service ?

1. Créez `<service>/run_tests.sh` basé sur les templates existants
2. Ajoutez `<service>/.env.test.example`
3. Ajoutez le service dans `.github/workflows/test.yaml` (matrix.service)
4. Écrivez vos tests dans `<service>/tests/`

### Les tests sont-ils obligatoires ?

Après activation de la protection de branche, **oui**. Impossible de merger sans tests verts.

### Comment override la DATABASE_URL ?

Trois méthodes :

```bash
# Méthode 1: .env.test (recommandé)
echo "DATABASE_URL=postgresql://..." > .env.test
./run_tests.sh

# Méthode 2: Variable d'environnement
DATABASE_URL=postgresql://... ./run_tests.sh

# Méthode 3: Export global
export DATABASE_URL=postgresql://...
./run_tests.sh
```

### Pourquoi certains tests sont ignorés sur CI ?

Les tests d'intégration (`test_integration.py`, `test_integration_auth.py`) nécessitent :
- Keycloak en cours d'exécution
- Communication entre microservices
- Configuration complexe

Ces tests sont **parfaits pour le développement local** mais **trop complexes pour CI/CD**.

Sur GitHub Actions, nous exécutons uniquement les **tests unitaires** :
- ✅ Rapides (< 2min par service)
- ✅ Fiables (pas de dépendances externes)
- ✅ Faciles à déboguer

### Comment lancer TOUS les tests localement ?

```bash
# 1. Démarrez tous les services requis
docker-compose up -d

# 2. Configurez .env.test avec les vraies credentials
cp .env.test.example .env.test
# Éditez .env.test

# 3. Lancez les tests complets
./run_tests.sh all
```

### Les tests utilisent-ils ma vraie DB ?

**Dépend** :
- **GitHub Actions** : NON, utilise une DB temporaire dédiée
- **Local** : Utilise ce que vous configurez dans `.env.test`

**Recommandation** : Utilisez toujours une DB de test séparée localement :
```bash
DATABASE_URL=postgresql://user:pass@localhost:5432/crewup_TEST
```

### Combien de temps prennent les tests sur GitHub Actions ?

Environ **2-5 minutes** par service :
- 30s pour setup PostgreSQL
- 30s pour appliquer schéma + migrations
- 1-3min pour exécuter les tests
- Tests en **parallèle** → 5-7min total pour tous les services

## 🎓 Pour Aller Plus Loin

### Tests E2E (End-to-End)

Considérez d'ajouter des tests E2E avec :
- Playwright
- Cypress
- Selenium

### Tests de Performance

Ajoutez des tests de charge avec :
- Locust
- k6
- Apache JMeter

### Monitoring des Tests

Intégrez avec :
- Codecov
- SonarQube
- Coveralls
