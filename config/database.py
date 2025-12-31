"""
Configuration de la connexion à la base de données PostgreSQL (Neon).

Ce module gère la connexion à la base de données en utilisant SQLAlchemy.
Les informations de connexion sont chargées depuis le fichier .env pour
éviter de stocker des secrets dans le code source.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

# Récupérer l'URL de connexion depuis les variables d'environnement
DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL n'est pas définie dans le fichier .env. "
        "Veuillez créer un fichier .env avec votre URL de connexion Neon."
    )

# Créer le moteur SQLAlchemy
# echo=True permet d'afficher les requêtes SQL (utile pour le débogage)
engine = create_engine(
    DATABASE_URL,
    echo=False,  # Mettre à True pour voir les requêtes SQL dans les logs
    pool_pre_ping=True,  # Vérifie la connexion avant utilisation
    pool_recycle=3600,  # Recycle les connexions après 1 heure
)

# Créer la classe de session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base pour les modèles déclaratifs SQLAlchemy
Base = declarative_base()


def get_db():
    """
    Générateur de session de base de données.
    
    Utilisé pour obtenir une session DB dans les opérations.
    La session est automatiquement fermée après utilisation grâce au yield.
    
    Yields:
        Session: Session SQLAlchemy pour accéder à la base de données
        
    Example:
        with get_db() as db:
            users = db.query(User).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialise la base de données en créant toutes les tables.
    
    Cette fonction doit être appelée une fois au démarrage de l'application
    pour créer les tables dans la base de données si elles n'existent pas.
    """
    # Importer tous les modèles ici pour qu'ils soient enregistrés
    # (à faire quand les modèles seront créés)
    # from dal.models import User, Product, etc.
    
    # Créer toutes les tables
    Base.metadata.create_all(bind=engine)
    print("Base de données initialisée avec succès.")

