# Guide de Configuration Initiale

## Étape 1 : Créer l'environnement virtuel Python

```bash
# Créer l'environnement virtuel
python -m venv venv

# Activer l'environnement virtuel
# Sur Windows (PowerShell) :
venv\Scripts\activate

# Sur Linux/Mac :
source venv/bin/activate
```

## Étape 2 : Installer les dépendances

```bash
pip install -r requirements.txt
```

## Étape 3 : Configurer la connexion à la base de données

1. **Créer un fichier `.env` à la racine du projet** (à la même place que `main.py`)
2. **Ajouter votre URL de connexion Neon** dans ce fichier :

```
DATABASE_URL=postgresql://neondb_owner:VOTRE_MOT_DE_PASSE@ep-curly-fire-agsyh90f-pooler.c-2.eu-central-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require
```

3. **Remplacer `VOTRE_MOT_DE_PASSE`** par votre vrai mot de passe Neon (celui que vous avez dans votre dashboard Neon)

**IMPORTANT** : 
- Le fichier `.env` est dans `.gitignore` et ne sera jamais commité dans Git
- Ne partagez JAMAIS ce fichier ou votre mot de passe

## Étape 4 : Créer les tables dans Neon

Une fois le fichier `.env` créé, initialisez la base de données :

```bash
python init_database.py
```

Ce script va :
- Vérifier la connexion à Neon
- Créer toutes les tables nécessaires (articles, clients, contrats, articles_contrats)
- Afficher la structure des tables créées

## Étape 5 : Lancer l'application

```bash
python main.py
```

Si tout fonctionne, vous devriez voir :
- ✓ Connexion à la base de données Neon réussie
- ✓ Nombre de tables dans la base : 4
- Le menu principal de l'application

## Prochaines étapes

Une fois le cahier des charges reçu, nous créerons :
1. Les modèles de données (DAL)
2. La logique métier (BLL)
3. L'interface utilisateur (UI)
4. Les tests unitaires

