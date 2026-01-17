"""
Interface utilisateur - Menu principal de l'application.

Ce module gère l'interface en ligne de commande pour l'application LOCA-MAT.
Toutes les interactions utilisateur sont gérées ici, mais aucune requête SQL
n'apparaît dans ce code (toutes les opérations passent par la couche BLL).
"""

from sqlalchemy.orm import Session
from datetime import date, timedelta
from typing import List, Optional

from config.database import get_db, SessionLocal
from dal.models import Article, Client, StatutArticle, StatutContrat
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
    
    def _input_int(self, prompt: str, default: Optional[int] = None, allow_empty: bool = False) -> Optional[int]:
        """
        Demande un entier à l'utilisateur avec gestion des erreurs.
        
        Args:
            prompt: Message à afficher
            default: Valeur par défaut si l'utilisateur appuie sur Entrée
            allow_empty: Si True, retourne None si l'utilisateur appuie sur Entrée sans valeur
            
        Returns:
            L'entier saisi, la valeur par défaut, ou None si allow_empty=True et valeur vide
        """
        while True:
            try:
                valeur = input(prompt).strip()
                if not valeur:
                    if default is not None:
                        return default
                    if allow_empty:
                        return None
                    print("❌ Ce champ est obligatoire. Veuillez saisir un nombre.")
                    continue
                return int(valeur)
            except ValueError:
                print("❌ Erreur : veuillez saisir un nombre entier valide.")
    
    def _input_float(self, prompt: str, default: Optional[float] = None) -> float:
        """
        Demande un nombre décimal à l'utilisateur avec gestion des erreurs.
        
        Args:
            prompt: Message à afficher
            default: Valeur par défaut si l'utilisateur appuie sur Entrée
            
        Returns:
            Le nombre saisi ou la valeur par défaut
        """
        while True:
            try:
                valeur = input(prompt).strip()
                if not valeur and default is not None:
                    return default
                if not valeur:
                    print("Veuillez saisir un nombre.")
                    continue
                return float(valeur)
            except ValueError:
                print("Erreur : veuillez saisir un nombre valide.")
    
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
            # Saisie des champs obligatoires avec validation
            categorie = input("Catégorie : ").strip()
            if not categorie:
                print("❌ La catégorie est obligatoire.")
                input("\nAppuyez sur Entrée pour continuer...")
                return
            
            marque = input("Marque : ").strip()
            if not marque:
                print("❌ La marque est obligatoire.")
                input("\nAppuyez sur Entrée pour continuer...")
                return
            
            modele = input("Modèle : ").strip()
            if not modele:
                print("❌ Le modèle est obligatoire.")
                input("\nAppuyez sur Entrée pour continuer...")
                return
            
            numero_serie = input("Numéro de série : ").strip()
            if not numero_serie:
                print("❌ Le numéro de série est obligatoire.")
                input("\nAppuyez sur Entrée pour continuer...")
                return
            
            # Saisie de la date avec validation
            date_achat_str = input("Date d'achat (YYYY-MM-DD) : ").strip()
            if not date_achat_str:
                print("❌ La date d'achat est obligatoire. Format attendu : YYYY-MM-DD (ex: 2024-01-15)")
                input("\nAppuyez sur Entrée pour continuer...")
                return
            
            try:
                date_achat = date.fromisoformat(date_achat_str)
            except ValueError:
                print(f"❌ Format de date invalide. Format attendu : YYYY-MM-DD (ex: 2024-01-15)")
                print(f"   Vous avez saisi : '{date_achat_str}'")
                input("\nAppuyez sur Entrée pour continuer...")
                return
            
            prix_journalier = self._input_float("Prix journalier (€) : ")
            if prix_journalier <= 0:
                print("❌ Le prix journalier doit être supérieur à 0.")
                input("\nAppuyez sur Entrée pour continuer...")
                return
            
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
        """Modifie un article existant (statut uniquement)."""
        article_id = self._input_int("\nID de l'article à modifier : ", allow_empty=True)
        
        if article_id is None:
            print("❌ L'ID de l'article est obligatoire.")
            input("\nAppuyez sur Entrée pour continuer...")
            return
        
        article = ArticleRepository.get_by_id(self.db, article_id)
        
        if not article:
            print(f"❌ Article {article_id} introuvable.")
            input("\nAppuyez sur Entrée pour continuer...")
            return
        
        print(f"\nArticle actuel : {article.marque} {article.modele} - Statut: {article.statut.value}")
        
        try:
            nouveau_statut_str = input("Nouveau statut (Disponible/Loué/En Maintenance/Rebut) : ").strip()
            
            # Vérifier que le statut n'est pas vide
            if not nouveau_statut_str:
                print("❌ Le statut est obligatoire. Veuillez saisir un statut valide.")
                print("   Statuts possibles : Disponible, Loué, En Maintenance, Rebut")
                input("\nAppuyez sur Entrée pour continuer...")
                return
            
            # Essayer de convertir en enum
            try:
                nouveau_statut = StatutArticle(nouveau_statut_str)
            except ValueError:
                print(f"❌ Statut invalide : '{nouveau_statut_str}'")
                print("   Statuts possibles : Disponible, Loué, En Maintenance, Rebut")
                input("\nAppuyez sur Entrée pour continuer...")
                return
            
            # Valider le changement de statut (BLL)
            est_valide, message = ServiceValidation.valider_changement_statut(
                self.db, article, nouveau_statut
            )
            
            if not est_valide:
                print(f"❌ {message}")
            else:
                # Assignation du statut (SQLAlchemy gère la conversion enum)
                article.statut = nouveau_statut  # type: ignore[assignment]
                ArticleRepository.update(self.db, article)
                print("✅ Article modifié avec succès.")
                
        except Exception as e:
            print(f"❌ Erreur : {e}")
        
        input("\nAppuyez sur Entrée pour continuer...")
    
    def supprimer_article(self):
        """Supprime un article."""
        article_id = self._input_int("\nID de l'article à supprimer : ", allow_empty=True)
        
        if article_id is None:
            print("❌ L'ID de l'article est obligatoire.")
            input("\nAppuyez sur Entrée pour continuer...")
            return
        
        try:
            succes, message = ArticleRepository.delete(self.db, article_id)
            if succes:
                print(f"✅ {message}")
            else:
                print(f"❌ {message}")
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
            print("3. Modifier un client")
            print("4. Supprimer un client")
            print("5. Retour au menu principal")
            
            choix = input("\nVotre choix : ").strip()
            
            if choix == "1":
                self.lister_clients()
            elif choix == "2":
                self.ajouter_client()
            elif choix == "3":
                self.modifier_client()
            elif choix == "4":
                self.supprimer_client()
            elif choix == "5":
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
            vip_status = "⭐ VIP" if bool(client.est_vip) else ""
            print(
                f"ID: {client.id} | {client.prenom} {client.nom} | "
                f"Email: {client.email} {vip_status}"
            )
        input("\nAppuyez sur Entrée pour continuer...")
    
    def ajouter_client(self):
        """Ajoute un nouveau client."""
        print("\n--- Ajout d'un nouveau client ---")
        
        try:
            # Saisie des champs obligatoires avec validation
            nom = input("Nom : ").strip()
            if not nom:
                print("❌ Le nom est obligatoire.")
                input("\nAppuyez sur Entrée pour continuer...")
                return
            
            prenom = input("Prénom : ").strip()
            if not prenom:
                print("❌ Le prénom est obligatoire.")
                input("\nAppuyez sur Entrée pour continuer...")
                return
            
            email = input("Email : ").strip()
            if not email:
                print("❌ L'email est obligatoire.")
                input("\nAppuyez sur Entrée pour continuer...")
                return
            
            # Validation basique de l'email
            if '@' not in email or '.' not in email.split('@')[-1]:
                print("❌ Format d'email invalide. Format attendu : exemple@domaine.com")
                input("\nAppuyez sur Entrée pour continuer...")
                return
            
            telephone = input("Téléphone (optionnel) : ").strip() or None
            
            # Validation du téléphone (BLL)
            if telephone:
                telephone_valide, msg_telephone = ServiceValidation.valider_telephone(telephone)
                if not telephone_valide:
                    print(f"❌ {msg_telephone}")
                    input("\nAppuyez sur Entrée pour continuer...")
                    return
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
    
    def modifier_client(self):
        """Modifie un client existant."""
        print("\n" + "=" * 80)
        print("MODIFICATION D'UN CLIENT")
        print("=" * 80)
        
        # Afficher la liste des clients pour faciliter la sélection
        clients = ClientRepository.get_all(self.db)
        if not clients:
            print("\n❌ Aucun client enregistré.")
            input("\nAppuyez sur Entrée pour continuer...")
            return
        
        print("\nListe des clients :")
        print("-" * 80)
        for client in clients:
            vip_status = "⭐ VIP" if bool(client.est_vip) else ""
            telephone = f" | Tél: {client.telephone}" if client.telephone is not None and str(client.telephone).strip() else ""
            print(
                f"ID: {client.id} | {client.prenom} {client.nom} | "
                f"Email: {client.email}{telephone} {vip_status}"
            )
        print("-" * 80)
        
        try:
            client_id = self._input_int("\nID du client à modifier : ", allow_empty=True)
            
            if client_id is None:
                print("❌ L'ID du client est obligatoire.")
                input("\nAppuyez sur Entrée pour continuer...")
                return
            
            client = ClientRepository.get_by_id(self.db, client_id)
            if not client:
                print(f"❌ Client avec l'ID {client_id} introuvable.")
                input("\nAppuyez sur Entrée pour continuer...")
                return
            
            print(f"\nClient actuel : {client.prenom} {client.nom} ({client.email})")
            print("\nLaissez vide pour conserver la valeur actuelle.")
            
            # Modification du nom
            nouveau_nom = input(f"Nom [{client.nom}] : ").strip()  # type: ignore[arg-type]
            if nouveau_nom:
                client.nom = nouveau_nom  # type: ignore[assignment]
            
            # Modification du prénom
            nouveau_prenom = input(f"Prénom [{client.prenom}] : ").strip()  # type: ignore[arg-type]
            if nouveau_prenom:
                client.prenom = nouveau_prenom  # type: ignore[assignment]
            
            # Modification de l'email
            nouvel_email = input(f"Email [{client.email}] : ").strip()  # type: ignore[arg-type]
            if nouvel_email:
                # Vérifier si l'email est déjà utilisé par un autre client
                client_existant = ClientRepository.get_by_email(self.db, nouvel_email)
                if client_existant and client_existant.id != client.id:  # type: ignore[comparison-overlap]
                    print(f"❌ L'email '{nouvel_email}' est déjà utilisé par un autre client.")
                    input("\nAppuyez sur Entrée pour continuer...")
                    return
                client.email = nouvel_email  # type: ignore[assignment]
            
            # Modification du téléphone
            telephone_actuel = client.telephone if client.telephone is not None else '(vide)'  # type: ignore[comparison-overlap]
            nouveau_telephone = input(f"Téléphone [{telephone_actuel}] : ").strip()
            if nouveau_telephone:
                # Validation du téléphone (BLL)
                telephone_valide, msg_telephone = ServiceValidation.valider_telephone(nouveau_telephone)
                if not telephone_valide:
                    print(f"❌ {msg_telephone}")
                    input("\nAppuyez sur Entrée pour continuer...")
                    return
                client.telephone = nouveau_telephone  # type: ignore[assignment]
            elif nouveau_telephone == "" and client.telephone is not None:  # type: ignore[comparison-overlap]
                # Si l'utilisateur entre une chaîne vide, on garde None
                client.telephone = None  # type: ignore[assignment]
            
            # Modification de l'adresse
            adresse_actuelle = client.adresse if client.adresse is not None else '(vide)'  # type: ignore[comparison-overlap]
            nouvelle_adresse = input(f"Adresse [{adresse_actuelle}] : ").strip()
            if nouvelle_adresse:
                client.adresse = nouvelle_adresse  # type: ignore[assignment]
            elif nouvelle_adresse == "" and client.adresse is not None:  # type: ignore[comparison-overlap]
                # Si l'utilisateur entre une chaîne vide, on garde None
                client.adresse = None  # type: ignore[assignment]
            
            # Modification du statut VIP
            vip_actuel = "Oui" if bool(client.est_vip) else "Non"  # type: ignore[arg-type]
            nouveau_vip = input(f"Client VIP (o/n) [{vip_actuel}] : ").strip().lower()
            if nouveau_vip == 'o':
                client.est_vip = True  # type: ignore[assignment]
            elif nouveau_vip == 'n':
                client.est_vip = False  # type: ignore[assignment]
            # Si vide, on garde la valeur actuelle
            
            # Mettre à jour le client
            ClientRepository.update(self.db, client)
            print(f"\n✅ Client {client_id} modifié avec succès.")
            
        except Exception as e:
            print(f"\n❌ Erreur : {e}")
        
        input("\nAppuyez sur Entrée pour continuer...")
    
    def supprimer_client(self):
        """Supprime un client."""
        print("\n" + "=" * 80)
        print("SUPPRESSION D'UN CLIENT")
        print("=" * 80)
        
        # Afficher la liste des clients pour faciliter la sélection
        clients = ClientRepository.get_all(self.db)
        if not clients:
            print("\n❌ Aucun client enregistré.")
            input("\nAppuyez sur Entrée pour continuer...")
            return
        
        print("\nListe des clients :")
        print("-" * 80)
        for client in clients:
            vip_status = "⭐ VIP" if bool(client.est_vip) else ""
            telephone = f" | Tél: {client.telephone}" if client.telephone is not None and str(client.telephone).strip() else ""
            print(
                f"ID: {client.id} | {client.prenom} {client.nom} | "
                f"Email: {client.email}{telephone} {vip_status}"
            )
        print("-" * 80)
        
        try:
            client_id = self._input_int("\nID du client à supprimer : ", allow_empty=True)
            
            if client_id is None:
                print("❌ L'ID du client est obligatoire.")
                input("\nAppuyez sur Entrée pour continuer...")
                return
            
            # Demander confirmation
            client = ClientRepository.get_by_id(self.db, client_id)
            if not client:
                print(f"❌ Client avec l'ID {client_id} introuvable.")
                input("\nAppuyez sur Entrée pour continuer...")
                return
            
            print(f"\n⚠️  ATTENTION : Vous êtes sur le point de supprimer :")
            print(f"   Client ID {client.id} : {client.prenom} {client.nom} ({client.email})")
            confirmation = input("\nÊtes-vous sûr de vouloir supprimer ce client ? (o/n) : ").strip().lower()
            
            if confirmation != 'o':
                print("❌ Suppression annulée.")
                input("\nAppuyez sur Entrée pour continuer...")
                return
            
            # Supprimer le client
            succes, message = ClientRepository.delete(self.db, client_id)
            
            if succes:
                print(f"\n✅ {message}")
            else:
                print(f"\n❌ {message}")
            
        except Exception as e:
            print(f"\n❌ Erreur : {e}")
        
        input("\nAppuyez sur Entrée pour continuer...")
    
    def creer_location(self):
        """Crée une nouvelle location (transaction atomique)."""
        print("\n" + "=" * 80)
        print("CRÉATION D'UNE LOCATION")
        print("=" * 80)
        
        try:
            # 1. Afficher le récapitulatif des clients
            clients = ClientRepository.get_all(self.db)
            if not clients:
                print("\n❌ Aucun client enregistré. Veuillez d'abord créer un client.")
                input("\nAppuyez sur Entrée pour continuer...")
                return
            
            print("\n--- RÉCAPITULATIF DES CLIENTS ---")
            print("-" * 80)
            for client in clients:
                vip_status = "⭐ VIP" if bool(client.est_vip) else ""
                print(f"  ID: {client.id} - {client.prenom} {client.nom} - Email: {client.email} {vip_status}")
            
            # 2. Sélectionner le client
            print("\n" + "-" * 80)
            client_id = self._input_int("ID du client : ", allow_empty=True)
            if client_id is None:
                print("❌ L'ID du client est obligatoire.")
                input("\nAppuyez sur Entrée pour continuer...")
                return
            client = ClientRepository.get_by_id(self.db, client_id)
            
            if not client:
                print(f"❌ Client {client_id} introuvable.")
                input("\nAppuyez sur Entrée pour continuer...")
                return
            
            # 3. Afficher le récapitulatif des articles disponibles
            articles_disponibles = ArticleRepository.get_disponibles(self.db)
            if not articles_disponibles:
                print("\n❌ Aucun article disponible pour la location.")
                input("\nAppuyez sur Entrée pour continuer...")
                return
            
            print("\n--- RÉCAPITULATIF DES ARTICLES DISPONIBLES ---")
            print("-" * 80)
            for art in articles_disponibles:
                print(f"  ID: {art.id} - {art.marque} {art.modele} ({art.categorie}) - {art.prix_journalier} €/jour")
            
            # 4. Sélectionner les articles (panier)
            print("\n" + "-" * 80)
            article_ids_str = input("IDs des articles à louer (séparés par des virgules) : ").strip()
            if not article_ids_str:
                print("Aucun article sélectionné.")
                input("\nAppuyez sur Entrée pour continuer...")
                return
            try:
                article_ids = [int(id_str.strip()) for id_str in article_ids_str.split(',') if id_str.strip()]
                if not article_ids:
                    print("Aucun ID valide saisi.")
                    input("\nAppuyez sur Entrée pour continuer...")
                    return
            except ValueError:
                print("Erreur : veuillez saisir des nombres séparés par des virgules.")
                input("\nAppuyez sur Entrée pour continuer...")
                return
            
            # 5. Saisir les dates avec validation
            date_debut_str = input("Date de début (YYYY-MM-DD) : ").strip()
            if not date_debut_str:
                print("❌ La date de début est obligatoire. Format attendu : YYYY-MM-DD (ex: 2024-01-15)")
                input("\nAppuyez sur Entrée pour continuer...")
                return
            
            try:
                date_debut = date.fromisoformat(date_debut_str)
            except ValueError:
                print(f"❌ Format de date invalide pour la date de début. Format attendu : YYYY-MM-DD")
                print(f"   Vous avez saisi : '{date_debut_str}'")
                input("\nAppuyez sur Entrée pour continuer...")
                return
            
            date_fin_str = input("Date de fin (YYYY-MM-DD) : ").strip()
            if not date_fin_str:
                print("❌ La date de fin est obligatoire. Format attendu : YYYY-MM-DD (ex: 2024-01-20)")
                input("\nAppuyez sur Entrée pour continuer...")
                return
            
            try:
                date_fin = date.fromisoformat(date_fin_str)
            except ValueError:
                print(f"❌ Format de date invalide pour la date de fin. Format attendu : YYYY-MM-DD")
                print(f"   Vous avez saisi : '{date_fin_str}'")
                input("\nAppuyez sur Entrée pour continuer...")
                return
            
            # 6. Calculer le prix (prévisualisation)
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
            
            # 7. Confirmer
            confirmer = input("\nConfirmer la location ? (o/n) : ").strip().lower()
            if confirmer != 'o':
                print("Location annulée.")
                input("\nAppuyez sur Entrée pour continuer...")
                return
            
            # 8. Valider transactionnellement
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
            # 1. Afficher les contrats en cours
            contrats_en_cours = ContratRepository.get_en_cours(self.db)
            
            if not contrats_en_cours:
                print("\n❌ Aucun contrat en cours. Aucun article à restituer.")
                input("\nAppuyez sur Entrée pour continuer...")
                return
            
            print("\n--- CONTRATS EN COURS ---")
            print("-" * 80)
            for contrat in contrats_en_cours:
                # SQLAlchemy retourne déjà des entiers, pas des colonnes
                client = ClientRepository.get_by_id(self.db, contrat.client_id)  # type: ignore[arg-type]
                client_nom = f"{client.prenom} {client.nom}" if client else f"Client ID:{contrat.client_id}"
                articles = ContratRepository.get_articles_du_contrat(self.db, contrat.id)  # type: ignore[arg-type]
                articles_str = ", ".join([f"{a.marque} {a.modele} (ID:{a.id})" for a in articles])
                
                print(f"\nContrat ID: {contrat.id}")
                print(f"  Client: {client_nom}")
                print(f"  Dates: {contrat.date_debut} → {contrat.date_fin}")
                print(f"  Statut: {contrat.statut.value}")
                print(f"  Articles: {articles_str}")
            
            # 2. Demander l'ID du contrat
            print("\n" + "-" * 80)
            contrat_id = self._input_int("\nID du contrat : ", allow_empty=True)
            if contrat_id is None:
                print("❌ L'ID du contrat est obligatoire.")
                input("\nAppuyez sur Entrée pour continuer...")
                return
            
            # Vérifier que le contrat existe et est en cours
            contrat = ContratRepository.get_by_id(self.db, contrat_id)
            if not contrat:
                print(f"❌ Contrat {contrat_id} introuvable.")
                input("\nAppuyez sur Entrée pour continuer...")
                return
            
            if contrat.statut not in [StatutContrat.EN_ATTENTE, StatutContrat.EN_COURS]:
                print(f"❌ Le contrat {contrat_id} n'est pas en cours (statut: {contrat.statut.value}).")
                input("\nAppuyez sur Entrée pour continuer...")
                return
            
            # 3. Afficher les articles du contrat
            articles = ContratRepository.get_articles_du_contrat(self.db, contrat_id)
            if not articles:
                print(f"❌ Aucun article trouvé pour le contrat {contrat_id}.")
                input("\nAppuyez sur Entrée pour continuer...")
                return
            
            print("\n--- ARTICLES DU CONTRAT ---")
            print("-" * 80)
            for article in articles:
                print(f"  ID: {article.id} - {article.marque} {article.modele} - Statut: {article.statut.value}")
            
            # 4. Demander l'ID de l'article à restituer
            print("\n" + "-" * 80)
            article_id = self._input_int("ID de l'article à restituer : ", allow_empty=True)
            if article_id is None:
                print("❌ L'ID de l'article est obligatoire.")
                input("\nAppuyez sur Entrée pour continuer...")
                return
            
            # Vérifier que l'article appartient au contrat
            article_ids_contrat = [a.id for a in articles]
            if article_id not in article_ids_contrat:
                print(f"❌ L'article {article_id} n'appartient pas au contrat {contrat_id}.")
                input("\nAppuyez sur Entrée pour continuer...")
                return
            
            # 5. Restituer l'article
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

