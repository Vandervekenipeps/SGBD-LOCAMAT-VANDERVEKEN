# Projet SGBD LOCAMAT

Projet de gestion de location de matériel réalisé dans le cadre du module SGBD.

## Technologies utilisées

- **Python** : Langage de programmation principal
- **SQLAlchemy** : ORM pour la gestion de la base de données
- **Neon** : Base de données PostgreSQL hébergée dans le cloud
- **Git** : Gestion de version avec historique propre

## Architecture

Le projet suit une architecture 3-tier (trois couches) :

- **DAL (Data Access Layer)** : Couche d'accès aux données, gestion des modèles SQLAlchemy
- **BLL (Business Logic Layer)** : Couche métier, logique de l'application (tarification, validations)
- **UI (User Interface)** : Couche présentation, interface utilisateur

## Installation

1. Cloner le dépôt
2. Créer un environnement virtuel Python :
   ```bash
   python -m venv venv
   ```

3. Activer l'environnement virtuel :
   - Windows : `venv\Scripts\activate`
   - Linux/Mac : `source venv/bin/activate`

4. Installer les dépendances :
   ```bash
   pip install -r requirements.txt
   ```

5. Créer le fichier `.env` à partir de `.env.example` et y mettre vos vraies valeurs de connexion

## Structure du projet

```
.
├── dal/              # Couche d'accès aux données
├── bll/              # Couche métier
├── ui/               # Interface utilisateur
├── config/           # Configuration (connexion DB, etc.)
├── tests/            # Tests unitaires
└── .env              # Variables d'environnement (non versionné)
```

## Sécurité

⚠️ **IMPORTANT** : Ne jamais committer le fichier `.env` contenant les mots de passe réels dans Git.


