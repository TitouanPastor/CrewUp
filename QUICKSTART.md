# 🚀 QUICKSTART - Lancer l'app en 2 minutes

## TL;DR

```bash
./setup.sh
docker-compose up
```

Puis ouvre **http://localhost:3000** 🎉

---

## Étape par étape

### 1. Build tout

```bash
./setup.sh
```

Ça va build tous les containers Docker (frontend React + 5 microservices + PostgreSQL).

**Temps**: ~5-10 min la première fois, ensuite c'est rapide.

### 2. Lance l'app

```bash
docker-compose up
```

Tu vas voir plein de logs. C'est normal !

**Attends que tu voies** :
```
crewup-frontend | ... ready in XXX ms
crewup-db | database system is ready to accept connections
```

### 3. Ouvre l'app

**http://localhost:3000**

Tu devrais voir :
- 🗺️ Une map avec des pins
- 📝 Une liste d'events à gauche
- 🎨 Un design moderne

### 4. Teste l'app

1. **Login** : Clique n'importe où → tu seras redirigé vers `/login`
2. **Clique "Sign up"** pour créer un compte (c'est mocké, pas de vraie DB encore)
3. **Explore la map** : Clique sur les markers ou les cards
4. **Rejoins un groupe** : Clique sur un event → "View Details" → "Join Group"
5. **Chat** : Envoie des messages dans le group chat
6. **Party Mode** : Active le bouton rouge dans la navbar → t'auras un bouton HELP dans le chat

---

## 🛑 Stopper l'app

```bash
# Ctrl+C dans le terminal
# Puis :
docker-compose down
```

Pour **tout reset** (DB incluse) :
```bash
docker-compose down -v
```

---

## 📦 Ce qui tourne

| Service    | Port  | URL                       |
|-----------|-------|---------------------------|
| Frontend  | 3000  | http://localhost:3000     |
| User API  | 8005  | http://localhost:8005     |
| Event API | 8001  | http://localhost:8001     |
| Group API | 8002  | http://localhost:8002     |
| Rating API| 8003  | http://localhost:8003     |
| Safety API| 8004  | http://localhost:8004     |
| Postgres  | 5432  | localhost:5432            |

---

## 🐛 Problèmes ?

### Le frontend ne charge pas
```bash
docker logs crewup-frontend
```

### Un service ne démarre pas
```bash
docker-compose logs user
docker-compose logs postgres
```

### Port déjà utilisé
Édite `docker-compose.yaml` et change le port :
```yaml
ports:
  - "3001:80"  # Au lieu de 3000:80
```

### Reset complet
```bash
docker-compose down -v
docker system prune -a
./setup.sh
docker-compose up
```

---

## 🎯 Fonctionnalités à tester

✅ **Map interactive** - Clique sur les markers  
✅ **Events list** - Vois tous les events de ce soir  
✅ **Event details** - Infos complètes sur un event  
✅ **Create group** - Forme ton crew pour l'event  
✅ **Join group** - Rejoins un groupe existant  
✅ **Real-time chat** - Discute avec ton crew  
✅ **Party Mode** - Bouton d'alerte sécurité  
✅ **User profile** - Ton profil + réputation  
✅ **Dark mode** - Interface sombre  

---

## 📝 Notes

- **Données mockées** : Pour l'instant tout est en mock (pas de vraie DB connectée)
- **Pas d'auth réelle** : Login/Register sont mockés
- **Pas de WebSocket** : Le chat est simulé (pas de temps réel pour l'instant)
- **To fix** : Faut connecter les APIs et implémenter les endpoints

---

**Enjoy! 🎉**

Des questions ? Check le `README.md` principal ou le `frontend/README.md` pour plus de détails.
