# Tests Automatisés - Guide Rapide

## 🚀 Quick Start

### Lancer les tests localement

```bash
cd event  # ou group, safety, user, rating
./run_tests.sh
```

C'est tout ! Le script détecte automatiquement votre environnement.

## 💡 Configuration (Optionnelle)

### Override la DATABASE_URL

```bash
# Créer .env.test dans le service
cp .env.test.example .env.test

# Éditer avec votre DB
DATABASE_URL=postgresql://user:pass@localhost:5432/my_test_db
```

## 📊 Sur GitHub Actions

Automatique ! Chaque PR exécute les tests :
- ✅ PostgreSQL 15 service container
- ✅ Schéma SQL appliqué automatiquement
- ✅ Tests unitaires parallèles
- ✅ Merge bloqué si tests échouent

## 🎯 Environnements

| Environnement | DATABASE_URL | Tests exécutés |
|---------------|--------------|----------------|
| **GitHub Actions** | `postgresql://crewup_test:test_password_123@localhost:5432/crewup_test` | Unitaires uniquement |
| **Local (sans .env.test)** | Valeur par défaut | Unitaires uniquement |
| **Local (avec .env.test)** | Votre valeur | Unitaires (+ intégration si service running) |

## 📚 Documentation Complète

Voir [TESTING.md](./TESTING.md) pour :
- Configuration détaillée
- Tests d'intégration
- Dépannage
- FAQ

## 🔧 Commandes Utiles

```bash
# Tests unitaires uniquement (rapide)
./run_tests.sh unit

# Tests d'intégration (nécessite service running)
./run_tests.sh integration

# Tous les tests (auto-détection)
./run_tests.sh all

# Simuler environnement CI
CI=true ./run_tests.sh
```

## 🎓 Exemples

### Tester avec DB Docker locale

```bash
# 1. Démarrer PostgreSQL
docker run -d --name test-db \
  -e POSTGRES_DB=crewup_test \
  -e POSTGRES_USER=test \
  -e POSTGRES_PASSWORD=test \
  -p 5432:5432 \
  postgres:15

# 2. Appliquer schéma
psql postgresql://test:test@localhost:5432/crewup_test \
  -f helm/crewup/config/schema.sql

# 3. Configurer
echo "DATABASE_URL=postgresql://test:test@localhost:5432/crewup_test" > event/.env.test

# 4. Tester
cd event && ./run_tests.sh
```

### Tester tous les services

```bash
# Rapide - tests unitaires
for service in event group safety user rating; do
  echo "Testing $service..."
  cd $service && ./run_tests.sh unit && cd ..
done
```

## ✅ Checklist Avant de Merger

- [ ] `./run_tests.sh` passe localement
- [ ] PR créée sur GitHub
- [ ] Checks "Test Summary" vert sur GitHub
- [ ] Code review approuvé
- [ ] Branch à jour avec main

## 🆘 Problème ?

```bash
# Voir les tests disponibles
cd event
pytest tests/ -v --collect-only

# Mode debug
pytest tests/test_api.py -v -s

# Voir coverage détaillée
pytest tests/ --cov=app --cov-report=html
open htmlcov/index.html
```

## 📞 Support

- Documentation : [TESTING.md](./TESTING.md)
- Branch Protection : [.github/BRANCH_PROTECTION_SETUP.md](.github/BRANCH_PROTECTION_SETUP.md)
- Issues : GitHub Issues
