"""
Interface graphique principale - Fenêtre principale de l'application LOCA-MAT.

Cette fenêtre utilise Tkinter pour créer une interface graphique moderne.
Toute la logique métier est déléguée à la couche BLL, aucune requête SQL
n'apparaît dans ce code.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from sqlalchemy.orm import Session

from config.database import SessionLocal
from ui_gui.gestion_parc_gui import FenetreGestionParc
from ui_gui.gestion_clients_gui import FenetreGestionClients
from ui_gui.creation_location_gui import FenetreCreationLocation
from ui_gui.restitution_gui import FenetreRestitution
from ui_gui.tableau_bord_gui import FenetreTableauBord


class MainWindow:
    """
    Fenêtre principale de l'application LOCA-MAT.
    
    Affiche le menu principal avec tous les boutons pour accéder
    aux différentes fonctionnalités.
    """
    
    def __init__(self):
        """Initialise la fenêtre principale."""
        self.root = tk.Tk()
        self.root.title("LOCA-MAT ENTREPRISE - Système de Gestion de Location")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # Session de base de données
        self.db: Session = SessionLocal()
        
        # Créer l'interface
        self._creer_interface()
        
        # Gérer la fermeture de la fenêtre
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _creer_interface(self):
        """Crée l'interface utilisateur de la fenêtre principale."""
        # En-tête
        header_frame = ttk.Frame(self.root, padding="20")
        header_frame.pack(fill=tk.X)
        
        title_label = ttk.Label(
            header_frame,
            text="LOCA-MAT ENTREPRISE",
            font=("Arial", 20, "bold")
        )
        title_label.pack()
        
        subtitle_label = ttk.Label(
            header_frame,
            text="Système de Gestion de Location",
            font=("Arial", 12)
        )
        subtitle_label.pack()
        
        # Séparateur
        ttk.Separator(self.root, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=20, pady=10)
        
        # Menu principal
        menu_frame = ttk.Frame(self.root, padding="20")
        menu_frame.pack(fill=tk.BOTH, expand=True)
        
        # Boutons du menu
        buttons = [
            ("📊 Tableau de Bord", self._ouvrir_tableau_bord),
            ("📦 Gestion du Parc", self._ouvrir_gestion_parc),
            ("👥 Gestion des Clients", self._ouvrir_gestion_clients),
            ("📝 Créer une Location", self._ouvrir_creation_location),
            ("↩️ Restituer un Article", self._ouvrir_restitution),
        ]
        
        for i, (text, command) in enumerate(buttons):
            btn = ttk.Button(
                menu_frame,
                text=text,
                command=command,
                width=30,
                padding=10
            )
            btn.pack(pady=5, fill=tk.X)
        
        # Pied de page
        footer_frame = ttk.Frame(self.root, padding="10")
        footer_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        footer_label = ttk.Label(
            footer_frame,
            text="Application LOCA-MAT - Version Graphique",
            font=("Arial", 9)
        )
        footer_label.pack()
    
    def _ouvrir_tableau_bord(self):
        """Ouvre la fenêtre du tableau de bord."""
        FenetreTableauBord(self.root, self.db)
    
    def _ouvrir_gestion_parc(self):
        """Ouvre la fenêtre de gestion du parc."""
        FenetreGestionParc(self.root, self.db)
    
    def _ouvrir_gestion_clients(self):
        """Ouvre la fenêtre de gestion des clients."""
        FenetreGestionClients(self.root, self.db)
    
    def _ouvrir_creation_location(self):
        """Ouvre la fenêtre de création de location."""
        FenetreCreationLocation(self.root, self.db)
    
    def _ouvrir_restitution(self):
        """Ouvre la fenêtre de restitution d'article."""
        FenetreRestitution(self.root, self.db)
    
    def _on_closing(self):
        """Gère la fermeture de l'application."""
        self.db.close()
        self.root.destroy()
    
    def run(self):
        """Lance l'application."""
        self.root.mainloop()



