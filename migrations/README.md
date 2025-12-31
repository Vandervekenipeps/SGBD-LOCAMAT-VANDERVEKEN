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

- `01_create_triggers.sql` : Trigger pour valider le changement de statut des articles

## Note

Les contraintes principales (PK, FK, NOT NULL, UNIQUE, CHECK) sont définies dans les modèles SQLAlchemy (`dal/models.py`).

Les triggers SQL offrent une protection supplémentaire au niveau de la base de données, mais la logique métier principale est gérée dans la couche BLL.



