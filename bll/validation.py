"""
Couche métier (BLL) - Validations métier.

Ce module contient toutes les validations métier qui ne peuvent pas
être gérées uniquement par le SGBD.
"""

from datetime import date
from typing import List, Tuple
from sqlalchemy.orm import Session

from dal.models import Article, StatutArticle
from dal.repositories import ArticleRepository


class ServiceValidation:
    """
    Service de validation métier.
    
    Contient toutes les règles de validation qui nécessitent de la logique applicative.
    """
    
    @staticmethod
    def valider_changement_statut(
        db: Session,
        article: Article,
        nouveau_statut: StatutArticle
    ) -> Tuple[bool, str]:
        """
        Valide le changement de statut d'un article.
        
        Règle métier : Un article ne peut passer au statut "Loué" que s'il est
        actuellement "Disponible".
        
        Cette validation est effectuée dans la couche BLL en plus des contraintes
        SGBD pour garantir la cohérence.
        
        Args:
            db: Session de base de données
            article: Article dont on veut changer le statut
            nouveau_statut: Nouveau statut souhaité
            
        Returns:
            Tuple (est_valide, message_erreur)
            - est_valide: True si le changement est autorisé
            - message_erreur: Message d'erreur si non valide, "" sinon
        """
        # Règle : Un article ne peut passer à "Loué" que s'il est "Disponible"
        if nouveau_statut == StatutArticle.LOUE:
            if article.statut != StatutArticle.DISPONIBLE:
                return False, (
                    f"Impossible de louer l'article {article.id}. "
                    f"L'article est actuellement '{article.statut.value}', "
                    f"il doit être 'Disponible' pour être loué."
                )
        
        return True, ""
    
    @staticmethod
    def valider_panier(
        db: Session,
        article_ids: List[int]
    ) -> Tuple[bool, str, List[int]]:
        """
        Valide un panier de location.
        
        Vérifie que tous les articles du panier sont disponibles.
        
        Args:
            db: Session de base de données
            article_ids: Liste des IDs d'articles dans le panier
            
        Returns:
            Tuple (est_valide, message_erreur, articles_indisponibles)
            - est_valide: True si tous les articles sont disponibles
            - message_erreur: Message d'erreur si non valide
            - articles_indisponibles: Liste des IDs d'articles non disponibles
        """
        if not article_ids:
            return False, "Le panier est vide.", []
        
        # Vérifier la disponibilité de tous les articles
        articles_disponibles = ArticleRepository.verifier_disponibilite(db, article_ids)
        
        if not articles_disponibles:
            # Récupérer les articles non disponibles pour le message d'erreur
            articles = db.query(Article).filter(Article.id.in_(article_ids)).all()
            articles_indisponibles = [
                art.id for art in articles 
                if art.statut != StatutArticle.DISPONIBLE
            ]
            
            message = (
                f"Certains articles ne sont pas disponibles : {articles_indisponibles}. "
                f"Veuillez retirer ces articles du panier."
            )
            return False, message, articles_indisponibles
        
        return True, "", []
    
    @staticmethod
    def valider_dates_location(date_debut: date, date_fin: date) -> Tuple[bool, str]:
        """
        Valide les dates d'une location.
        
        Args:
            date_debut: Date de début
            date_fin: Date de fin
            
        Returns:
            Tuple (est_valide, message_erreur)
        """
        if date_debut > date_fin:
            return False, "La date de début doit être antérieure à la date de fin."
        
        if date_debut < date.today():
            return False, "La date de début ne peut pas être dans le passé."
        
        return True, ""


