"""
Interface graphique - Restitution d'article.

Permet de restituer un article d'un contrat en cours.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from sqlalchemy.orm import Session
from datetime import date

from dal.models import StatutContrat
from dal.repositories import ClientRepository, ContratRepository
from bll.transactions import ServiceTransaction


class FenetreRestitution:
    """
    Fenêtre de restitution d'article.
    """
    
    def __init__(self, parent, db: Session):
        """Initialise la fenêtre."""
        self.db = db
        self.window = tk.Toplevel(parent)
        self.window.title("Restitution d'Article - LOCA-MAT")
        self.window.geometry("900x700")
        
        self.contrat_selectionne = None
        self._creer_interface()
        self._charger_contrats()
    
    def _creer_interface(self):
        """Crée l'interface de la fenêtre."""
        # En-tête
        header = ttk.Label(
            self.window,
            text="RESTITUTION D'ARTICLE",
            font=("Arial", 16, "bold")
        )
        header.pack(pady=10)
        
        # Notebook
        notebook = ttk.Notebook(self.window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Onglet 1: Sélection du contrat
        self.frame_contrats = ttk.Frame(notebook, padding=10)
        notebook.add(self.frame_contrats, text="1. Contrats en Cours")
        self._creer_onglet_contrats()
        
        # Onglet 2: Articles du contrat
        self.frame_articles = ttk.Frame(notebook, padding=10)
        notebook.add(self.frame_articles, text="2. Articles du Contrat")
        self._creer_onglet_articles()
        
        # Bouton de restitution
        btn_frame = ttk.Frame(self.window)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="↩️ Restituer l'Article", command=self._restituer).pack(padx=5)
    
    def _creer_onglet_contrats(self):
        """Crée l'onglet de sélection du contrat."""
        ttk.Label(self.frame_contrats, text="Contrats en Cours", font=("Arial", 12, "bold")).pack(pady=10)
        
        # Liste des contrats
        list_frame = ttk.Frame(self.frame_contrats)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree_contrats = ttk.Treeview(
            list_frame,
            columns=("ID", "Client", "Date Début", "Date Fin", "Statut"),
            show="headings",
            yscrollcommand=scrollbar.set
        )
        scrollbar.config(command=self.tree_contrats.yview)
        
        self.tree_contrats.heading("ID", text="ID")
        self.tree_contrats.heading("Client", text="Client")
        self.tree_contrats.heading("Date Début", text="Date Début")
        self.tree_contrats.heading("Date Fin", text="Date Fin")
        self.tree_contrats.heading("Statut", text="Statut")
        
        self.tree_contrats.column("ID", width=50)
        self.tree_contrats.column("Client", width=150)
        self.tree_contrats.column("Date Début", width=100)
        self.tree_contrats.column("Date Fin", width=100)
        self.tree_contrats.column("Statut", width=100)
        
        self.tree_contrats.pack(fill=tk.BOTH, expand=True)
        self.tree_contrats.bind("<<TreeviewSelect>>", self._on_contrat_select)
        
        ttk.Button(self.frame_contrats, text="🔄 Rafraîchir", command=self._charger_contrats).pack(pady=10)
    
    def _creer_onglet_articles(self):
        """Crée l'onglet d'affichage des articles du contrat."""
        ttk.Label(self.frame_articles, text="Articles du Contrat Sélectionné", font=("Arial", 12, "bold")).pack(pady=10)
        
        # Liste des articles
        list_frame = ttk.Frame(self.frame_articles)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree_articles = ttk.Treeview(
            list_frame,
            columns=("ID", "Marque", "Modèle", "Statut"),
            show="headings",
            yscrollcommand=scrollbar.set
        )
        scrollbar.config(command=self.tree_articles.yview)
        
        self.tree_articles.heading("ID", text="ID")
        self.tree_articles.heading("Marque", text="Marque")
        self.tree_articles.heading("Modèle", text="Modèle")
        self.tree_articles.heading("Statut", text="Statut")
        
        self.tree_articles.column("ID", width=50)
        self.tree_articles.column("Marque", width=150)
        self.tree_articles.column("Modèle", width=150)
        self.tree_articles.column("Statut", width=120)
        
        self.tree_articles.pack(fill=tk.BOTH, expand=True)
        self.tree_articles.bind("<<TreeviewSelect>>", self._on_article_select)
        
        self.article_selectionne = None
        ttk.Label(self.frame_articles, text="Article sélectionné: Aucun", font=("Arial", 10)).pack(pady=5)
    
    def _charger_contrats(self):
        """Charge la liste des contrats en cours."""
        for item in self.tree_contrats.get_children():
            self.tree_contrats.delete(item)
        
        contrats = ContratRepository.get_en_cours(self.db)
        
        if not contrats:
            return
        
        for contrat in contrats:
            client = ClientRepository.get_by_id(self.db, contrat.client_id)  # type: ignore[arg-type]
            client_nom = f"{client.prenom} {client.nom}" if client else f"Client ID:{contrat.client_id}"
            
            self.tree_contrats.insert(
                "",
                tk.END,
                values=(
                    contrat.id,
                    client_nom,
                    contrat.date_debut.strftime("%Y-%m-%d"),
                    contrat.date_fin.strftime("%Y-%m-%d"),
                    contrat.statut.value
                )
            )
    
    def _on_contrat_select(self, event):
        """Gère la sélection d'un contrat."""
        selection = self.tree_contrats.selection()
        if not selection:
            return
        
        item = self.tree_contrats.item(selection[0])
        contrat_id = item['values'][0]
        
        self.contrat_selectionne = contrat_id
        self._charger_articles_contrat(contrat_id)
    
    def _charger_articles_contrat(self, contrat_id: int):
        """Charge les articles du contrat sélectionné."""
        for item in self.tree_articles.get_children():
            self.tree_articles.delete(item)
        
        articles = ContratRepository.get_articles_du_contrat(self.db, contrat_id)
        
        for article in articles:
            self.tree_articles.insert(
                "",
                tk.END,
                values=(
                    article.id,
                    article.marque,
                    article.modele,
                    article.statut.value
                )
            )
    
    def _on_article_select(self, event):
        """Gère la sélection d'un article."""
        selection = self.tree_articles.selection()
        if not selection:
            self.article_selectionne = None
            return
        
        item = self.tree_articles.item(selection[0])
        self.article_selectionne = item['values'][0]
    
    def _restituer(self):
        """Restitue l'article sélectionné."""
        if not self.contrat_selectionne:
            messagebox.showerror("Erreur", "Veuillez sélectionner un contrat.")
            return
        
        if not self.article_selectionne:
            messagebox.showerror("Erreur", "Veuillez sélectionner un article à restituer.")
            return
        
        if not messagebox.askyesno("Confirmation", f"Restituer l'article {self.article_selectionne} du contrat {self.contrat_selectionne} ?"):
            return
        
        succes, message = ServiceTransaction.restituer_article(
            self.db, self.contrat_selectionne, self.article_selectionne
        )
        
        if succes:
            messagebox.showinfo("Succès", message)
            self._charger_contrats()
            if self.contrat_selectionne:
                self._charger_articles_contrat(self.contrat_selectionne)
        else:
            messagebox.showerror("Erreur", message)




