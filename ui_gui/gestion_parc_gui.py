"""
Interface graphique - Gestion du parc d'articles.

Permet de lister, ajouter, modifier et supprimer des articles.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from sqlalchemy.orm import Session
from datetime import date

from dal.models import Article, StatutArticle
from dal.repositories import ArticleRepository
from bll.validation import ServiceValidation


class FenetreGestionParc:
    """
    Fenêtre de gestion du parc d'articles.
    """
    
    def __init__(self, parent, db: Session):
        """Initialise la fenêtre."""
        self.db = db
        self.window = tk.Toplevel(parent)
        self.window.title("Gestion du Parc - LOCA-MAT")
        self.window.geometry("1000x700")
        
        self._creer_interface()
        self._charger_liste()
    
    def _creer_interface(self):
        """Crée l'interface de la fenêtre."""
        # En-tête
        header = ttk.Label(
            self.window,
            text="GESTION DU PARC D'ARTICLES",
            font=("Arial", 16, "bold")
        )
        header.pack(pady=10)
        
        # Boutons d'action
        btn_frame = ttk.Frame(self.window)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="➕ Ajouter un Article", command=self._ajouter_article).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🔄 Rafraîchir", command=self._charger_liste).pack(side=tk.LEFT, padx=5)
        
        # Liste des articles avec Treeview
        list_frame = ttk.Frame(self.window)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Treeview
        self.tree = ttk.Treeview(
            list_frame,
            columns=("ID", "Catégorie", "Marque", "Modèle", "N° Série", "Date Achat", "Statut", "Prix/jour"),
            show="headings",
            yscrollcommand=scrollbar.set
        )
        scrollbar.config(command=self.tree.yview)
        
        # Configuration des colonnes
        self.tree.heading("ID", text="ID")
        self.tree.heading("Catégorie", text="Catégorie")
        self.tree.heading("Marque", text="Marque")
        self.tree.heading("Modèle", text="Modèle")
        self.tree.heading("N° Série", text="N° Série")
        self.tree.heading("Date Achat", text="Date Achat")
        self.tree.heading("Statut", text="Statut")
        self.tree.heading("Prix/jour", text="Prix/jour (€)")
        
        self.tree.column("ID", width=50)
        self.tree.column("Catégorie", width=100)
        self.tree.column("Marque", width=100)
        self.tree.column("Modèle", width=120)
        self.tree.column("N° Série", width=120)
        self.tree.column("Date Achat", width=100)
        self.tree.column("Statut", width=120)
        self.tree.column("Prix/jour", width=100)
        
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # Boutons d'action sur sélection
        action_frame = ttk.Frame(self.window)
        action_frame.pack(pady=10)
        
        ttk.Button(action_frame, text="✏️ Modifier Statut", command=self._modifier_statut).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="🗑️ Supprimer", command=self._supprimer_article).pack(side=tk.LEFT, padx=5)
    
    def _charger_liste(self):
        """Charge et affiche la liste des articles."""
        # Vider le treeview
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Charger les articles
        articles = ArticleRepository.get_all(self.db)
        
        for art in articles:
            self.tree.insert(
                "",
                tk.END,
                values=(
                    art.id,
                    art.categorie,
                    art.marque,
                    art.modele,
                    art.numero_serie,
                    art.date_achat.strftime("%Y-%m-%d"),
                    art.statut.value,
                    f"{art.prix_journalier:.2f}"
                )
            )
    
    def _ajouter_article(self):
        """Ouvre une fenêtre pour ajouter un article."""
        FenetreAjoutArticle(self.window, self.db, self._charger_liste)
    
    def _modifier_statut(self):
        """Modifie le statut de l'article sélectionné."""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Aucune sélection", "Veuillez sélectionner un article.")
            return
        
        item = self.tree.item(selection[0])
        article_id = item['values'][0]
        
        article = ArticleRepository.get_by_id(self.db, article_id)
        if not article:
            messagebox.showerror("Erreur", f"Article {article_id} introuvable.")
            return
        
        FenetreModifierStatut(self.window, self.db, article, self._charger_liste)
    
    def _supprimer_article(self):
        """Supprime l'article sélectionné."""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Aucune sélection", "Veuillez sélectionner un article.")
            return
        
        item = self.tree.item(selection[0])
        article_id = item['values'][0]
        
        if not messagebox.askyesno("Confirmation", f"Êtes-vous sûr de vouloir supprimer l'article {article_id} ?"):
            return
        
        try:
            if ArticleRepository.delete(self.db, article_id):
                messagebox.showinfo("Succès", "Article supprimé avec succès.")
                self._charger_liste()
            else:
                messagebox.showerror(
                    "Erreur",
                    f"Impossible de supprimer l'article {article_id}.\n"
                    "Il est peut-être lié à un contrat."
                )
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la suppression : {e}")


class FenetreAjoutArticle:
    """Fenêtre pour ajouter un nouvel article."""
    
    def __init__(self, parent, db: Session, callback_refresh):
        self.db = db
        self.callback_refresh = callback_refresh
        
        self.window = tk.Toplevel(parent)
        self.window.title("Ajouter un Article")
        self.window.geometry("500x400")
        
        self._creer_interface()
    
    def _creer_interface(self):
        """Crée l'interface de la fenêtre."""
        ttk.Label(self.window, text="Ajouter un Nouvel Article", font=("Arial", 14, "bold")).pack(pady=10)
        
        # Formulaire
        form_frame = ttk.Frame(self.window, padding=20)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # Champs
        ttk.Label(form_frame, text="Catégorie *:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.categorie = ttk.Entry(form_frame, width=30)
        self.categorie.grid(row=0, column=1, pady=5)
        
        ttk.Label(form_frame, text="Marque *:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.marque = ttk.Entry(form_frame, width=30)
        self.marque.grid(row=1, column=1, pady=5)
        
        ttk.Label(form_frame, text="Modèle *:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.modele = ttk.Entry(form_frame, width=30)
        self.modele.grid(row=2, column=1, pady=5)
        
        ttk.Label(form_frame, text="N° Série *:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.numero_serie = ttk.Entry(form_frame, width=30)
        self.numero_serie.grid(row=3, column=1, pady=5)
        
        ttk.Label(form_frame, text="Date Achat (YYYY-MM-DD) *:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.date_achat = ttk.Entry(form_frame, width=30)
        self.date_achat.grid(row=4, column=1, pady=5)
        
        ttk.Label(form_frame, text="Prix journalier (€) *:").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.prix_journalier = ttk.Entry(form_frame, width=30)
        self.prix_journalier.grid(row=5, column=1, pady=5)
        
        # Boutons
        btn_frame = ttk.Frame(self.window)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="Ajouter", command=self._ajouter).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Annuler", command=self.window.destroy).pack(side=tk.LEFT, padx=5)
    
    def _ajouter(self):
        """Ajoute l'article."""
        try:
            # Validation des champs
            if not all([self.categorie.get(), self.marque.get(), self.modele.get(), 
                       self.numero_serie.get(), self.date_achat.get(), self.prix_journalier.get()]):
                messagebox.showerror("Erreur", "Tous les champs sont obligatoires.")
                return
            
            date_achat = date.fromisoformat(self.date_achat.get())
            prix = float(self.prix_journalier.get())
            
            if prix <= 0:
                messagebox.showerror("Erreur", "Le prix journalier doit être supérieur à 0.")
                return
            
            # Valider la date d'achat
            date_valide, msg = ServiceValidation.valider_date_achat(date_achat)
            if not date_valide:
                messagebox.showerror("Erreur", msg)
                return
            
            # Créer l'article
            article = Article(
                categorie=self.categorie.get(),
                marque=self.marque.get(),
                modele=self.modele.get(),
                numero_serie=self.numero_serie.get(),
                date_achat=date_achat,
                prix_journalier=prix,
                statut=StatutArticle.DISPONIBLE
            )
            
            ArticleRepository.create(self.db, article)
            messagebox.showinfo("Succès", f"Article créé avec succès (ID: {article.id})")
            self.callback_refresh()
            self.window.destroy()
            
        except ValueError as e:
            messagebox.showerror("Erreur", f"Format invalide : {e}")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la création : {e}")


class FenetreModifierStatut:
    """Fenêtre pour modifier le statut d'un article."""
    
    def __init__(self, parent, db: Session, article: Article, callback_refresh):
        self.db = db
        self.article = article
        self.callback_refresh = callback_refresh
        
        self.window = tk.Toplevel(parent)
        self.window.title("Modifier le Statut")
        self.window.geometry("400x200")
        
        self._creer_interface()
    
    def _creer_interface(self):
        """Crée l'interface de la fenêtre."""
        ttk.Label(
            self.window,
            text=f"Modifier le statut de l'article {self.article.id}",
            font=("Arial", 12, "bold")
        ).pack(pady=10)
        
        ttk.Label(
            self.window,
            text=f"{self.article.marque} {self.article.modele} - Statut actuel: {self.article.statut.value}"
        ).pack(pady=5)
        
        # Sélection du nouveau statut
        ttk.Label(self.window, text="Nouveau statut:").pack(pady=10)
        
        self.statut_var = tk.StringVar(value=self.article.statut.value)
        statut_frame = ttk.Frame(self.window)
        statut_frame.pack()
        
        for statut in StatutArticle:
            ttk.Radiobutton(
                statut_frame,
                text=statut.value,
                variable=self.statut_var,
                value=statut.value
            ).pack(side=tk.LEFT, padx=10)
        
        # Boutons
        btn_frame = ttk.Frame(self.window)
        btn_frame.pack(pady=20)
        
        ttk.Button(btn_frame, text="Modifier", command=self._modifier).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Annuler", command=self.window.destroy).pack(side=tk.LEFT, padx=5)
    
    def _modifier(self):
        """Modifie le statut."""
        try:
            nouveau_statut = StatutArticle(self.statut_var.get())
            
            # Valider le changement
            est_valide, message = ServiceValidation.valider_changement_statut(
                self.db, self.article, nouveau_statut
            )
            
            if not est_valide:
                messagebox.showerror("Erreur", message)
                return
            
            self.article.statut = nouveau_statut  # type: ignore[assignment]
            ArticleRepository.update(self.db, self.article)
            
            messagebox.showinfo("Succès", "Statut modifié avec succès.")
            self.callback_refresh()
            self.window.destroy()
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la modification : {e}")

