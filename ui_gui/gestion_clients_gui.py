"""
Interface graphique - Gestion des clients.

Permet de lister et ajouter des clients.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from sqlalchemy.orm import Session

from dal.models import Client
from dal.repositories import ClientRepository


class FenetreGestionClients:
    """
    Fenêtre de gestion des clients.
    """
    
    def __init__(self, parent, db: Session):
        """Initialise la fenêtre."""
        self.db = db
        self.window = tk.Toplevel(parent)
        self.window.title("Gestion des Clients - LOCA-MAT")
        self.window.geometry("900x600")
        
        self._creer_interface()
        self._charger_liste()
    
    def _creer_interface(self):
        """Crée l'interface de la fenêtre."""
        # En-tête
        header = ttk.Label(
            self.window,
            text="GESTION DES CLIENTS",
            font=("Arial", 16, "bold")
        )
        header.pack(pady=10)
        
        # Boutons d'action
        btn_frame = ttk.Frame(self.window)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="➕ Ajouter un Client", command=self._ajouter_client).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🔄 Rafraîchir", command=self._charger_liste).pack(side=tk.LEFT, padx=5)
        
        # Liste des clients avec Treeview
        list_frame = ttk.Frame(self.window)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Treeview
        self.tree = ttk.Treeview(
            list_frame,
            columns=("ID", "Nom", "Prénom", "Email", "Téléphone", "Adresse", "VIP"),
            show="headings",
            yscrollcommand=scrollbar.set
        )
        scrollbar.config(command=self.tree.yview)
        
        # Configuration des colonnes
        self.tree.heading("ID", text="ID")
        self.tree.heading("Nom", text="Nom")
        self.tree.heading("Prénom", text="Prénom")
        self.tree.heading("Email", text="Email")
        self.tree.heading("Téléphone", text="Téléphone")
        self.tree.heading("Adresse", text="Adresse")
        self.tree.heading("VIP", text="VIP")
        
        self.tree.column("ID", width=50)
        self.tree.column("Nom", width=100)
        self.tree.column("Prénom", width=100)
        self.tree.column("Email", width=200)
        self.tree.column("Téléphone", width=120)
        self.tree.column("Adresse", width=150)
        self.tree.column("VIP", width=50)
        
        self.tree.pack(fill=tk.BOTH, expand=True)
    
    def _charger_liste(self):
        """Charge et affiche la liste des clients."""
        # Vider le treeview
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Charger les clients
        clients = ClientRepository.get_all(self.db)
        
        for client in clients:
            self.tree.insert(
                "",
                tk.END,
                values=(
                    client.id,
                    client.nom,
                    client.prenom,
                    client.email,
                    client.telephone or "",
                    client.adresse or "",
                    "⭐" if bool(client.est_vip) else ""
                )
            )
    
    def _ajouter_client(self):
        """Ouvre une fenêtre pour ajouter un client."""
        FenetreAjoutClient(self.window, self.db, self._charger_liste)


class FenetreAjoutClient:
    """Fenêtre pour ajouter un nouveau client."""
    
    def __init__(self, parent, db: Session, callback_refresh):
        self.db = db
        self.callback_refresh = callback_refresh
        
        self.window = tk.Toplevel(parent)
        self.window.title("Ajouter un Client")
        self.window.geometry("500x400")
        
        self._creer_interface()
    
    def _creer_interface(self):
        """Crée l'interface de la fenêtre."""
        ttk.Label(self.window, text="Ajouter un Nouveau Client", font=("Arial", 14, "bold")).pack(pady=10)
        
        # Formulaire
        form_frame = ttk.Frame(self.window, padding=20)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # Champs
        ttk.Label(form_frame, text="Nom *:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.nom = ttk.Entry(form_frame, width=30)
        self.nom.grid(row=0, column=1, pady=5)
        
        ttk.Label(form_frame, text="Prénom *:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.prenom = ttk.Entry(form_frame, width=30)
        self.prenom.grid(row=1, column=1, pady=5)
        
        ttk.Label(form_frame, text="Email *:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.email = ttk.Entry(form_frame, width=30)
        self.email.grid(row=2, column=1, pady=5)
        
        ttk.Label(form_frame, text="Téléphone:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.telephone = ttk.Entry(form_frame, width=30)
        self.telephone.grid(row=3, column=1, pady=5)
        
        ttk.Label(form_frame, text="Adresse:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.adresse = ttk.Entry(form_frame, width=30)
        self.adresse.grid(row=4, column=1, pady=5)
        
        ttk.Label(form_frame, text="Client VIP:").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.est_vip = tk.BooleanVar()
        ttk.Checkbutton(form_frame, variable=self.est_vip).grid(row=5, column=1, sticky=tk.W, pady=5)
        
        # Boutons
        btn_frame = ttk.Frame(self.window)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="Ajouter", command=self._ajouter).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Annuler", command=self.window.destroy).pack(side=tk.LEFT, padx=5)
    
    def _ajouter(self):
        """Ajoute le client."""
        try:
            # Validation des champs obligatoires
            if not all([self.nom.get(), self.prenom.get(), self.email.get()]):
                messagebox.showerror("Erreur", "Les champs Nom, Prénom et Email sont obligatoires.")
                return
            
            # Validation basique de l'email
            if '@' not in self.email.get() or '.' not in self.email.get().split('@')[-1]:
                messagebox.showerror("Erreur", "Format d'email invalide.")
                return
            
            # Créer le client
            client = Client(
                nom=self.nom.get(),
                prenom=self.prenom.get(),
                email=self.email.get(),
                telephone=self.telephone.get() or None,
                adresse=self.adresse.get() or None,
                est_vip=self.est_vip.get()
            )
            
            ClientRepository.create(self.db, client)
            messagebox.showinfo("Succès", f"Client créé avec succès (ID: {client.id})")
            self.callback_refresh()
            self.window.destroy()
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la création : {e}")

