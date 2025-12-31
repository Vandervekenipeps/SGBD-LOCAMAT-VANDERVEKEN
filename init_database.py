"""
Script d'initialisation de la base de données.

Ce script crée toutes les tables dans la base de données Neon
et peut être exécuté pour initialiser ou réinitialiser la base.
"""

from config.database import init_db, engine
from sqlalchemy import inspect
import sys


def main():
    """
    Initialise la base de données en créant toutes les tables.
    """
    print("=" * 80)
    print("INITIALISATION DE LA BASE DE DONNÉES NEON")
    print("=" * 80)
    
    try:
        # Vérifier la connexion
        print("\n1. Verification de la connexion a Neon...")
        with engine.connect() as connection:
            print("   [OK] Connexion reussie")
        
        # Vérifier les tables existantes
        print("\n2. Vérification des tables existantes...")
        inspector = inspect(engine)
        tables_avant = inspector.get_table_names()
        
        if tables_avant:
            print(f"   Tables existantes : {', '.join(tables_avant)}")
            print("\n   Les tables existantes seront conservees.")
            print("   Seules les tables manquantes seront creees.")
        
        # Créer les tables
        print("\n3. Création des tables...")
        init_db()
        
        # Vérifier les tables créées
        print("\n4. Vérification finale...")
        inspector = inspect(engine)
        tables_apres = inspector.get_table_names()
        
        print(f"\n   [OK] {len(tables_apres)} table(s) creee(s) :")
        for table in tables_apres:
            print(f"      - {table}")
        
        # Afficher la structure de chaque table
        print("\n5. Structure des tables :")
        for table_name in tables_apres:
            print(f"\n   Table: {table_name}")
            columns = inspector.get_columns(table_name)
            for col in columns:
                nullable = "NULL" if col['nullable'] else "NOT NULL"
                default = f" DEFAULT {col['default']}" if col.get('default') else ""
                print(f"      - {col['name']}: {col['type']} {nullable}{default}")
        
        print("\n" + "=" * 80)
        print("[OK] INITIALISATION TERMINEE AVEC SUCCES")
        print("=" * 80)
        print("\nVous pouvez maintenant lancer l'application avec : python main.py")
        
        return 0
        
    except Exception as e:
        print(f"\n[ERREUR] ERREUR lors de l'initialisation : {e}")
        print("\nVérifiez que :")
        print("  1. Le fichier .env existe à la racine du projet")
        print("  2. Le fichier .env contient DATABASE_URL avec vos identifiants Neon")
        print("  3. La connexion à Neon est active")
        print("  4. Les dépendances sont installées (pip install -r requirements.txt)")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())


