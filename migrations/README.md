# Scripts de Migration SQL

Ce dossier contient les scripts SQL supplémentaires pour les triggers et contraintes avancées.

## Utilisation

1. Les tables sont créées automatiquement par SQLAlchemy lors du premier lancement de l'application (`python main.py`)

2. Pour ajouter les triggers supplémentaires, exécutez le script SQL :
   ```bash
   # Via psql ou votre client PostgreSQL
   psql $DATABASE_URL -f migrations/01_create_triggers.sql
   ```

## Contenu

- `00_create_tables.sql` : Création des tables avec contraintes de base
- `01_create_triggers.sql` : Trigger pour valider le changement de statut des articles
- `02_add_date_achat_constraint.sql` : Contrainte CHECK pour valider que la date d'achat n'est pas dans le futur

## Note

Les contraintes principales (PK, FK, NOT NULL, UNIQUE, CHECK) sont définies dans les modèles SQLAlchemy (`dal/models.py`).

Les triggers SQL offrent une protection supplémentaire au niveau de la base de données, mais la logique métier principale est gérée dans la couche BLL.

## Migration 02 : Contrainte date d'achat

**Fichier** : `02_add_date_achat_constraint.sql`

**Objectif** : Ajouter une contrainte CHECK pour garantir que la date d'achat d'un article ne peut pas être dans le futur.

**Contrainte ajoutée** :
- `check_date_achat_passee` : Vérifie que `date_achat <= CURRENT_DATE`

Cette contrainte est également validée dans la couche BLL (`bll/validation.py`) pour fournir des messages d'erreur clairs à l'utilisateur.



