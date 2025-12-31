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

1. Créer un fichier `.env` à la racine du projet
2. Copier le contenu de `env.example.txt` dans `.env`
3. Remplacer `VOTRE_MOT_DE_PASSE` par votre vrai mot de passe Neon

**IMPORTANT** : Le fichier `.env` est dans `.gitignore` et ne sera jamais commité dans Git.

## Étape 4 : Vérifier la connexion

```bash
python main.py
```

Si tout fonctionne, vous devriez voir :
- ✓ Connexion à la base de données Neon réussie
- ✓ Nombre de tables dans la base : 0 (pour l'instant)

## Prochaines étapes

Une fois le cahier des charges reçu, nous créerons :
1. Les modèles de données (DAL)
2. La logique métier (BLL)
3. L'interface utilisateur (UI)
4. Les tests unitaires

