"""
Interface graphique - Création d'une location.

Permet de créer une nouvelle location avec sélection de client, articles et dates.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from sqlalchemy.orm import Session
from datetime import date

from dal.models import Article
from dal.repositories import ArticleRepository, ClientRepository, ContratRepository
from bll.transactions import ServiceTransaction
from bll.tarification import ServiceTarification
from bll.validation import ServiceValidation


class FenetreCreationLocation:
    """
    Fenêtre de création d'une location.
    """
    
    def __init__(self, parent, db: Session):
        """Initialise la fenêtre."""
        self.db = db
        self.window = tk.Toplevel(parent)
        self.window.title("Créer une Location - LOCA-MAT")
        self.window.geometry("800x700")
        
        self.articles_selectionnes = []
        self._creer_interface()
        self._charger_clients()
        self._charger_articles()
    
    def _creer_interface(self):
        """Crée l'interface de la fenêtre."""
        # En-tête
        header = ttk.Label(
            self.window,
            text="CRÉATION D'UNE LOCATION",
            font=("Arial", 16, "bold")
        )
        header.pack(pady=10)
        
        # Notebook pour les onglets
        notebook = ttk.Notebook(self.window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Onglet 1: Sélection du client
        self.frame_client = ttk.Frame(notebook, padding=10)
        notebook.add(self.frame_client, text="1. Client")
        self._creer_onglet_client()
        
        # Onglet 2: Sélection des articles
        self.frame_articles = ttk.Frame(notebook, padding=10)
        notebook.add(self.frame_articles, text="2. Articles")
        self._creer_onglet_articles()
        
        # Onglet 3: Dates et validation
        self.frame_dates = ttk.Frame(notebook, padding=10)
        notebook.add(self.frame_dates, text="3. Dates & Validation")
        self._creer_onglet_dates()
        
        # Bouton de création
        btn_frame = ttk.Frame(self.window)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="✅ Créer la Location", command=self._creer_location).pack(padx=5)
    
    def _creer_onglet_client(self):
        """Crée l'onglet de sélection du client."""
        ttk.Label(self.frame_client, text="Sélectionner un Client", font=("Arial", 12, "bold")).pack(pady=10)
        
        # Liste des clients
        list_frame = ttk.Frame(self.frame_client)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree_clients = ttk.Treeview(
            list_frame,
            columns=("ID", "Nom", "Prénom", "Email", "VIP"),
            show="headings",
            yscrollcommand=scrollbar.set
        )
        scrollbar.config(command=self.tree_clients.yview)
        
        self.tree_clients.heading("ID", text="ID")
        self.tree_clients.heading("Nom", text="Nom")
        self.tree_clients.heading("Prénom", text="Prénom")
        self.tree_clients.heading("Email", text="Email")
        self.tree_clients.heading("VIP", text="VIP")
        
        self.tree_clients.column("ID", width=50)
        self.tree_clients.column("Nom", width=100)
        self.tree_clients.column("Prénom", width=100)
        self.tree_clients.column("Email", width=200)
        self.tree_clients.column("VIP", width=50)
        
        self.tree_clients.pack(fill=tk.BOTH, expand=True)
        self.tree_clients.bind("<<TreeviewSelect>>", self._on_client_select)
        
        self.client_selectionne = None
        self.label_client = ttk.Label(self.frame_client, text="Client sélectionné: Aucun", font=("Arial", 10))
        self.label_client.pack(pady=5)
    
    def _creer_onglet_articles(self):
        """Crée l'onglet de sélection des articles."""
        ttk.Label(self.frame_articles, text="Sélectionner les Articles Disponibles", font=("Arial", 12, "bold")).pack(pady=10)
        
        # Liste des articles disponibles
        list_frame = ttk.Frame(self.frame_articles)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree_articles = ttk.Treeview(
            list_frame,
            columns=("ID", "Marque", "Modèle", "Catégorie", "Prix/jour"),
            show="headings",
            yscrollcommand=scrollbar.set
        )
        scrollbar.config(command=self.tree_articles.yview)
        
        self.tree_articles.heading("ID", text="ID")
        self.tree_articles.heading("Marque", text="Marque")
        self.tree_articles.heading("Modèle", text="Modèle")
        self.tree_articles.heading("Catégorie", text="Catégorie")
        self.tree_articles.heading("Prix/jour", text="Prix/jour (€)")
        
        self.tree_articles.column("ID", width=50)
        self.tree_articles.column("Marque", width=100)
        self.tree_articles.column("Modèle", width=120)
        self.tree_articles.column("Catégorie", width=100)
        self.tree_articles.column("Prix/jour", width=100)
        
        self.tree_articles.pack(fill=tk.BOTH, expand=True)
        
        # Boutons d'action
        btn_frame = ttk.Frame(self.frame_articles)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="➕ Ajouter au Panier", command=self._ajouter_au_panier).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🔄 Rafraîchir", command=self._charger_articles).pack(side=tk.LEFT, padx=5)
        
        # Panier
        ttk.Label(self.frame_articles, text="Articles dans le panier:", font=("Arial", 10, "bold")).pack(pady=10)
        self.label_panier = ttk.Label(self.frame_articles, text="Aucun article sélectionné", font=("Arial", 9))
        self.label_panier.pack()
    
    def _creer_onglet_dates(self):
        """Crée l'onglet de saisie des dates."""
        ttk.Label(self.frame_dates, text="Période de Location", font=("Arial", 12, "bold")).pack(pady=10)
        
        form_frame = ttk.Frame(self.frame_dates, padding=20)
        form_frame.pack()
        
        ttk.Label(form_frame, text="Date de début (YYYY-MM-DD) *:").grid(row=0, column=0, sticky=tk.W, pady=10)
        self.date_debut = ttk.Entry(form_frame, width=20)
        self.date_debut.grid(row=0, column=1, pady=10)
        
        ttk.Label(form_frame, text="Date de fin (YYYY-MM-DD) *:").grid(row=1, column=0, sticky=tk.W, pady=10)
        self.date_fin = ttk.Entry(form_frame, width=20)
        self.date_fin.grid(row=1, column=1, pady=10)
        
        # Aperçu du calcul
        ttk.Label(self.frame_dates, text="Aperçu du Calcul", font=("Arial", 10, "bold")).pack(pady=20)
        self.label_calcul = ttk.Label(self.frame_dates, text="Sélectionnez un client et des articles pour voir le calcul", font=("Arial", 9))
        self.label_calcul.pack()
        
        ttk.Button(self.frame_dates, text="🔄 Calculer le Prix", command=self._calculer_prix).pack(pady=10)
    
    def _charger_clients(self):
        """Charge la liste des clients."""
        for item in self.tree_clients.get_children():
            self.tree_clients.delete(item)
        
        clients = ClientRepository.get_all(self.db)
        for client in clients:
            self.tree_clients.insert(
                "",
                tk.END,
                values=(
                    client.id,
                    client.nom,
                    client.prenom,
                    client.email,
                    "⭐" if bool(client.est_vip) else ""
                )
            )
    
    def _charger_articles(self):
        """Charge la liste des articles disponibles."""
        for item in self.tree_articles.get_children():
            self.tree_articles.delete(item)
        
        articles = ArticleRepository.get_disponibles(self.db)
        for art in articles:
            self.tree_articles.insert(
                "",
                tk.END,
                values=(
                    art.id,
                    art.marque,
                    art.modele,
                    art.categorie,
                    f"{art.prix_journalier:.2f}"
                )
            )
    
    def _ajouter_au_panier(self):
        """Ajoute l'article sélectionné au panier."""
        selection = self.tree_articles.selection()
        if not selection:
            messagebox.showwarning("Aucune sélection", "Veuillez sélectionner un article.")
            return
        
        item = self.tree_articles.item(selection[0])
        article_id = int(item['values'][0])
        
        article = ArticleRepository.get_by_id(self.db, article_id)
        if not article:
            return
        
        # Vérifier si déjà dans le panier
        if any(a.id == article_id for a in self.articles_selectionnes):
            messagebox.showinfo("Info", "Cet article est déjà dans le panier.")
            return
        
        self.articles_selectionnes.append(article)
        self._mettre_a_jour_panier()
    
    def _on_client_select(self, event):
        """Gère la sélection d'un client."""
        selection = self.tree_clients.selection()
        if not selection:
            self.client_selectionne = None
            self.label_client.config(text="Client sélectionné: Aucun")
            return
        
        item = self.tree_clients.item(selection[0])
        self.client_selectionne = int(item['values'][0])
        client_nom = f"{item['values'][1]} {item['values'][2]}"
        self.label_client.config(text=f"Client sélectionné: {client_nom} (ID: {self.client_selectionne})")
    
    def _mettre_a_jour_panier(self):
        """Met à jour l'affichage du panier."""
        if not self.articles_selectionnes:
            self.label_panier.config(text="Aucun article sélectionné")
        else:
            text = ", ".join([f"{a.marque} {a.modele} (ID:{a.id})" for a in self.articles_selectionnes])
            self.label_panier.config(text=text)
    
    def _calculer_prix(self):
        """Calcule et affiche le prix prévisionnel."""
        if not self.client_selectionne:
            messagebox.showwarning("Client manquant", "Veuillez sélectionner un client.")
            return
        
        if not self.articles_selectionnes:
            messagebox.showwarning("Articles manquants", "Veuillez sélectionner au moins un article.")
            return
        
        try:
            date_debut = date.fromisoformat(self.date_debut.get())
            date_fin = date.fromisoformat(self.date_fin.get())
        except ValueError:
            messagebox.showerror("Erreur", "Format de date invalide. Utilisez YYYY-MM-DD")
            return
        
        client = ClientRepository.get_by_id(self.db, int(self.client_selectionne))
        calcul = ServiceTarification.calculer_prix_final(
            self.articles_selectionnes, client, date_debut, date_fin, self.db
        )
        
        texte = (
            f"Prix de base : {calcul['prix_base']:.2f} €\n"
            f"Remise durée (>7j) : -{calcul['remise_duree']:.2f} €\n"
            f"Remise VIP : -{calcul['remise_vip']:.2f} €\n"
            f"Surcharge retard : +{calcul['surcharge_retard']:.2f} €\n"
            f"\nPRIX FINAL : {calcul['prix_final']:.2f} €"
        )
        self.label_calcul.config(text=texte)
    
    def _creer_location(self):
        """Crée la location."""
        if not self.client_selectionne:
            messagebox.showerror("Erreur", "Veuillez sélectionner un client.")
            return
        
        if not self.articles_selectionnes:
            messagebox.showerror("Erreur", "Veuillez sélectionner au moins un article.")
            return
        
        try:
            date_debut = date.fromisoformat(self.date_debut.get())
            date_fin = date.fromisoformat(self.date_fin.get())
        except ValueError:
            messagebox.showerror("Erreur", "Format de date invalide. Utilisez YYYY-MM-DD")
            return
        
        # Valider les dates
        dates_valides, msg_dates = ServiceValidation.valider_dates_location(date_debut, date_fin)
        if not dates_valides:
            messagebox.showerror("Erreur", msg_dates)
            return
        
        # Confirmer
        if not messagebox.askyesno("Confirmation", "Créer cette location ?"):
            return
        
        article_ids = [a.id for a in self.articles_selectionnes]
        
        succes, contrat, message = ServiceTransaction.valider_panier_transactionnel(
            self.db, int(self.client_selectionne), article_ids, date_debut, date_fin
        )
        
        if succes and contrat:
            messagebox.showinfo("Succès", f"{message}\n\nContrat créé avec succès (ID: {contrat.id})")
            self.window.destroy()
        else:
            messagebox.showerror("Erreur", message)

