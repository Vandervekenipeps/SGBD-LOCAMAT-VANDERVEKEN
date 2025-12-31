"""
Point d'entrée pour l'interface graphique de l'application LOCA-MAT.

Lance l'interface graphique Tkinter au lieu de l'interface console.
"""

from config.database import init_db
from ui_gui.main_window import MainWindow

if __name__ == "__main__":
    try:
        # Initialiser la base de données
        init_db()
        
        # Lancer l'interface graphique
        app = MainWindow()
        app.run()
        
    except Exception as e:
        print(f"Erreur lors de l'initialisation : {e}")
        print("\nVérifiez que :")
        print("1. Le fichier .env existe et contient DATABASE_URL")
        print("2. La connexion à Neon est active")
        print("3. Les dépendances sont installées (pip install -r requirements.txt)")


