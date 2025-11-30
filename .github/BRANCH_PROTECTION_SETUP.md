# Configuration de la Protection de Branche

Ce document explique comment configurer GitHub pour exiger que tous les tests passent avant de pouvoir merger une Pull Request.

## Étapes de Configuration

### 1. Accéder aux Paramètres du Repository

1. Allez sur votre repository GitHub : `https://github.com/TitouanPastor/CrewUp`
2. Cliquez sur **Settings** (en haut à droite)
3. Dans le menu de gauche, cliquez sur **Branches**

### 2. Ajouter une Règle de Protection

1. Cliquez sur **Add branch protection rule** (ou **Add rule**)
2. Dans **Branch name pattern**, entrez : `main`

### 3. Configurer les Règles Requises

Cochez les options suivantes :

#### ✅ Require a pull request before merging
- Exige une PR pour tout merge vers main
- Optionnel : Cochez **Require approvals** (1 approbation recommandée)

#### ✅ Require status checks to pass before merging
- **Cochez cette option** (critique pour les tests automatiques)
- Cherchez et sélectionnez : **Test Summary**
- Optionnel : Cochez **Require branches to be up to date before merging**

#### ✅ Do not allow bypassing the above settings
- Empêche même les admins de bypass les règles
- Recommandé pour la rigueur du projet

### 4. Autres Options Recommandées

- ☑️ **Require conversation resolution before merging** : Force la résolution de tous les commentaires
- ☑️ **Require linear history** : Garde un historique Git propre
- ☑️ **Include administrators** : Les règles s'appliquent aussi aux admins

### 5. Sauvegarder

Cliquez sur **Create** ou **Save changes** en bas de la page.

## Workflow Après Configuration

### Pour Développer une Fonctionnalité

```bash
# 1. Créer une nouvelle branche
git checkout -b feature/ma-nouvelle-fonctionnalite

# 2. Faire vos modifications
git add .
git commit -m "feat: ajout de ma fonctionnalité"

# 3. Pousser la branche
git push origin feature/ma-nouvelle-fonctionnalite

# 4. Créer une Pull Request sur GitHub
# Les tests s'exécuteront automatiquement
```

### État de la Pull Request

Une fois la PR créée :
- ⏳ Les tests démarrent automatiquement
- ✅ Si tous les tests passent → Le bouton "Merge" devient disponible
- ❌ Si des tests échouent → Le merge est bloqué jusqu'à correction

## Vérification des Tests

### Voir les Résultats des Tests

1. Allez sur votre Pull Request
2. Scrollez vers le bas jusqu'à la section "Checks"
3. Cliquez sur **Details** à côté de "Test Summary"
4. Vous verrez les logs de chaque microservice testé

### Tests Exécutés

Le workflow teste automatiquement :
- ✅ **Event Service** : API d'événements
- ✅ **Group Service** : Gestion des groupes
- ✅ **Safety Service** : Alertes de sécurité
- ✅ **User Service** : Gestion des utilisateurs
- ✅ **Rating Service** : Système de notation

Chaque service est testé avec :
- Une base de données PostgreSQL 15 isolée
- Le schéma complet (schema.sql + migrations)
- Tests unitaires et d'intégration

## Débloquer une PR Bloquée

Si les tests échouent :

1. **Consulter les logs** :
   ```
   PR → Checks → Test Summary → Details
   ```

2. **Corriger localement** :
   ```bash
   # Corriger le code
   git add .
   git commit -m "fix: correction des tests"
   git push
   ```

3. **Les tests se relancent automatiquement** après le push

## Bypass d'Urgence (Déconseillé)

En cas d'urgence absolue, un admin peut :
1. Aller dans Settings → Branches
2. Modifier la règle
3. Décocher temporairement "Require status checks"
4. **Ne pas oublier de réactiver après !**

## Support

Pour toute question sur la configuration :
- Consultez la [documentation GitHub](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
- Vérifiez que le workflow `.github/workflows/test.yaml` est présent
- Testez avec une PR de test avant d'activer pour de vrai

## Validation de la Configuration

Pour tester que tout fonctionne :

```bash
# Créer une branche de test
git checkout -b test/branch-protection
echo "test" >> README.md
git add README.md
git commit -m "test: validation branch protection"
git push origin test/branch-protection
```

Puis créez une PR sur GitHub et vérifiez que les tests s'exécutent.
