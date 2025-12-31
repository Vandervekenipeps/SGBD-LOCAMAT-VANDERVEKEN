"""
Point d'entrée principal de l'application LOCAMAT.

Ce fichier initialise l'application et peut servir de point de départ
pour les tests ou le lancement de l'interface utilisateur.
"""

from config.database import init_db, engine
from sqlalchemy import inspect

def main():
    """
    Fonction principale de l'application.
    
    Initialise la base de données et vérifie la connexion.
    """
    print("=" * 50)
    print("Application LOCAMAT - Gestion de Location de Matériel")
    print("=" * 50)
    
    try:
        # Vérifier la connexion à la base de données
        with engine.connect() as connection:
            print("✓ Connexion à la base de données Neon réussie")
            
            # Afficher les informations de la base de données
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            print(f"✓ Nombre de tables dans la base : {len(tables)}")
            if tables:
                print(f"  Tables existantes : {', '.join(tables)}")
            else:
                print("  Aucune table n'existe encore.")
        
        # Initialiser la base de données (créer les tables si nécessaire)
        # Décommenter cette ligne une fois les modèles créés
        # init_db()
        
        print("\n✓ Application prête à être utilisée")
        
    except Exception as e:
        print(f"✗ Erreur lors de l'initialisation : {e}")
        print("\nVérifiez que :")
        print("  1. Le fichier .env existe et contient DATABASE_URL")
        print("  2. La connexion à Neon est active")
        print("  3. Les dépendances sont installées (pip install -r requirements.txt)")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())

