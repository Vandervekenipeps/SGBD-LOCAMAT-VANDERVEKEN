"""
Interface graphique - Tableau de bord décisionnel.

Affiche les indicateurs calculés en temps réel dans une fenêtre graphique.
"""

import tkinter as tk
from tkinter import ttk
from sqlalchemy.orm import Session
from datetime import date

from dal.repositories import ContratRepository


class FenetreTableauBord:
    """
    Fenêtre affichant le tableau de bord avec tous les indicateurs.
    """
    
    def __init__(self, parent, db: Session):
        """Initialise la fenêtre du tableau de bord."""
        self.db = db
        self.window = tk.Toplevel(parent)
        self.window.title("Tableau de Bord - LOCA-MAT")
        self.window.geometry("900x700")
        
        self._creer_interface()
        self._charger_donnees()
    
    def _creer_interface(self):
        """Crée l'interface de la fenêtre."""
        # En-tête
        header = ttk.Label(
            self.window,
            text="TABLEAU DE BORD - LOCA-MAT ENTREPRISE",
            font=("Arial", 16, "bold")
        )
        header.pack(pady=10)
        
        # Notebook pour les onglets
        notebook = ttk.Notebook(self.window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Onglet Top 5
        self.frame_top5 = ttk.Frame(notebook, padding=10)
        notebook.add(self.frame_top5, text="Top 5 Matériels Rentables")
        
        # Onglet CA
        self.frame_ca = ttk.Frame(notebook, padding=10)
        notebook.add(self.frame_ca, text="Chiffre d'Affaires")
        
        # Onglet Alertes
        self.frame_alertes = ttk.Frame(notebook, padding=10)
        notebook.add(self.frame_alertes, text="Alertes Retards")
        
        # Bouton de rafraîchissement
        btn_refresh = ttk.Button(
            self.window,
            text="🔄 Rafraîchir",
            command=self._charger_donnees
        )
        btn_refresh.pack(pady=5)
    
    def _charger_donnees(self):
        """Charge et affiche les données du tableau de bord."""
        # Top 5
        self._afficher_top5()
        
        # CA 30 jours
        self._afficher_ca()
        
        # Alertes
        self._afficher_alertes()
    
    def _afficher_top5(self):
        """Affiche le top 5 des matériels rentables."""
        # Nettoyer le frame
        for widget in self.frame_top5.winfo_children():
            widget.destroy()
        
        top_5 = ContratRepository.get_top_5_rentables(self.db)
        
        if not top_5:
            label = ttk.Label(
                self.frame_top5,
                text="Aucun matériel loué ce mois-ci.",
                font=("Arial", 12)
            )
            label.pack(pady=20)
            return
        
        # En-tête du tableau
        headers = ["Rang", "Marque", "Modèle", "Catégorie", "CA Total (€)"]
        for i, header in enumerate(headers):
            label = ttk.Label(
                self.frame_top5,
                text=header,
                font=("Arial", 10, "bold")
            )
            label.grid(row=0, column=i, padx=10, pady=5, sticky=tk.W)
        
        # Données
        for i, materiel in enumerate(top_5, 1):
            ttk.Label(self.frame_top5, text=str(i)).grid(row=i, column=0, padx=10, pady=2)
            ttk.Label(self.frame_top5, text=materiel['marque']).grid(row=i, column=1, padx=10, pady=2)
            ttk.Label(self.frame_top5, text=materiel['modele']).grid(row=i, column=2, padx=10, pady=2)
            ttk.Label(self.frame_top5, text=materiel['categorie']).grid(row=i, column=3, padx=10, pady=2)
            ttk.Label(self.frame_top5, text=f"{materiel['ca_total']:.2f}").grid(row=i, column=4, padx=10, pady=2)
    
    def _afficher_ca(self):
        """Affiche le chiffre d'affaires des 30 derniers jours."""
        # Nettoyer le frame
        for widget in self.frame_ca.winfo_children():
            widget.destroy()
        
        ca_30_jours = ContratRepository.get_ca_30_jours(self.db)
        
        label_title = ttk.Label(
            self.frame_ca,
            text="Chiffre d'Affaires des 30 Derniers Jours",
            font=("Arial", 14, "bold")
        )
        label_title.pack(pady=20)
        
        label_ca = ttk.Label(
            self.frame_ca,
            text=f"{float(ca_30_jours):.2f} EUR",
            font=("Arial", 24, "bold"),
            foreground="green"
        )
        label_ca.pack(pady=10)
    
    def _afficher_alertes(self):
        """Affiche les alertes de retards."""
        # Nettoyer le frame
        for widget in self.frame_alertes.winfo_children():
            widget.destroy()
        
        retards = ContratRepository.get_retards(self.db)
        
        if not retards:
            label = ttk.Label(
                self.frame_alertes,
                text="✅ Aucun retard à signaler.",
                font=("Arial", 12),
                foreground="green"
            )
            label.pack(pady=20)
            return
        
        # En-tête
        label_title = ttk.Label(
            self.frame_alertes,
            text=f"⚠️ {len(retards)} Contrat(s) en Retard",
            font=("Arial", 14, "bold"),
            foreground="red"
        )
        label_title.pack(pady=10)
        
        # Liste des retards
        for contrat in retards:
            jours_retard = (date.today() - contrat.date_fin).days
            frame_retard = ttk.Frame(self.frame_alertes)
            frame_retard.pack(fill=tk.X, padx=10, pady=5)
            
            text = (
                f"Contrat #{contrat.id} - Client ID: {contrat.client_id} - "
                f"Date retour prévue: {contrat.date_fin} - "
                f"Retard: {jours_retard} jour(s)"
            )
            ttk.Label(frame_retard, text=text, font=("Arial", 10)).pack(anchor=tk.W)




