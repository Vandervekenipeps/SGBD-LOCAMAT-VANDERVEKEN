"""
Point d'entrée principal de l'application LOCAMAT.

Ce fichier initialise l'application et lance l'interface utilisateur.
"""

from config.database import init_db, engine
from sqlalchemy import inspect
from ui.menu_principal import MenuPrincipal

def main():
    """
    Fonction principale de l'application.
    
    Initialise la base de données et lance le menu principal.
    """
    print("=" * 50)
    print("Application LOCAMAT - Gestion de Location de Matériel")
    print("=" * 50)
    
    try:
        # Vérifier la connexion à la base de données
        with engine.connect() as connection:
            print("[OK] Connexion a la base de donnees Neon reussie")
            
            # Afficher les informations de la base de données
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            print(f"[OK] Nombre de tables dans la base : {len(tables)}")
            if tables:
                print(f"  Tables existantes : {', '.join(tables)}")
            else:
                print("  Aucune table n'existe encore.")
        
        # Initialiser la base de données (créer les tables si nécessaire)
        init_db()
        
        print("\n[OK] Application prete a etre utilisee")
        
        # Lancer le menu principal
        menu = MenuPrincipal()
        menu.executer()
        
    except Exception as e:
        print(f"[ERREUR] Erreur lors de l'initialisation : {e}")
        print("\nVérifiez que :")
        print("  1. Le fichier .env existe et contient DATABASE_URL")
        print("  2. La connexion à Neon est active")
        print("  3. Les dépendances sont installées (pip install -r requirements.txt)")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())

