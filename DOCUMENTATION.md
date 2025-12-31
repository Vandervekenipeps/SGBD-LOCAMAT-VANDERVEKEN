# Documentation Technique - Projet LOCA-MAT

## 1. Architecture 3-Tier

### DAL (Data Access Layer) - `dal/`
**Responsabilité** : Gestion des accès à la base de données

- **`models.py`** : Définition des modèles SQLAlchemy (ORM)
  - `Article` : Matériel du parc
  - `Client` : Clients de l'entreprise
  - `Contrat` : Contrats de location
  - `ArticleContrat` : Table de liaison (normalisation 3NF)

- **`repositories.py`** : Opérations CRUD sur les entités
  - `ArticleRepository` : Gestion des articles
  - `ClientRepository` : Gestion des clients
  - `ContratRepository` : Gestion des contrats et requêtes d'agrégation

**Aucune logique métier dans cette couche** - Seulement des opérations de base de données.

### BLL (Business Logic Layer) - `bll/`
**Responsabilité** : Logique métier de l'application

- **`tarification.py`** : Calcul des prix selon les règles métier
  - Remise de 10% si durée > 7 jours
  - Remise de 15% si client VIP (cumulable)
  - Surcharge de 5% si retard précédent

- **`validation.py`** : Validations métier
  - Validation du changement de statut
  - Validation du panier
  - Validation des dates

- **`transactions.py`** : Gestion des transactions ACID
  - Validation atomique des paniers
  - Gestion de la concurrence (SELECT FOR UPDATE)
  - Rollback en cas d'erreur

**Aucune requête SQL directe** - Utilise les repositories de la couche DAL.

### UI (User Interface) - `ui/`
**Responsabilité** : Interface utilisateur

- **`menu_principal.py`** : Menu interactif en ligne de commande
- **`tableau_bord.py`** : Affichage des indicateurs décisionnels

**Aucune requête SQL** - Toutes les opérations passent par la couche BLL.

## 2. Contraintes d'Intégrité

### Contraintes SGBD (définies dans `dal/models.py`)

#### Clés Primaires (PK)
- `articles.id` : Auto-incrémenté
- `clients.id` : Auto-incrémenté
- `contrats.id` : Auto-incrémenté
- `articles_contrats.id` : Auto-incrémenté

#### Clés Étrangères (FK)
- `contrats.client_id` → `clients.id` (RESTRICT sur suppression)
- `articles_contrats.article_id` → `articles.id` (RESTRICT sur suppression)
- `articles_contrats.contrat_id` → `contrats.id` (CASCADE sur suppression)

**Règle d'intégrité 1** : Un article lié à un contrat ne peut pas être supprimé (RESTRICT).

#### Contraintes NOT NULL
- Tous les champs obligatoires sont marqués `nullable=False`

#### Contraintes UNIQUE
- `articles.numero_serie` : Unique
- `clients.email` : Unique

#### Contraintes CHECK
- `check_statut_article` : Statut doit être dans la liste autorisée
- `check_dates_contrat` : date_fin >= date_debut
- `check_statut_contrat` : Statut doit être valide

### Contraintes Programmatiques (BLL)

**Règle d'intégrité 2** : Un article ne peut passer au statut "Loué" que s'il est "Disponible"
- Validée dans `bll/validation.py` (ServiceValidation.valider_changement_statut)
- Protégée par trigger SQL (`migrations/01_create_triggers.sql`)

## 3. Transactions ACID

### Validation Atomique des Paniers

La méthode `ServiceTransaction.valider_panier_transactionnel()` garantit :

1. **Atomicité** : Toute la transaction réussit ou échoue (rollback)
2. **Cohérence** : Vérification de la disponibilité avant et après verrouillage
3. **Isolation** : Utilisation de `SELECT FOR UPDATE` pour éviter les conflits
4. **Durabilité** : Commit uniquement si tout est valide

### Gestion de la Concurrence

- **Verrous de ligne** : `SELECT FOR UPDATE` sur les articles
- **Re-vérification** : Disponibilité vérifiée après le verrouillage
- **Messages explicites** : "Conflit de concurrence détecté" si échec

## 4. Tableau de Bord Décisionnel

### Requêtes d'Agrégation SQL

Toutes les requêtes sont dans `dal/repositories.py` :

1. **Top 5 matériels rentables** : `ContratRepository.get_top_5_rentables()`
   - Utilise `GROUP BY`, `SUM()`, `ORDER BY`, `LIMIT`
   - Agrégation par article sur le mois en cours

2. **CA des 30 derniers jours** : `ContratRepository.get_ca_30_jours()`
   - Utilise `SUM()` avec filtre de date
   - Somme des prix totaux des contrats

3. **Liste d'alerte retards** : `ContratRepository.get_retards()`
   - Filtre sur statut "En Cours" et date dépassée
   - Aucune agrégation, mais requête optimisée

**Aucune boucle dans le code** - Tout est géré par des requêtes SQL optimisées.

## 5. Gestion des Erreurs

### Try/Catch dans toutes les opérations critiques

- **`bll/transactions.py`** : Gestion des `IntegrityError`, `OperationalError`
- **`ui/menu_principal.py`** : Capture des exceptions et affichage de messages clairs
- **Messages utilisateur** : Toutes les erreurs techniques sont traduites en français

### Exemples de messages

- "Conflit de concurrence détecté. Les articles suivants ne sont plus disponibles..."
- "Erreur d'intégrité : Impossible de créer le contrat..."
- "Erreur de connexion à la base de données. Veuillez réessayer."

## 6. Sécurité

### Secrets dans .env

- **Fichier `.env`** : Contient `DATABASE_URL` (dans `.gitignore`)
- **Fichier `env.example.txt`** : Modèle sans valeurs réelles
- **Aucun mot de passe en clair** dans le code source

### Requêtes Paramétrées

- SQLAlchemy utilise des requêtes paramétrées par défaut
- Protection contre les injections SQL

## 7. Structure de la Base de Données

### Schéma Normalisé (3NF)

```
articles (id, categorie, marque, modele, numero_serie, date_achat, statut, prix_journalier)
clients (id, nom, prenom, email, telephone, adresse, est_vip)
contrats (id, client_id, date_debut, date_fin, date_retour_reelle, prix_total, statut, date_creation)
articles_contrats (id, article_id, contrat_id)
```

**Normalisation** : Aucune redondance d'information, relations via clés étrangères.

## 8. Utilisation

### Initialisation

1. Créer le fichier `.env` avec `DATABASE_URL`
2. Installer les dépendances : `pip install -r requirements.txt`
3. Lancer l'application : `python main.py`
4. Les tables sont créées automatiquement

### Scripts SQL supplémentaires

Pour ajouter les triggers :
```bash
psql $DATABASE_URL -f migrations/01_create_triggers.sql
```

## 9. Points Clés pour la Défense

### Expliquabilité du Code

- **Tous les fichiers sont commentés en français**
- **Chaque fonction a une docstring explicative**
- **Architecture claire** : Séparation stricte des couches

### Débogage

- **Points d'arrêt possibles** : Dans `bll/transactions.py` (ligne de validation)
- **Variables inspectables** : `articles`, `calcul_prix`, `contrat`
- **Logs SQL** : Activer `echo=True` dans `config/database.py` pour voir les requêtes

### Modifications à Chaud

Exemples de modifications faciles :
- **Taux de TVA** : Modifier dans `bll/tarification.py` (lignes avec `Decimal('0.10')`, etc.)
- **Règle de validation** : Modifier dans `bll/validation.py`
- **Affichage** : Modifier dans `ui/menu_principal.py`

## 10. Livrables

✅ Code Source (Git) : Historique complet avec commits progressifs  
✅ Application fonctionnelle : Interface en ligne de commande  
✅ Base de données Cloud : Neon PostgreSQL  
✅ CI/CD : Pipeline GitHub Actions configuré  
✅ Documentation : Ce fichier + README.md + SETUP.md

