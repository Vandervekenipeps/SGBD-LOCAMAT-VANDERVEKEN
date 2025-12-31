"""
Couche d'accès aux données (DAL) - Repositories.

Ce module contient les opérations CRUD de base pour chaque entité.
Toutes les requêtes SQL sont centralisées ici, aucune requête ne doit
apparaître dans la couche UI ou BLL.

Principe : Cette couche ne contient QUE des opérations de base de données,
pas de logique métier.
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from datetime import date, timedelta
from typing import List, Optional, Tuple
from decimal import Decimal

from dal.models import Article, Client, Contrat, ArticleContrat, StatutArticle, StatutContrat


class ArticleRepository:
    """
    Repository pour la gestion des articles.
    
    Contient toutes les opérations CRUD sur la table articles.
    """
    
    @staticmethod
    def create(db: Session, article: Article) -> Article:
        """
        Crée un nouvel article dans la base de données.
        
        Args:
            db: Session de base de données
            article: Objet Article à créer
            
        Returns:
            Article créé avec son ID généré
        """
        db.add(article)
        db.commit()
        db.refresh(article)
        return article
    
    @staticmethod
    def get_by_id(db: Session, article_id: int) -> Optional[Article]:
        """Récupère un article par son ID."""
        return db.query(Article).filter(Article.id == article_id).first()
    
    @staticmethod
    def get_all(db: Session) -> List[Article]:
        """Récupère tous les articles."""
        return db.query(Article).all()
    
    @staticmethod
    def get_by_statut(db: Session, statut: StatutArticle) -> List[Article]:
        """Récupère tous les articles ayant un statut donné."""
        return db.query(Article).filter(Article.statut == statut).all()
    
    @staticmethod
    def get_disponibles(db: Session) -> List[Article]:
        """Récupère tous les articles disponibles pour la location."""
        return db.query(Article).filter(Article.statut == StatutArticle.DISPONIBLE).all()
    
    @staticmethod
    def update(db: Session, article: Article) -> Article:
        """Met à jour un article existant."""
        db.commit()
        db.refresh(article)
        return article
    
    @staticmethod
    def delete(db: Session, article_id: int) -> bool:
        """
        Supprime un article.
        
        ATTENTION : Cette opération échouera si l'article est lié à un contrat
        (contrainte RESTRICT sur la FK).
        
        Returns:
            True si la suppression a réussi, False sinon
        """
        article = ArticleRepository.get_by_id(db, article_id)
        if article:
            db.delete(article)
            db.commit()
            return True
        return False
    
    @staticmethod
    def verifier_disponibilite(db: Session, article_ids: List[int]) -> bool:
        """
        Vérifie que tous les articles de la liste sont disponibles.
        
        Utilisé pour valider un panier avant la création d'un contrat.
        
        Args:
            db: Session de base de données
            article_ids: Liste des IDs d'articles à vérifier
            
        Returns:
            True si tous les articles sont disponibles, False sinon
        """
        count = db.query(Article).filter(
            and_(
                Article.id.in_(article_ids),
                Article.statut == StatutArticle.DISPONIBLE
            )
        ).count()
        return count == len(article_ids)


class ClientRepository:
    """Repository pour la gestion des clients."""
    
    @staticmethod
    def create(db: Session, client: Client) -> Client:
        """Crée un nouveau client."""
        db.add(client)
        db.commit()
        db.refresh(client)
        return client
    
    @staticmethod
    def get_by_id(db: Session, client_id: int) -> Optional[Client]:
        """Récupère un client par son ID."""
        return db.query(Client).filter(Client.id == client_id).first()
    
    @staticmethod
    def get_all(db: Session) -> List[Client]:
        """Récupère tous les clients."""
        return db.query(Client).all()
    
    @staticmethod
    def get_by_email(db: Session, email: str) -> Optional[Client]:
        """Récupère un client par son email."""
        return db.query(Client).filter(Client.email == email).first()
    
    @staticmethod
    def delete(db: Session, client_id: int) -> Tuple[bool, str]:
        """
        Supprime un client.
        
        ATTENTION : Cette opération échouera si le client a des contrats
        (contrainte RESTRICT sur la FK dans la table contrats).
        
        Args:
            db: Session de base de données
            client_id: ID du client à supprimer
            
        Returns:
            Tuple (succes, message)
            - succes: True si la suppression a réussi, False sinon
            - message: Message d'erreur ou de succès
        """
        client = ClientRepository.get_by_id(db, client_id)
        if not client:
            return False, f"Client avec l'ID {client_id} introuvable."
        
        # Vérifier si le client a des contrats
        from dal.models import Contrat
        contrats_count = db.query(Contrat).filter(Contrat.client_id == client_id).count()
        if contrats_count > 0:
            return False, (
                f"Impossible de supprimer le client {client_id} ({client.prenom} {client.nom}). "
                f"Le client a {contrats_count} contrat(s) associé(s). "
                f"Veuillez d'abord supprimer ou terminer tous les contrats du client."
            )
        
        try:
            db.delete(client)
            db.commit()
            return True, f"Client {client_id} ({client.prenom} {client.nom}) supprimé avec succès."
        except Exception as e:
            db.rollback()
            return False, f"Erreur lors de la suppression : {str(e)}"
    
    @staticmethod
    def a_eu_retard(db: Session, client_id: int) -> bool:
        """
        Vérifie si le client a eu un retard lors de sa dernière location.
        
        Un retard est défini comme une date de retour réelle supérieure
        à la date de fin prévue du contrat.
        
        Args:
            db: Session de base de données
            client_id: ID du client à vérifier
            
        Returns:
            True si le client a eu un retard, False sinon
        """
        # Récupère le dernier contrat terminé du client
        dernier_contrat = db.query(Contrat).filter(
            and_(
                Contrat.client_id == client_id,
                Contrat.statut == StatutContrat.TERMINE,
                Contrat.date_retour_reelle.isnot(None)
            )
        ).order_by(desc(Contrat.date_retour_reelle)).first()
        
        if dernier_contrat and dernier_contrat.date_retour_reelle:
            # Vérifie si la date de retour réelle est après la date de fin prévue
            return dernier_contrat.date_retour_reelle > dernier_contrat.date_fin
        
        return False


class ContratRepository:
    """Repository pour la gestion des contrats."""
    
    @staticmethod
    def create(db: Session, contrat: Contrat) -> Contrat:
        """Crée un nouveau contrat."""
        db.add(contrat)
        db.commit()
        db.refresh(contrat)
        return contrat
    
    @staticmethod
    def get_by_id(db: Session, contrat_id: int) -> Optional[Contrat]:
        """Récupère un contrat par son ID."""
        return db.query(Contrat).filter(Contrat.id == contrat_id).first()
    
    @staticmethod
    def get_all(db: Session) -> List[Contrat]:
        """Récupère tous les contrats."""
        return db.query(Contrat).all()
    
    @staticmethod
    def get_en_cours(db: Session) -> List[Contrat]:
        """Récupère tous les contrats en cours (non terminés, non annulés)."""
        return db.query(Contrat).filter(
            Contrat.statut.in_([StatutContrat.EN_ATTENTE, StatutContrat.EN_COURS])
        ).all()
    
    @staticmethod
    def get_articles_du_contrat(db: Session, contrat_id: int) -> List[Article]:
        """
        Récupère tous les articles associés à un contrat.
        
        Args:
            db: Session de base de données
            contrat_id: ID du contrat
            
        Returns:
            Liste des articles du contrat
        """
        return db.query(Article).join(ArticleContrat).filter(
            ArticleContrat.contrat_id == contrat_id
        ).all()
    
    @staticmethod
    def ajouter_article(db: Session, contrat_id: int, article_id: int) -> ArticleContrat:
        """
        Ajoute un article à un contrat.
        
        Args:
            db: Session de base de données
            contrat_id: ID du contrat
            article_id: ID de l'article à ajouter
            
        Returns:
            L'objet ArticleContrat créé
        """
        article_contrat = ArticleContrat(
            contrat_id=contrat_id,
            article_id=article_id
        )
        db.add(article_contrat)
        db.commit()
        db.refresh(article_contrat)
        return article_contrat
    
    @staticmethod
    def get_retards(db: Session) -> List[Contrat]:
        """
        Récupère tous les contrats en retard (date de retour prévue dépassée).
        
        Utilisé pour le tableau de bord (liste d'alerte).
        
        Returns:
            Liste des contrats en retard
        """
        aujourdhui = date.today()
        return db.query(Contrat).filter(
            and_(
                Contrat.statut == StatutContrat.EN_COURS,
                Contrat.date_fin < aujourdhui,
                Contrat.date_retour_reelle.is_(None)
            )
        ).all()
    
    @staticmethod
    def get_ca_30_jours(db: Session) -> Decimal:
        """
        Calcule le chiffre d'affaires total des 30 derniers jours.
        
        Utilisé pour le tableau de bord.
        
        Returns:
            Montant total en euros
        """
        date_limite = date.today() - timedelta(days=30)
        result = db.query(func.sum(Contrat.prix_total)).filter(
            and_(
                Contrat.date_creation >= date_limite,
                Contrat.statut != StatutContrat.ANNULE
            )
        ).scalar()
        return Decimal(result) if result else Decimal('0.00')
    
    @staticmethod
    def get_top_5_rentables(db: Session) -> List[dict]:
        """
        Récupère le top 5 des matériels les plus rentables du mois.
        
        Un matériel est "rentable" s'il a généré le plus de revenus
        (somme des prix des contrats où il apparaît).
        
        Returns:
            Liste de dictionnaires avec les informations du matériel et le CA généré
        """
        date_debut_mois = date.today().replace(day=1)
        
        # Requête d'agrégation : somme des prix par article
        result = db.query(
            Article.id,
            Article.marque,
            Article.modele,
            Article.categorie,
            func.sum(Contrat.prix_total).label('ca_total')
        ).join(
            ArticleContrat, Article.id == ArticleContrat.article_id
        ).join(
            Contrat, ArticleContrat.contrat_id == Contrat.id
        ).filter(
            and_(
                Contrat.date_creation >= date_debut_mois,
                Contrat.statut != StatutContrat.ANNULE
            )
        ).group_by(
            Article.id, Article.marque, Article.modele, Article.categorie
        ).order_by(
            desc('ca_total')
        ).limit(5).all()
        
        # Convertir en liste de dictionnaires
        return [
            {
                'id': r.id,
                'marque': r.marque,
                'modele': r.modele,
                'categorie': r.categorie,
                'ca_total': float(r.ca_total) if r.ca_total else 0.0
            }
            for r in result
        ]



