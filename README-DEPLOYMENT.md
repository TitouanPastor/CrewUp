# 🚀 CrewUp - Multi-Environment Deployment Guide

## 📋 Table des Matières

- [Architecture](#architecture)
- [Setup Initial ArgoCD](#setup-initial-argocd)
- [Workflow de Développement](#workflow-de-développement)
- [Promotion des Environnements](#promotion-des-environnements)
- [Monitoring & Troubleshooting](#monitoring--troubleshooting)

---

## 🏗️ Architecture

### Vue d'ensemble

```
┌─────────────┐
│   GitHub    │
│   Main      │
└──────┬──────┘
       │
       │ Push → CI/CD
       │
       ▼
┌─────────────────────────────────────┐
│  Build & Push Images (GHCR)         │
│  Update environments/dev/values.yaml │
└──────┬──────────────────────────────┘
       │
       │ ArgoCD Auto-Sync
       │
       ▼
┌──────────────┐      Manual Promotion      ┌─────────────┐      Manual Promotion      ┌──────────────┐
│     DEV      │ ─────────────────────────► │   STAGING   │ ─────────────────────────► │  PRODUCTION  │
│ crewup-dev   │                            │ crewup-     │                            │ crewup       │
│   .ltu...    │                            │ staging.ltu │                            │   .ltu...    │
└──────────────┘                            └─────────────┘                            └──────────────┘
```

### Environnements

| Environnement | Namespace | Domain | Replicas | Cert Issuer | Auto-Deploy |
|---------------|-----------|--------|----------|-------------|-------------|
| **Dev** | `crewup-dev` | `crewup-dev.ltu-m7011e-3.se` | 1 | letsencrypt-staging | ✅ Yes |
| **Staging** | `crewup-staging` | `crewup-staging.ltu-m7011e-3.se` | 2 | letsencrypt-prod | ❌ Manual |
| **Production** | `crewup-production` | `crewup.ltu-m7011e-3.se` | 3 | letsencrypt-prod | ❌ Manual |

---

## 🎯 Setup Initial ArgoCD

### Prérequis

1. **ArgoCD installé et accessible**
2. **kubectl configuré** pour ton cluster
3. **Accès admin ArgoCD**

### 1. Créer les Namespaces Kubernetes

```bash
# Créer les 3 namespaces
kubectl create namespace crewup-dev
kubectl create namespace crewup-staging
kubectl create namespace crewup-production

# Vérifier
kubectl get namespaces | grep crewup
```

### 2. Login ArgoCD

**Via CLI :**
```bash
# Installer ArgoCD CLI si pas déjà fait
brew install argocd  # macOS
# ou
curl -sSL -o argocd https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
chmod +x argocd
sudo mv argocd /usr/local/bin/

# Login
argocd login <ARGOCD_SERVER> --username admin --password <PASSWORD>
# Example: argocd login argocd.ltu-m7011e-3.se
```

**Via UI :**
Ouvre `https://<ARGOCD_SERVER>` dans ton navigateur.

### 3. Créer les Applications ArgoCD

#### Option A : Via CLI (Recommandé)

```bash
# ========================================
# Application DEV
# ========================================
argocd app create crewup-dev \
  --repo https://github.com/TitouanPastor/CrewUp.git \
  --path helm/crewup \
  --dest-namespace crewup-dev \
  --dest-server https://kubernetes.default.svc \
  --helm-set-file values=../../environments/dev/values.yaml \
  --sync-policy automated \
  --auto-prune \
  --self-heal

# ========================================
# Application STAGING
# ========================================
argocd app create crewup-staging \
  --repo https://github.com/TitouanPastor/CrewUp.git \
  --path helm/crewup \
  --dest-namespace crewup-staging \
  --dest-server https://kubernetes.default.svc \
  --helm-set-file values=../../environments/staging/values.yaml \
  --sync-policy automated \
  --auto-prune \
  --self-heal

# ========================================
# Application PRODUCTION
# ========================================
argocd app create crewup-production \
  --repo https://github.com/TitouanPastor/CrewUp.git \
  --path helm/crewup \
  --dest-namespace crewup-production \
  --dest-server https://kubernetes.default.svc \
  --helm-set-file values=../../environments/production/values.yaml \
  --sync-policy automated \
  --auto-prune \
  --self-heal

# Vérifier les applications
argocd app list
```

#### Option B : Via UI ArgoCD

Pour chaque environnement (dev, staging, production) :

1. **New App** → `+ NEW APP`
2. **Application Name** : `crewup-{env}`
3. **Project** : `default`
4. **Sync Policy** : `Automatic`
   - ✅ Prune Resources
   - ✅ Self Heal
5. **Repository URL** : `https://github.com/TitouanPastor/CrewUp.git`
6. **Revision** : `main`
7. **Path** : `helm/crewup`
8. **Helm** → **VALUES FILES** : `../../environments/{env}/values.yaml`
9. **Cluster URL** : `https://kubernetes.default.svc`
10. **Namespace** : `crewup-{env}`
11. **CREATE**

### 4. Vérifier le Déploiement

```bash
# Vérifier le statut des apps
argocd app get crewup-dev
argocd app get crewup-staging
argocd app get crewup-production

# Vérifier les pods dans chaque namespace
kubectl get pods -n crewup-dev
kubectl get pods -n crewup-staging
kubectl get pods -n crewup-production

# Vérifier les ingress (domaines)
kubectl get ingress -n crewup-dev
kubectl get ingress -n crewup-staging
kubectl get ingress -n crewup-production
```

---

## 💻 Workflow de Développement

### 1. Développer une Feature

```bash
# Créer une branche
git checkout -b feature/ma-nouvelle-feature

# Développer...
# Éditer frontend/, event/, group/, etc.

# Commit
git add .
git commit -m "feat: ajout de ma nouvelle feature"
git push origin feature/ma-nouvelle-feature
```

### 2. Ouvrir une Pull Request

- Ouvre une PR sur GitHub : `feature/ma-nouvelle-feature` → `main`
- **GitHub Actions** lance les **tests uniquement** (pas de build)
- Review du code par l'équipe

### 3. Merge de la PR

```bash
# Merge la PR (via GitHub UI ou CLI)
gh pr merge <PR_NUMBER> --squash
```

**Ce qui se passe automatiquement :**

1. ✅ **GitHub Actions CI/CD** :
   - Build les images Docker des services modifiés
   - Push vers `ghcr.io/titouanpastor/crewup-*:<commit-sha>`
   - Met à jour `environments/dev/values.yaml` avec les nouveaux tags
   - Commit avec message : `chore(dev): update image tags to <sha> [services] [skip ci]`

2. ✅ **ArgoCD** détecte le changement dans `environments/dev/values.yaml` :
   - Sync automatique vers le namespace `crewup-dev`
   - Déploiement des nouveaux pods

3. ✅ **Test sur DEV** : `https://crewup-dev.ltu-m7011e-3.se`

### 4. Vérifier le Déploiement DEV

```bash
# Via ArgoCD CLI
argocd app get crewup-dev
argocd app sync crewup-dev  # Force sync si besoin

# Via kubectl
kubectl get pods -n crewup-dev -w
kubectl logs -n crewup-dev -l app=frontend --tail=50
kubectl logs -n crewup-dev -l app=group --tail=50

# Tester l'application
curl https://crewup-dev.ltu-m7011e-3.se/health
```

---

## 🚀 Promotion des Environnements

### DEV → STAGING

**Quand :** Après validation complète en DEV

```bash
# Option 1: Via GitHub UI
# 1. Aller sur https://github.com/TitouanPastor/CrewUp/actions
# 2. Cliquer sur "Promote to Environment"
# 3. Cliquer "Run workflow"
# 4. Sélectionner:
#    - source_env: dev
#    - target_env: staging
# 5. Cliquer "Run workflow"
```

**Ce qui se passe :**

1. ✅ GitHub Actions :
   - Lit les tags image depuis `environments/dev/values.yaml`
   - Copie ces tags dans `environments/staging/values.yaml`
   - Commit : `chore(staging): promote from dev [skip ci]`

2. ✅ ArgoCD sync automatique vers `crewup-staging`

3. ✅ **Tester sur STAGING** : `https://crewup-staging.ltu-m7011e-3.se`

```bash
# Vérifier le déploiement staging
argocd app get crewup-staging
kubectl get pods -n crewup-staging
```

### STAGING → PRODUCTION

**Quand :** Après validation complète en STAGING

```bash
# Via GitHub UI
# 1. Aller sur https://github.com/TitouanPastor/CrewUp/actions
# 2. Cliquer sur "Promote to Environment"
# 3. Cliquer "Run workflow"
# 4. Sélectionner:
#    - source_env: staging
#    - target_env: production
# 5. Cliquer "Run workflow"
```

**Ce qui se passe :**

1. ✅ GitHub Actions :
   - Lit les tags depuis `environments/staging/values.yaml`
   - Copie dans `environments/production/values.yaml`
   - Commit : `chore(production): promote from staging [skip ci]`

2. ✅ ArgoCD sync vers `crewup-production`

3. ✅ **LIVE en PRODUCTION** : `https://crewup.ltu-m7011e-3.se` 🎉

```bash
# Vérifier le déploiement production
argocd app get crewup-production
kubectl get pods -n crewup-production
```

---

## 🔍 Monitoring & Troubleshooting

### Vérifier le Statut d'une App ArgoCD

```bash
# Statut général
argocd app get crewup-{env}

# Détails de sync
argocd app history crewup-{env}

# Logs de sync
argocd app logs crewup-{env} --tail 100

# Forcer un sync
argocd app sync crewup-{env}

# Rollback si besoin
argocd app rollback crewup-{env} <REVISION_ID>
```

### Vérifier les Pods Kubernetes

```bash
# Lister les pods
kubectl get pods -n crewup-{env}

# Décrire un pod
kubectl describe pod <POD_NAME> -n crewup-{env}

# Logs d'un pod
kubectl logs <POD_NAME> -n crewup-{env} --tail=100 -f

# Logs d'un service (tous les pods)
kubectl logs -n crewup-{env} -l app=group --tail=50

# Exec dans un pod
kubectl exec -it <POD_NAME> -n crewup-{env} -- /bin/bash
```

### Problèmes Courants

#### 1. ArgoCD ne détecte pas les changements

```bash
# Forcer un refresh
argocd app get crewup-dev --refresh

# Vérifier la config Git
argocd app set crewup-dev --revision main
```

#### 2. Pods en CrashLoopBackOff

```bash
# Vérifier les logs
kubectl logs <POD_NAME> -n crewup-{env} --previous

# Vérifier les events
kubectl get events -n crewup-{env} --sort-by='.lastTimestamp'

# Vérifier la config
kubectl describe pod <POD_NAME> -n crewup-{env}
```

#### 3. Images ne se mettent pas à jour

```bash
# Vérifier le tag dans values.yaml
cat environments/{env}/values.yaml | grep imageTag

# Forcer le pull de l'image
kubectl delete pod <POD_NAME> -n crewup-{env}
```

#### 4. Problème de certificat SSL

```bash
# Vérifier les certificats
kubectl get certificate -n crewup-{env}
kubectl describe certificate -n crewup-{env}

# Vérifier cert-manager
kubectl get pods -n cert-manager
```

### Rollback d'un Déploiement

**Via ArgoCD :**
```bash
# Lister l'historique
argocd app history crewup-{env}

# Rollback vers une révision
argocd app rollback crewup-{env} <REVISION_NUMBER>
```

**Via Git (recommandé pour prod) :**
```bash
# Revenir à un commit précédent dans environments/production/values.yaml
git log environments/production/values.yaml
git checkout <COMMIT_SHA> -- environments/production/values.yaml
git commit -m "chore(production): rollback to <COMMIT_SHA>"
git push origin main
# ArgoCD sync automatique
```

---

## 📊 Résumé des Commandes Essentielles

### ArgoCD

```bash
# Login
argocd login <SERVER>

# Créer une app
argocd app create <NAME> --repo <REPO> --path <PATH> --dest-namespace <NS>

# Lister les apps
argocd app list

# Sync une app
argocd app sync <NAME>

# Statut d'une app
argocd app get <NAME>

# Rollback
argocd app rollback <NAME> <REVISION>
```

### Kubernetes

```bash
# Namespaces
kubectl create namespace <NAME>
kubectl get namespaces

# Pods
kubectl get pods -n <NAMESPACE>
kubectl logs <POD> -n <NAMESPACE>
kubectl describe pod <POD> -n <NAMESPACE>

# Services & Ingress
kubectl get svc -n <NAMESPACE>
kubectl get ingress -n <NAMESPACE>
```

### GitHub Workflows

- **CI/CD automatique** : Push sur `main` → Build & Deploy DEV
- **Promotion manuelle** : Actions → "Promote to Environment"

---

## 🎉 Bon Déploiement !

Pour toute question, contacte l'équipe DevOps ou consulte la documentation officielle :
- [ArgoCD Docs](https://argo-cd.readthedocs.io/)
- [Kubernetes Docs](https://kubernetes.io/docs/)
- [Helm Docs](https://helm.sh/docs/)
