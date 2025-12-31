"""
Interface utilisateur - Menu principal de l'application.

Ce module gère l'interface en ligne de commande pour l'application LOCA-MAT.
Toutes les interactions utilisateur sont gérées ici, mais aucune requête SQL
n'apparaît dans ce code (toutes les opérations passent par la couche BLL).
"""

from sqlalchemy.orm import Session
from datetime import date, timedelta
from typing import List

from config.database import get_db, SessionLocal
from dal.models import Article, Client, StatutArticle
from dal.repositories import ArticleRepository, ClientRepository, ContratRepository
from bll.transactions import ServiceTransaction
from bll.validation import ServiceValidation
from bll.tarification import ServiceTarification
from ui.tableau_bord import TableauBord


class MenuPrincipal:
    """
    Classe principale pour gérer le menu et les interactions utilisateur.
    """
    
    def __init__(self):
        """Initialise le menu principal."""
        self.db: Session = SessionLocal()
    
    def afficher_menu(self):
        """Affiche le menu principal."""
        print("\n" + "=" * 80)
        print("LOCA-MAT ENTREPRISE - Système de Gestion de Location")
        print("=" * 80)
        print("\n1. Tableau de bord")
        print("2. Gestion du parc (CRUD Articles)")
        print("3. Gestion des clients")
        print("4. Créer une location")
        print("5. Restituer un article")
        print("6. Quitter")
        print("-" * 80)
    
    def executer(self):
        """Boucle principale du menu."""
        while True:
            self.afficher_menu()
            choix = input("\nVotre choix : ").strip()
            
            if choix == "1":
                self.afficher_tableau_bord()
            elif choix == "2":
                self.menu_gestion_parc()
            elif choix == "3":
                self.menu_gestion_clients()
            elif choix == "4":
                self.creer_location()
            elif choix == "5":
                self.restituer_article()
            elif choix == "6":
                print("\nAu revoir !")
                self.db.close()
                break
            else:
                print("\n❌ Choix invalide. Veuillez réessayer.")
    
    def afficher_tableau_bord(self):
        """Affiche le tableau de bord."""
        TableauBord.afficher_tableau_bord(self.db)
        input("\nAppuyez sur Entrée pour continuer...")
    
    def menu_gestion_parc(self):
        """Menu de gestion du parc d'articles."""
        while True:
            print("\n" + "=" * 80)
            print("GESTION DU PARC")
            print("=" * 80)
            print("1. Lister tous les articles")
            print("2. Ajouter un article")
            print("3. Modifier un article")
            print("4. Supprimer un article")
            print("5. Retour au menu principal")
            
            choix = input("\nVotre choix : ").strip()
            
            if choix == "1":
                self.lister_articles()
            elif choix == "2":
                self.ajouter_article()
            elif choix == "3":
                self.modifier_article()
            elif choix == "4":
                self.supprimer_article()
            elif choix == "5":
                break
            else:
                print("❌ Choix invalide.")
    
    def lister_articles(self):
        """Liste tous les articles."""
        articles = ArticleRepository.get_all(self.db)
        
        if not articles:
            print("\nAucun article dans le parc.")
            return
        
        print("\n" + "-" * 80)
        print("LISTE DES ARTICLES")
        print("-" * 80)
        for art in articles:
            print(
                f"ID: {art.id} | {art.marque} {art.modele} | "
                f"Catégorie: {art.categorie} | "
                f"Statut: {art.statut.value} | "
                f"Prix/jour: {art.prix_journalier} €"
            )
        input("\nAppuyez sur Entrée pour continuer...")
    
    def ajouter_article(self):
        """Ajoute un nouvel article."""
        print("\n--- Ajout d'un nouvel article ---")
        
        try:
            categorie = input("Catégorie : ").strip()
            marque = input("Marque : ").strip()
            modele = input("Modèle : ").strip()
            numero_serie = input("Numéro de série : ").strip()
            date_achat_str = input("Date d'achat (YYYY-MM-DD) : ").strip()
            prix_journalier = float(input("Prix journalier (€) : ").strip())
            
            date_achat = date.fromisoformat(date_achat_str)
            
            article = Article(
                categorie=categorie,
                marque=marque,
                modele=modele,
                numero_serie=numero_serie,
                date_achat=date_achat,
                prix_journalier=prix_journalier,
                statut=StatutArticle.DISPONIBLE
            )
            
            article = ArticleRepository.create(self.db, article)
            print(f"\n✅ Article créé avec succès (ID: {article.id})")
            
        except ValueError as e:
            print(f"\n❌ Erreur de saisie : {e}")
        except Exception as e:
            print(f"\n❌ Erreur : {e}")
        
        input("\nAppuyez sur Entrée pour continuer...")
    
    def modifier_article(self):
        """Modifie un article existant."""
        article_id = int(input("\nID de l'article à modifier : ").strip())
        article = ArticleRepository.get_by_id(self.db, article_id)
        
        if not article:
            print(f"❌ Article {article_id} introuvable.")
            input("\nAppuyez sur Entrée pour continuer...")
            return
        
        print(f"\nArticle actuel : {article.marque} {article.modele} - Statut: {article.statut.value}")
        
        try:
            nouveau_statut_str = input("Nouveau statut (Disponible/Loué/En Maintenance/Rebut) : ").strip()
            nouveau_statut = StatutArticle(nouveau_statut_str)
            
            # Valider le changement de statut (BLL)
            est_valide, message = ServiceValidation.valider_changement_statut(
                self.db, article, nouveau_statut
            )
            
            if not est_valide:
                print(f"❌ {message}")
            else:
                article.statut = nouveau_statut
                ArticleRepository.update(self.db, article)
                print("✅ Article modifié avec succès.")
                
        except ValueError:
            print("❌ Statut invalide.")
        except Exception as e:
            print(f"❌ Erreur : {e}")
        
        input("\nAppuyez sur Entrée pour continuer...")
    
    def supprimer_article(self):
        """Supprime un article."""
        article_id = int(input("\nID de l'article à supprimer : ").strip())
        
        try:
            if ArticleRepository.delete(self.db, article_id):
                print("✅ Article supprimé avec succès.")
            else:
                print(f"❌ Article {article_id} introuvable ou impossible à supprimer "
                      f"(peut-être lié à un contrat).")
        except Exception as e:
            print(f"❌ Erreur : {e}")
        
        input("\nAppuyez sur Entrée pour continuer...")
    
    def menu_gestion_clients(self):
        """Menu de gestion des clients."""
        while True:
            print("\n" + "=" * 80)
            print("GESTION DES CLIENTS")
            print("=" * 80)
            print("1. Lister tous les clients")
            print("2. Ajouter un client")
            print("3. Retour au menu principal")
            
            choix = input("\nVotre choix : ").strip()
            
            if choix == "1":
                self.lister_clients()
            elif choix == "2":
                self.ajouter_client()
            elif choix == "3":
                break
            else:
                print("❌ Choix invalide.")
    
    def lister_clients(self):
        """Liste tous les clients."""
        clients = ClientRepository.get_all(self.db)
        
        if not clients:
            print("\nAucun client enregistré.")
            return
        
        print("\n" + "-" * 80)
        print("LISTE DES CLIENTS")
        print("-" * 80)
        for client in clients:
            vip_status = "⭐ VIP" if client.est_vip else ""
            print(
                f"ID: {client.id} | {client.prenom} {client.nom} | "
                f"Email: {client.email} {vip_status}"
            )
        input("\nAppuyez sur Entrée pour continuer...")
    
    def ajouter_client(self):
        """Ajoute un nouveau client."""
        print("\n--- Ajout d'un nouveau client ---")
        
        try:
            nom = input("Nom : ").strip()
            prenom = input("Prénom : ").strip()
            email = input("Email : ").strip()
            telephone = input("Téléphone (optionnel) : ").strip() or None
            adresse = input("Adresse (optionnel) : ").strip() or None
            est_vip_str = input("Client VIP ? (o/n) : ").strip().lower()
            est_vip = est_vip_str == 'o'
            
            client = Client(
                nom=nom,
                prenom=prenom,
                email=email,
                telephone=telephone,
                adresse=adresse,
                est_vip=est_vip
            )
            
            client = ClientRepository.create(self.db, client)
            print(f"\n✅ Client créé avec succès (ID: {client.id})")
            
        except Exception as e:
            print(f"\n❌ Erreur : {e}")
        
        input("\nAppuyez sur Entrée pour continuer...")
    
    def creer_location(self):
        """Crée une nouvelle location (transaction atomique)."""
        print("\n" + "=" * 80)
        print("CRÉATION D'UNE LOCATION")
        print("=" * 80)
        
        try:
            # 1. Sélectionner le client
            client_id = int(input("ID du client : ").strip())
            client = ClientRepository.get_by_id(self.db, client_id)
            
            if not client:
                print(f"❌ Client {client_id} introuvable.")
                input("\nAppuyez sur Entrée pour continuer...")
                return
            
            # 2. Afficher les articles disponibles
            articles_disponibles = ArticleRepository.get_disponibles(self.db)
            if not articles_disponibles:
                print("❌ Aucun article disponible pour la location.")
                input("\nAppuyez sur Entrée pour continuer...")
                return
            
            print("\nArticles disponibles :")
            for art in articles_disponibles:
                print(f"  ID: {art.id} - {art.marque} {art.modele} - {art.prix_journalier} €/jour")
            
            # 3. Sélectionner les articles (panier)
            article_ids_str = input("\nIDs des articles à louer (séparés par des virgules) : ").strip()
            article_ids = [int(id_str.strip()) for id_str in article_ids_str.split(',')]
            
            # 4. Saisir les dates
            date_debut_str = input("Date de début (YYYY-MM-DD) : ").strip()
            date_fin_str = input("Date de fin (YYYY-MM-DD) : ").strip()
            date_debut = date.fromisoformat(date_debut_str)
            date_fin = date.fromisoformat(date_fin_str)
            
            # 5. Calculer le prix (prévisualisation)
            articles = [ArticleRepository.get_by_id(self.db, aid) for aid in article_ids]
            calcul_prix = ServiceTarification.calculer_prix_final(
                articles, client, date_debut, date_fin, self.db
            )
            
            print("\n--- Détail du calcul ---")
            print(f"Prix de base : {calcul_prix['prix_base']:.2f} €")
            print(f"Remise durée (>7j) : -{calcul_prix['remise_duree']:.2f} €")
            print(f"Remise VIP : -{calcul_prix['remise_vip']:.2f} €")
            print(f"Surcharge retard : +{calcul_prix['surcharge_retard']:.2f} €")
            print(f"PRIX FINAL : {calcul_prix['prix_final']:.2f} €")
            
            # 6. Confirmer
            confirmer = input("\nConfirmer la location ? (o/n) : ").strip().lower()
            if confirmer != 'o':
                print("Location annulée.")
                input("\nAppuyez sur Entrée pour continuer...")
                return
            
            # 7. Valider transactionnellement
            succes, contrat, message = ServiceTransaction.valider_panier_transactionnel(
                self.db, client_id, article_ids, date_debut, date_fin
            )
            
            if succes:
                print(f"\n✅ {message}")
            else:
                print(f"\n❌ {message}")
            
        except ValueError as e:
            print(f"\n❌ Erreur de saisie : {e}")
        except Exception as e:
            print(f"\n❌ Erreur : {e}")
        
        input("\nAppuyez sur Entrée pour continuer...")
    
    def restituer_article(self):
        """Restitue un article."""
        print("\n" + "=" * 80)
        print("RESTITUTION D'ARTICLE")
        print("=" * 80)
        
        try:
            contrat_id = int(input("ID du contrat : ").strip())
            article_id = int(input("ID de l'article à restituer : ").strip())
            
            succes, message = ServiceTransaction.restituer_article(
                self.db, contrat_id, article_id
            )
            
            if succes:
                print(f"\n✅ {message}")
            else:
                print(f"\n❌ {message}")
                
        except ValueError:
            print("❌ Erreur de saisie.")
        except Exception as e:
            print(f"❌ Erreur : {e}")
        
        input("\nAppuyez sur Entrée pour continuer...")

