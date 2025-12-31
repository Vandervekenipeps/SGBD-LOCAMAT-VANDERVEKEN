"""
Couche métier (BLL) - Validations métier.

Ce module contient toutes les validations métier qui ne peuvent pas
être gérées uniquement par le SGBD.
"""

import re
from datetime import date
from typing import List, Tuple, Optional
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
    
    @staticmethod
    def valider_date_achat(date_achat: date) -> Tuple[bool, str]:
        """
        Valide la date d'achat d'un article.
        
        Règle métier : La date d'achat ne peut pas être dans le futur.
        Cette validation est effectuée dans la couche BLL en plus de la contrainte
        SGBD pour garantir la cohérence et fournir un message d'erreur clair.
        
        Args:
            date_achat: Date d'achat à valider
            
        Returns:
            Tuple (est_valide, message_erreur)
            - est_valide: True si la date est valide
            - message_erreur: Message d'erreur si non valide, "" sinon
        """
        aujourdhui = date.today()
        
        if date_achat > aujourdhui:
            return False, (
                f"La date d'achat ({date_achat}) ne peut pas être dans le futur. "
                f"Date maximale autorisée : {aujourdhui}."
            )
        
        return True, ""
    
    @staticmethod
    def valider_telephone(telephone: Optional[str]) -> Tuple[bool, str]:
        """
        Valide le format d'un numéro de téléphone.
        
        Accepte les formats suivants :
        - Format belge : 012345678, 012/34.56.78, 012 34 56 78
        - Format international : +32 12 34 56 78, +3212345678
        - Format avec espaces/tirets : 012-34-56-78
        
        Règles :
        - Si None ou chaîne vide, retourne True (champ optionnel)
        - Doit contenir entre 8 et 15 chiffres (selon norme ITU-T E.164)
        - Peut contenir des caractères de formatage : espaces, tirets, points, slashes, parenthèses
        - Doit commencer par + (international) ou 0 (belge) ou un chiffre
        
        Args:
            telephone: Numéro de téléphone à valider (peut être None)
            
        Returns:
            Tuple (est_valide, message_erreur)
            - est_valide: True si le format est valide
            - message_erreur: Message d'erreur si non valide, "" sinon
        """
        # Si le téléphone est None ou vide, c'est valide (champ optionnel)
        if not telephone or not telephone.strip():
            return True, ""
        
        telephone = telephone.strip()
        
        # Extraire uniquement les chiffres pour compter
        chiffres = re.sub(r'\D', '', telephone)
        
        # Vérifier le nombre de chiffres (8 à 15 selon norme ITU-T E.164)
        if len(chiffres) < 8:
            return False, (
                f"Le numéro de téléphone doit contenir au moins 8 chiffres. "
                f"Vous avez saisi : '{telephone}' ({len(chiffres)} chiffres)"
            )
        
        if len(chiffres) > 15:
            return False, (
                f"Le numéro de téléphone ne peut pas contenir plus de 15 chiffres. "
                f"Vous avez saisi : '{telephone}' ({len(chiffres)} chiffres)"
            )
        
        # Vérifier que le numéro commence par un format valide
        # Formats acceptés : +32..., 0..., ou directement des chiffres
        if telephone.startswith('+'):
            # Format international : doit commencer par + suivi de chiffres
            if not re.match(r'^\+\d+$', telephone.replace(' ', '').replace('-', '')):
                return False, (
                    f"Format international invalide. "
                    f"Format attendu : +32 12 34 56 78 ou +3212345678. "
                    f"Vous avez saisi : '{telephone}'"
                )
        elif telephone.startswith('0'):
            # Format belge : doit commencer par 0 suivi de 8 ou 9 chiffres
            if len(chiffres) < 9 or len(chiffres) > 10:
                return False, (
                    f"Format belge invalide. "
                    f"Un numéro belge doit contenir 9 ou 10 chiffres (0 + 8 ou 9 chiffres). "
                    f"Vous avez saisi : '{telephone}' ({len(chiffres)} chiffres)"
                )
        else:
            # Format sans préfixe : doit contenir uniquement des chiffres
            if not chiffres.isdigit():
                return False, (
                    f"Format invalide. "
                    f"Si le numéro ne commence pas par + ou 0, il doit contenir uniquement des chiffres. "
                    f"Vous avez saisi : '{telephone}'"
                )
        
        # Vérifier qu'il n'y a pas de caractères invalides
        # Autoriser : chiffres, espaces, tirets, points, slashes, parenthèses, +
        if not re.match(r'^[\d\s\-\./\(\)\+]+$', telephone):
            return False, (
                f"Le numéro de téléphone contient des caractères invalides. "
                f"Caractères autorisés : chiffres, espaces, tirets (-), points (.), slashes (/), parenthèses, +. "
                f"Vous avez saisi : '{telephone}'"
            )
        
        return True, ""



