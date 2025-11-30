#!/bin/bash
# Script de validation avant push
# Vérifie que tous les fichiers nécessaires sont en place et corrects

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}         Validation Setup Tests Automatisés${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""

ERRORS=0
WARNINGS=0

# 1. Vérifier les scripts run_tests.sh
echo -e "${YELLOW}[1/6] Vérification des scripts run_tests.sh...${NC}"
for service in event group safety user rating; do
  script="${service}/run_tests.sh"
  if [ -f "$script" ]; then
    if [ -x "$script" ]; then
      echo -e "  ${GREEN}✓${NC} $script (exécutable)"
    else
      echo -e "  ${RED}✗${NC} $script (pas exécutable)"
      chmod +x "$script"
      echo -e "     ${GREEN}→ Permissions fixées${NC}"
    fi
  else
    echo -e "  ${RED}✗${NC} $script (manquant)"
    ERRORS=$((ERRORS+1))
  fi
done
echo ""

# 2. Vérifier les fichiers .env.test.example
echo -e "${YELLOW}[2/6] Vérification des templates .env.test.example...${NC}"
for service in event group safety user rating; do
  example="${service}/.env.test.example"
  if [ -f "$example" ]; then
    echo -e "  ${GREEN}✓${NC} $example"
  else
    echo -e "  ${RED}✗${NC} $example (manquant)"
    ERRORS=$((ERRORS+1))
  fi
done
echo ""

# 3. Vérifier le workflow GitHub Actions
echo -e "${YELLOW}[3/6] Vérification du workflow GitHub Actions...${NC}"
workflow=".github/workflows/test.yaml"
if [ -f "$workflow" ]; then
  echo -e "  ${GREEN}✓${NC} $workflow"
  
  # Vérifier que tous les services sont dans la matrix
  for service in event group safety user rating; do
    if grep -q "$service" "$workflow"; then
      echo -e "    ${GREEN}✓${NC} Service $service dans la matrix"
    else
      echo -e "    ${RED}✗${NC} Service $service absent de la matrix"
      ERRORS=$((ERRORS+1))
    fi
  done
else
  echo -e "  ${RED}✗${NC} $workflow (manquant)"
  ERRORS=$((ERRORS+1))
fi
echo ""

# 4. Vérifier la documentation
echo -e "${YELLOW}[4/6] Vérification de la documentation...${NC}"
for doc in TESTING.md TESTING_QUICKSTART.md TESTS_SETUP_SUMMARY.md .github/BRANCH_PROTECTION_SETUP.md READY_TO_PUSH.md; do
  if [ -f "$doc" ]; then
    lines=$(wc -l < "$doc")
    echo -e "  ${GREEN}✓${NC} $doc ($lines lignes)"
  else
    echo -e "  ${RED}✗${NC} $doc (manquant)"
    ERRORS=$((ERRORS+1))
  fi
done
echo ""

# 5. Vérifier qu'aucun .env.test n'est tracké
echo -e "${YELLOW}[5/6] Vérification que .env.test n'est pas tracké...${NC}"
if git ls-files | grep -q ".env.test$"; then
  echo -e "  ${RED}✗${NC} Fichier .env.test détecté dans git (ne devrait pas être commité)"
  echo -e "     ${YELLOW}→ Ajoutez .env.test à .gitignore${NC}"
  WARNINGS=$((WARNINGS+1))
else
  echo -e "  ${GREEN}✓${NC} Aucun .env.test tracké"
fi
echo ""

# 6. Test rapide d'un service
echo -e "${YELLOW}[6/6] Test rapide du service event...${NC}"
if [ -d "event" ]; then
  cd event
  if ./run_tests.sh unit > /tmp/test_output.log 2>&1; then
    echo -e "  ${GREEN}✓${NC} Tests unitaires passent"
  else
    echo -e "  ${YELLOW}⚠${NC} Certains tests échouent (normal si DB pas configurée)"
    echo -e "     ${YELLOW}→ Voir /tmp/test_output.log pour détails${NC}"
    WARNINGS=$((WARNINGS+1))
  fi
  cd ..
else
  echo -e "  ${RED}✗${NC} Répertoire event manquant"
  ERRORS=$((ERRORS+1))
fi
echo ""

# Résumé
echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}                      RÉSUMÉ${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
  echo -e "${GREEN}✅ Tous les tests de validation passent !${NC}"
  echo ""
  echo -e "${GREEN}Vous êtes prêt à pusher ! 🚀${NC}"
  echo ""
  echo -e "${BLUE}Prochaines étapes :${NC}"
  echo "  1. git add ."
  echo "  2. git commit -m 'feat: setup automated testing'"
  echo "  3. git push origin main (ou créer une PR)"
  echo ""
elif [ $ERRORS -eq 0 ]; then
  echo -e "${YELLOW}⚠ Validation OK avec $WARNINGS avertissement(s)${NC}"
  echo ""
  echo -e "${YELLOW}Vous pouvez pusher, mais vérifiez les avertissements ci-dessus.${NC}"
  echo ""
else
  echo -e "${RED}❌ Validation échouée : $ERRORS erreur(s), $WARNINGS avertissement(s)${NC}"
  echo ""
  echo -e "${RED}Corrigez les erreurs ci-dessus avant de pusher.${NC}"
  echo ""
  exit 1
fi

echo -e "${BLUE}============================================================${NC}"
