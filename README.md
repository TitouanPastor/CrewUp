# 🚀 CrewUp - Local Development Guide

CrewUp est une application pour trouver des groupes pour sortir en soirée. Cette version minimale te permet de tester l'infrastructure de base.

## 📋 Prérequis

- Docker et Docker Compose installés
- WSL2 (si tu es sur Windows)
- 4GB+ de RAM disponible

## 🏗️ Architecture

L'app est composée de :
- **5 microservices FastAPI** : user, event, group, rating, safety
- **1 frontend React** : SPA moderne avec TypeScript, Vite, TailwindCSS, Leaflet
- **PostgreSQL** : base de données avec schema complet

### Ports exposés

| Service    | Port Local | URL                        |
|------------|------------|----------------------------|
| Frontend   | 3000       | http://localhost:3000      |
| Event      | 8001       | http://localhost:8001      |
| Group      | 8002       | http://localhost:8002      |
| Rating     | 8003       | http://localhost:8003      |
| Safety     | 8004       | http://localhost:8004      |
| User       | 8005       | http://localhost:8005      |
| PostgreSQL | 5432       | localhost:5432             |

## 🚀 Démarrage rapide

### Option A: Script automatique (recommandé)

```bash
./setup.sh
docker-compose up
```

### Option B: Manuel

#### 1️⃣ Build tous les containers

```bash
chmod +x build-all.sh
./build-all.sh
```

Ou manuellement :
```bash
docker-compose build
```

#### 2️⃣ Lancer tous les services

```bash
docker-compose up
```

Pour lancer en arrière-plan :
```bash
docker-compose up -d
```

### 3️⃣ Ouvrir l'app

Ouvre ton navigateur sur **http://localhost:3000**

Tu devrais voir :
- 🗺️ Une carte interactive avec les événements
- 📝 Une liste d'événements sur la gauche
- 🎨 Une interface moderne dark/light mode

### 4️⃣ Tester le backend

```bash
# User service
curl http://localhost:8005

# Event service
curl http://localhost:8001

# Health checks
curl http://localhost:8005/health
curl http://localhost:8001/health
```

## 🗄️ Base de données

La DB PostgreSQL se lance automatiquement et exécute `database/schema.sql` au démarrage.

### Se connecter à la DB

```bash
# Depuis WSL/Linux
docker exec -it crewup-db psql -U crewup -d crewup

# Ou avec un client comme DBeaver
Host: localhost
Port: 5432
Database: crewup
User: crewup
Password: crewup_dev_password
```

### Commandes SQL utiles

```sql
-- Lister les tables
\dt

-- Voir le schema d'une table
\d users

-- Quelques requêtes de test
SELECT * FROM users;
SELECT * FROM events;
```

## 🛠️ Commandes utiles

### Voir les logs

```bash
# Tous les services
docker-compose logs -f

# Un service spécifique
docker-compose logs -f user
docker-compose logs -f postgres
```

### Redémarrer un service

```bash
docker-compose restart user
```

### Stopper tout

```bash
docker-compose down
```

### Stopper ET supprimer les volumes (reset complet de la DB)

```bash
docker-compose down -v
```

### Rebuild un seul service

```bash
docker-compose build user
docker-compose up -d user
```

## 🔧 Debugging

### Problème : Les containers ne démarrent pas

```bash
# Vérifier les logs
docker-compose logs

# Vérifier l'état des containers
docker ps -a
```

### Problème : Port déjà utilisé

Si un port est déjà pris sur Windows/WSL, édite `docker-compose.yaml` et change le port local :
```yaml
ports:
  - "9001:8000"  # Au lieu de 8001:8000
```

### Problème : La DB ne se connecte pas

```bash
# Vérifier que postgres est healthy
docker-compose ps

# Regarder les logs postgres
docker-compose logs postgres
```

### Problème : Permissions sur WSL

```bash
# Si build-all.sh ne se lance pas
chmod +x build-all.sh deploy.sh cleanup.sh upgrade.sh
```

## 📝 Tester l'API avec curl

### Créer un utilisateur (quand les endpoints seront implémentés)

```bash
curl -X POST http://localhost:8005/users \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123","first_name":"John","last_name":"Doe"}'
```

### Lister les événements

```bash
curl http://localhost:8001/events
```

## 🎯 Prochaines étapes

1. **Implémenter les endpoints CRUD** dans chaque service
2. **Connecter les services à PostgreSQL** (ajouter psycopg2/sqlalchemy)
3. **Connecter le frontend aux APIs** (remplacer les mock data)
4. **Implémenter WebSocket** pour le chat temps réel
5. **Ajouter RabbitMQ** pour la communication inter-services
6. **Ajouter Keycloak** pour l'authentification
7. **Ajouter des tests**

## 🐛 Problèmes connus

- [ ] Les services backend ne sont pas encore connectés à PostgreSQL
- [ ] Le frontend utilise des données mockées (pas d'API réelle)
- [ ] Pas d'authentification réelle (Keycloak à implémenter)
- [ ] Pas de WebSocket réel pour le chat
- [ ] Pas de message broker (RabbitMQ à ajouter)

## 📚 Ressources

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Docker Compose Docs](https://docs.docker.com/compose/)
- [PostgreSQL Docs](https://www.postgresql.org/docs/)

---

**Enjoy coding! 🎉**
