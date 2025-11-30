# 🚀 Commandes pour Push sur Main

## ✅ Pré-Push Checklist

Avant de pusher, vérifie que tout est OK :

```bash
# 1. Vérifier que les scripts sont exécutables
ls -la */run_tests.sh

# 2. Tester localement (au moins un service)
cd event && ./run_tests.sh unit && cd ..

# 3. Vérifier les fichiers créés
git status
```

## 📦 Fichiers à Commiter

### Scripts de tests (5 services)
- ✅ `event/run_tests.sh`
- ✅ `group/run_tests.sh`
- ✅ `safety/run_tests.sh`
- ✅ `user/run_tests.sh`
- ✅ `rating/run_tests.sh`

### Templates de configuration (5 services)
- ✅ `event/.env.test.example`
- ✅ `group/.env.test.example`
- ✅ `safety/.env.test.example`
- ✅ `user/.env.test.example`
- ✅ `rating/.env.test.example`

### Workflow GitHub Actions
- ✅ `.github/workflows/test.yaml`

### Documentation
- ✅ `TESTING.md` (guide complet)
- ✅ `TESTING_QUICKSTART.md` (guide rapide)
- ✅ `TESTS_SETUP_SUMMARY.md` (résumé setup)
- ✅ `.github/BRANCH_PROTECTION_SETUP.md` (protection branche)

## 🔥 Commandes Git

### Option 1 : Commit Direct sur Main (si autorisé)

```bash
# 1. Vérifier les changements
git status

# 2. Ajouter tous les fichiers
git add .github/workflows/test.yaml \
  event/run_tests.sh event/.env.test.example \
  group/run_tests.sh group/.env.test.example \
  safety/run_tests.sh safety/.env.test.example \
  user/run_tests.sh user/.env.test.example \
  rating/run_tests.sh rating/.env.test.example \
  TESTING.md \
  TESTING_QUICKSTART.md \
  TESTS_SETUP_SUMMARY.md \
  .github/BRANCH_PROTECTION_SETUP.md

# 3. Commit
git commit -m "feat: setup automated testing with GitHub Actions

- Add GitHub Actions workflow with PostgreSQL service container
- Create intelligent run_tests.sh scripts for all services
- Add .env.test.example templates for local testing
- Support DATABASE_URL override for local/CI environments
- Add comprehensive testing documentation
- Tests auto-detect CI vs local environment
- Unit tests on CI, full tests optional locally"

# 4. Push
git push origin main
```

### Option 2 : Via Pull Request (Recommandé)

```bash
# 1. Créer une branche
git checkout -b feat/automated-testing

# 2. Ajouter tous les fichiers
git add .github/workflows/test.yaml \
  */run_tests.sh \
  */.env.test.example \
  TESTING*.md \
  TESTS_SETUP_SUMMARY.md \
  .github/BRANCH_PROTECTION_SETUP.md

# 3. Commit
git commit -m "feat: setup automated testing with GitHub Actions

Setup complet des tests automatisés :

## GitHub Actions
- PostgreSQL 15 service container
- Application auto du schéma SQL + migrations
- Tests parallèles pour tous les services
- Variables d'env configurées automatiquement

## Scripts run_tests.sh (tous les services)
- Détection auto CI vs local
- Override DATABASE_URL via .env.test
- Fallback intelligent sur tests unitaires
- Support tests unitaires + intégration

## Configuration
- Templates .env.test.example pour chaque service
- Documentation complète (TESTING.md)
- Guide rapide (TESTING_QUICKSTART.md)
- Guide protection branche

## Services Supportés
- Event Service ✅
- Group Service ✅
- Safety Service ✅
- User Service ✅
- Rating Service ✅

Fixes #XX (si vous avez une issue)"

# 4. Push de la branche
git push origin feat/automated-testing

# 5. Créer la PR sur GitHub
# → Les tests vont s'exécuter automatiquement !
# → Vérifier que tout est vert
# → Merger la PR
```

## 🧪 Tester Avant de Push

```bash
# Test rapide - un service
cd event && ./run_tests.sh unit && cd ..

# Test complet - tous les services (optionnel)
for service in event group safety user rating; do
  echo "Testing $service..."
  (cd $service && ./run_tests.sh unit)
done
```

## ⚠️ Points d'Attention

### 1. Permissions des Scripts

Les scripts doivent être exécutables :
```bash
chmod +x */run_tests.sh
git add */run_tests.sh
```

### 2. Pas de Secrets

Vérifiez que vous ne commitez pas de `.env.test` :
```bash
git status | grep ".env.test"
# Ne devrait rien afficher (sauf .env.test.example)
```

### 3. Workflow Valide

Vérifiez la syntaxe YAML :
```bash
# Sur GitHub, les erreurs de syntaxe apparaîtront immédiatement
# Vous pouvez aussi valider localement avec yamllint
```

## 🎯 Après le Push

### 1. Vérifier GitHub Actions

```
GitHub → Actions → Attendre le premier run
```

### 2. Créer une PR de Test

```bash
git checkout -b test/validate-ci
echo "# Test" >> README.md
git add README.md
git commit -m "test: validate CI setup"
git push origin test/validate-ci
```

Puis créer la PR et vérifier que les tests s'exécutent.

### 3. Activer Branch Protection

Suivre le guide : `.github/BRANCH_PROTECTION_SETUP.md`

## 📊 Statut Actuel

Branche actuelle :
```bash
git branch --show-current
```

Fichiers modifiés :
```bash
git status --short
```

Derniers commits :
```bash
git log --oneline -5
```

## ✅ Validation Finale

Avant de pusher, exécutez :

```bash
# 1. Vérifier les scripts
for script in event/run_tests.sh group/run_tests.sh safety/run_tests.sh user/run_tests.sh rating/run_tests.sh; do
  if [ -x "$script" ]; then
    echo "✓ $script est exécutable"
  else
    echo "✗ $script n'est PAS exécutable"
    chmod +x "$script"
  fi
done

# 2. Vérifier les templates
for example in event/.env.test.example group/.env.test.example safety/.env.test.example user/.env.test.example rating/.env.test.example; do
  if [ -f "$example" ]; then
    echo "✓ $example existe"
  else
    echo "✗ $example MANQUANT"
  fi
done

# 3. Vérifier la doc
for doc in TESTING.md TESTING_QUICKSTART.md TESTS_SETUP_SUMMARY.md .github/BRANCH_PROTECTION_SETUP.md; do
  if [ -f "$doc" ]; then
    echo "✓ $doc existe"
  else
    echo "✗ $doc MANQUANT"
  fi
done

# 4. Vérifier le workflow
if [ -f ".github/workflows/test.yaml" ]; then
  echo "✓ Workflow GitHub Actions existe"
else
  echo "✗ Workflow MANQUANT"
fi
```

Si tout est ✓, vous êtes prêt à pusher !

## 🚀 Push Now!

```bash
# Méthode rapide (si vous êtes sûr)
git add .
git commit -m "feat: automated testing setup complete"
git push origin main

# OU via PR (recommandé)
git checkout -b feat/automated-testing
git add .
git commit -m "feat: automated testing setup complete"
git push origin feat/automated-testing
# Puis créer la PR sur GitHub
```

## 🎉 Success!

Après le push, vérifiez :
1. ✅ GitHub Actions s'est déclenché
2. ✅ Tests sont verts
3. ✅ Documentation accessible
4. ✅ Scripts fonctionnent en local

---

**Prêt ? Let's go! 🚀**
