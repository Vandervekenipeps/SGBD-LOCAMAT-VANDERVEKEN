# Documentation CI/CD - Application LOCA-MAT

## Vue d'ensemble

Le pipeline CI/CD (Continuous Integration / Continuous Deployment) de l'application LOCA-MAT est configuré avec **GitHub Actions**. Il s'exécute automatiquement à chaque push ou pull request pour vérifier que le code fonctionne correctement avant de le fusionner dans les branches principales.

**Fichier de configuration** : `.github/workflows/ci.yml`

---

## Déclencheurs du Pipeline

Le pipeline s'exécute automatiquement dans les cas suivants :

### 1. Push sur les branches principales
- ✅ Push sur la branche `main`
- ✅ Push sur la branche `develop`

### 2. Pull Requests
- ✅ Pull Request vers `main`
- ✅ Pull Request vers `develop`

### Exemple
```yaml
on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]
```

**Note** : Le pipeline ne s'exécute pas sur les autres branches (feature, hotfix, etc.) pour économiser les ressources.

---

## Environnement d'exécution

### Système d'exploitation
- **OS** : `ubuntu-latest` (dernière version d'Ubuntu LTS)
- **Architecture** : x64

### Version Python
- **Python 3.11** (configuré dans le workflow)

### Avantages
- ✅ Environnement isolé et reproductible
- ✅ Pas d'impact sur votre machine locale
- ✅ Tests dans un environnement propre à chaque exécution

---

## Étapes du Pipeline

Le pipeline est composé de 6 étapes principales, exécutées séquentiellement :

### 1. Checkout du code

**Nom** : `Checkout code`

**Action** : `actions/checkout@v3`

**Description** :
- Récupère le code source depuis le dépôt GitHub
- Clone le repository dans l'environnement d'exécution
- Permet aux étapes suivantes d'accéder au code

**Durée** : ~10-20 secondes

---

### 2. Configuration de Python

**Nom** : `Set up Python`

**Action** : `actions/setup-python@v4`

**Configuration** :
```yaml
python-version: '3.11'
```

**Description** :
- Installe Python 3.11 dans l'environnement
- Configure les chemins et variables d'environnement
- Prépare l'environnement pour l'exécution des tests

**Durée** : ~30-60 secondes

---

### 3. Installation des dépendances

**Nom** : `Install dependencies`

**Commandes** :
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

**Description** :
- Met à jour pip vers la dernière version
- Installe toutes les dépendances listées dans `requirements.txt` :
  - SQLAlchemy 2.0.23 (ORM)
  - psycopg2-binary 2.9.9 (Driver PostgreSQL)
  - python-dotenv 1.0.0 (Variables d'environnement)
  - python-dateutil 2.8.2 (Utilitaires dates)
  - pytest 7.4.3 (Framework de tests)
  - pytest-cov 4.1.0 (Couverture de code)

**Durée** : ~1-2 minutes (selon la vitesse de téléchargement)

**Important** : Si cette étape échoue, toutes les étapes suivantes échoueront également.

---

### 4. Lint avec flake8 (Optionnel)

**Nom** : `Lint with flake8 (optionnel)`

**Commandes** :
```bash
pip install flake8
# Les commandes flake8 sont commentées pour le moment
```

**Description** :
- Installe flake8 (linter Python)
- **Note** : Les commandes de lint sont actuellement commentées
- Cette étape ne bloque pas le pipeline (`continue-on-error: true`)

**Commandes disponibles (commentées)** :
```bash
# Vérification stricte des erreurs critiques
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics

# Vérification complète avec rapport
flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
```

**Activation** : Pour activer le lint, décommenter les lignes 30-31 dans `ci.yml`

**Durée** : ~10-30 secondes (si activé)

---

### 5. Tests avec pytest

**Nom** : `Test with pytest`

**Commandes** :
```bash
pip install pytest pytest-cov
pytest tests/ -v --cov=. --cov-report=xml
```

**Description** :
- Installe pytest et pytest-cov
- Exécute tous les tests dans le dossier `tests/`
- Options :
  - `-v` : Mode verbeux (affiche chaque test)
  - `--cov=.` : Calcule la couverture de code pour tout le projet
  - `--cov-report=xml` : Génère un rapport XML de couverture

**Variables d'environnement** :
```yaml
DATABASE_URL: ${{ secrets.DATABASE_URL }}
```

**Note** : Cette étape ne bloque pas le pipeline (`continue-on-error: true`)

**Durée** : ~1-3 minutes (selon le nombre de tests)

**Rapport de couverture** :
- Génère un fichier `coverage.xml`
- Peut être visualisé dans GitHub Actions ou avec des outils externes

---

### 6. Tests avec test_application.py

**Nom** : `Test application (test_application.py)`

**Commande** :
```bash
python tests/test_application.py
```

**Description** :
- Exécute la suite de tests complète de l'application
- Teste toutes les fonctionnalités principales :
  - ✅ Connexion à la base de données
  - ✅ Contraintes d'intégrité (UNIQUE, RESTRICT)
  - ✅ Trigger de validation de statut
  - ✅ Calcul tarifaire
  - ✅ Transactions ACID
  - ✅ Requêtes d'agrégation

**Variables d'environnement** :
```yaml
DATABASE_URL: ${{ secrets.DATABASE_URL }}
DEBUG_MODE: "False"
```

**Note** : Cette étape ne bloque pas le pipeline (`continue-on-error: true`)

**Durée** : ~30-60 secondes

**Sortie attendue** :
```
================================================================================
SUITE DE TESTS - APPLICATION LOCA-MAT
================================================================================
[...]
[SUCCES] TOUS LES TESTS SONT PASSES !
================================================================================
```

**Documentation détaillée** : Voir `tests/DOCUMENTATION_TESTS.md`

---

### 7. Vérification du build

**Nom** : `Build check`

**Commandes** :
```bash
python -c "import sqlalchemy; print('SQLAlchemy import OK')"
python -c "from config.database import engine; print('Database config OK')"
```

**Description** :
- Vérifie que SQLAlchemy peut être importé
- Vérifie que la configuration de la base de données est valide
- Teste que les imports principaux fonctionnent

**Note** : Cette étape ne bloque pas le pipeline (`continue-on-error: true`)

**Durée** : ~5-10 secondes

**Résultat attendu** :
```
SQLAlchemy import OK
Database config OK
```

---

## Variables d'environnement

### Secrets GitHub

Le pipeline utilise des **secrets GitHub** pour stocker les informations sensibles :

#### DATABASE_URL

**Type** : Secret GitHub

**Utilisation** : Connexion à la base de données Neon PostgreSQL

**Format** :
```
postgresql://user:password@host:port/database
```

**Configuration** :
1. Aller dans votre repository GitHub
2. Cliquer sur **Settings** → **Secrets and variables** → **Actions**
3. Cliquer sur **New repository secret**
4. Nom : `DATABASE_URL`
5. Valeur : Votre chaîne de connexion PostgreSQL complète
6. Cliquer sur **Add secret**

**Sécurité** :
- ✅ Les secrets ne sont jamais affichés dans les logs
- ✅ Les secrets ne sont accessibles que dans les workflows GitHub Actions
- ✅ Les secrets ne sont pas visibles dans les pull requests des forks

---

### Variables d'environnement du pipeline

#### DEBUG_MODE

**Valeur** : `"False"`

**Description** : Désactive les breakpoints de débogage dans les tests

**Utilisation** : Utilisé par `test_application.py` pour contrôler les breakpoints

**Note** : Toujours défini à `False` dans le CI/CD pour une exécution normale

---

## Résultats du Pipeline

### Statuts possibles

#### ✅ Succès (vert)
- Toutes les étapes se sont exécutées sans erreur
- Le code est prêt à être fusionné

#### ⚠️ Succès avec avertissements (jaune)
- Certaines étapes optionnelles ont échoué (`continue-on-error: true`)
- Le pipeline continue mais des problèmes peuvent exister
- **Recommandation** : Vérifier les logs des étapes en échec

#### ❌ Échec (rouge)
- Une étape critique a échoué (checkout, installation, build check)
- Le code ne peut pas être fusionné
- **Action** : Corriger les erreurs et recommitter

---

### Consultation des résultats

1. **Dans GitHub** :
   - Aller dans l'onglet **Actions** de votre repository
   - Cliquer sur le workflow qui vous intéresse
   - Voir les détails de chaque étape

2. **Dans les logs** :
   - Cliquer sur une étape pour voir les logs détaillés
   - Les erreurs sont affichées en rouge
   - Les succès sont affichés en vert

3. **Notifications** :
   - GitHub envoie des notifications par email si configuré
   - Les statuts apparaissent dans les pull requests

---

## Gestion des erreurs

### Étapes avec `continue-on-error: true`

Actuellement, **4 étapes** ne bloquent pas le pipeline en cas d'échec :

1. ✅ Lint with flake8
2. ✅ Test with pytest
3. ✅ Test application (test_application.py)
4. ✅ Build check

**Conséquence** : Le pipeline peut être marqué comme "succès" même si des tests échouent.

### Recommandation

Pour que les tests bloquent le pipeline en cas d'échec, retirer `continue-on-error: true` des étapes de test :

```yaml
- name: Test application (test_application.py)
  run: |
    python tests/test_application.py
  # Retirer cette ligne pour bloquer en cas d'échec :
  # continue-on-error: true
  env:
    DATABASE_URL: ${{ secrets.DATABASE_URL }}
    DEBUG_MODE: "False"
```

---

## Améliorations possibles

### 1. Activer le linting

Décommenter les lignes 30-31 dans `ci.yml` :

```yaml
- name: Lint with flake8
  run: |
    pip install flake8
    flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
    flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
```

### 2. Bloquer le pipeline en cas d'échec de test

Retirer `continue-on-error: true` des étapes de test pour garantir la qualité du code.

### 3. Ajouter des notifications

Ajouter une étape de notification (Slack, Discord, Email) en cas d'échec :

```yaml
- name: Notify on failure
  if: failure()
  run: |
    # Envoyer une notification
```

### 4. Ajouter un cache pour les dépendances

Accélérer les builds en mettant en cache les dépendances Python :

```yaml
- name: Cache pip packages
  uses: actions/cache@v3
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
```

### 5. Tests sur plusieurs versions de Python

Tester sur plusieurs versions de Python pour garantir la compatibilité :

```yaml
strategy:
  matrix:
    python-version: ['3.10', '3.11', '3.12']
```

---

## Exécution locale du pipeline

### Simuler le pipeline localement

Pour tester le pipeline localement avant de pousser :

```bash
# 1. Installer les dépendances
pip install -r requirements.txt

# 2. Configurer les variables d'environnement
export DATABASE_URL="votre_url_de_connexion"
export DEBUG_MODE="False"

# 3. Exécuter les tests
python tests/test_application.py

# 4. Exécuter pytest (si configuré)
pytest tests/ -v --cov=. --cov-report=xml
```

### Utiliser act (outil local GitHub Actions)

Installer `act` pour exécuter les workflows GitHub Actions localement :

```bash
# Installation (Windows avec Chocolatey)
choco install act-cli

# Exécution
act -l  # Lister les workflows
act push  # Exécuter le workflow push
```

**Note** : `act` nécessite Docker pour fonctionner.

---

## Dépannage

### Problème : Pipeline échoue à l'installation des dépendances

**Solution** :
- Vérifier que `requirements.txt` est à jour
- Vérifier que toutes les dépendances sont compatibles avec Python 3.11
- Vérifier les versions dans `requirements.txt`

### Problème : Tests échouent avec erreur de connexion

**Solution** :
- Vérifier que le secret `DATABASE_URL` est correctement configuré
- Vérifier que la base de données Neon est accessible depuis l'extérieur
- Vérifier que l'URL de connexion est au bon format

### Problème : Pipeline prend trop de temps

**Solution** :
- Activer le cache des dépendances (voir section "Améliorations")
- Paralléliser les tests si possible
- Optimiser les tests pour réduire leur durée

### Problème : Tests passent localement mais échouent dans le CI

**Solution** :
- Vérifier que les variables d'environnement sont identiques
- Vérifier que la version de Python est la même (3.11)
- Vérifier que les dépendances sont les mêmes versions
- Vérifier les logs du CI pour voir l'erreur exacte

---

## Statistiques du pipeline

### Durée moyenne

- **Checkout** : ~10-20 secondes
- **Setup Python** : ~30-60 secondes
- **Install dependencies** : ~1-2 minutes
- **Lint** : ~10-30 secondes (si activé)
- **Tests pytest** : ~1-3 minutes
- **Tests application** : ~30-60 secondes
- **Build check** : ~5-10 secondes

**Total** : ~3-7 minutes par exécution

### Coûts

- **GitHub Actions** : Gratuit pour les repositories publics
- **GitHub Actions** : 2000 minutes/mois gratuites pour les repositories privés
- **Neon Database** : Selon votre plan (gratuit jusqu'à 0.5 GB)

---

## Diagramme du pipeline

```
┌─────────────────────────────────────────────────────────────┐
│                    DÉCLENCHEUR                               │
│  Push sur main/develop OU Pull Request vers main/develop     │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  ÉTAPE 1: Checkout code                                     │
│  → Clone le repository                                       │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  ÉTAPE 2: Set up Python                                     │
│  → Installe Python 3.11                                     │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  ÉTAPE 3: Install dependencies                             │
│  → pip install -r requirements.txt                          │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  ÉTAPE 4: Lint with flake8 (optionnel)                     │
│  → Vérifie la qualité du code                               │
│  → continue-on-error: true                                  │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  ÉTAPE 5: Test with pytest                                  │
│  → pytest tests/ -v --cov=.                                 │
│  → continue-on-error: true                                  │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  ÉTAPE 6: Test application (test_application.py)          │
│  → python tests/test_application.py                         │
│  → continue-on-error: true                                  │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  ÉTAPE 7: Build check                                       │
│  → Vérifie les imports                                       │
│  → continue-on-error: true                                  │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    RÉSULTAT                                  │
│  ✅ Succès OU ❌ Échec                                       │
└─────────────────────────────────────────────────────────────┘
```

---

## Conclusion

Le pipeline CI/CD de l'application LOCA-MAT :

- ✅ S'exécute automatiquement à chaque push/PR
- ✅ Teste le code dans un environnement isolé
- ✅ Vérifie la qualité et la fonctionnalité
- ✅ Utilise des secrets sécurisés pour la base de données
- ✅ Fournit des rapports détaillés sur les résultats

**Prochaine étape** : Considérer retirer `continue-on-error: true` des étapes de test pour garantir que seuls les codes testés et validés peuvent être fusionnés.

---

## Ressources

- **Documentation GitHub Actions** : https://docs.github.com/en/actions
- **Documentation des tests** : `tests/DOCUMENTATION_TESTS.md`
- **Fichier de configuration** : `.github/workflows/ci.yml`
- **Requirements** : `requirements.txt`

