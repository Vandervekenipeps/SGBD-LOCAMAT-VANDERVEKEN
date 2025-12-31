"""
Couche métier (BLL) - Gestion des transactions ACID.

Ce module gère la validation transactionnelle atomique des paniers de location.
Si un seul article du panier n'est plus disponible au moment de la validation,
l'ensemble de la transaction doit être annulée (rollback).

Gestion de la concurrence : Le système doit gérer le cas où deux gestionnaires
tentent de louer le même dernier article simultanément.
"""

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, OperationalError
from datetime import date
from typing import List, Tuple, Optional
from decimal import Decimal

from dal.models import Article, Client, Contrat, ArticleContrat, StatutArticle, StatutContrat
from dal.repositories import ArticleRepository, ContratRepository, ClientRepository
from bll.tarification import ServiceTarification
from bll.validation import ServiceValidation


class ServiceTransaction:
    """
    Service de gestion des transactions de location.
    
    Implémente la validation atomique des paniers avec gestion de la concurrence.
    """
    
    @staticmethod
    def valider_panier_transactionnel(
        db: Session,
        client_id: int,
        article_ids: List[int],
        date_debut: date,
        date_fin: date
    ) -> Tuple[bool, Optional[Contrat], str]:
        """
        Valide un panier de location de manière transactionnelle (ACID).
        
        Cette méthode garantit que :
        1. Tous les articles sont disponibles au moment de la validation
        2. Si un seul article n'est plus disponible, toute la transaction est annulée
        3. Les statuts des articles sont mis à jour atomiquement
        4. Le contrat est créé uniquement si tout est valide
        
        Gestion de la concurrence :
        - Utilise des verrous de ligne (SELECT FOR UPDATE) pour éviter les conflits
        - Si deux transactions tentent de louer le même article, seule la première réussit
        - La seconde reçoit un message d'erreur explicite
        
        Args:
            db: Session de base de données
            client_id: ID du client
            article_ids: Liste des IDs d'articles à louer
            date_debut: Date de début de location
            date_fin: Date de fin de location
            
        Returns:
            Tuple (succes, contrat, message)
            - succes: True si la transaction a réussi
            - contrat: Contrat créé si succès, None sinon
            - message: Message de succès ou d'erreur
        """
        try:
            # Début de la transaction (déjà dans une transaction par défaut avec SQLAlchemy)
            
            # 1. Vérifier que le client existe
            client = ClientRepository.get_by_id(db, client_id)
            if not client:
                db.rollback()
                return False, None, f"Client avec l'ID {client_id} introuvable."
            
            # 2. Valider les dates
            dates_valides, msg_dates = ServiceValidation.valider_dates_location(date_debut, date_fin)
            if not dates_valides:
                db.rollback()
                return False, None, msg_dates
            
            # 3. Vérifier la disponibilité AVANT de verrouiller (optimisation)
            panier_valide, msg_panier, articles_indisponibles = ServiceValidation.valider_panier(
                db, article_ids
            )
            if not panier_valide:
                db.rollback()
                return False, None, msg_panier
            
            # 4. Verrouiller les articles avec SELECT FOR UPDATE (gestion de la concurrence)
            # Cela empêche une autre transaction de modifier ces articles simultanément
            articles = db.query(Article).filter(
                Article.id.in_(article_ids)
            ).with_for_update().all()
            
            # 5. Re-vérifier la disponibilité APRÈS le verrouillage (cas de concurrence)
            articles_disponibles = [
                art for art in articles 
                if art.statut == StatutArticle.DISPONIBLE
            ]
            
            if len(articles_disponibles) != len(article_ids):
                # Un article n'est plus disponible (conflit de concurrence)
                articles_indisponibles = [
                    art.id for art in articles 
                    if art.statut != StatutArticle.DISPONIBLE
                ]
                db.rollback()
                return False, None, (
                    f"Conflit de concurrence détecté. "
                    f"Les articles suivants ne sont plus disponibles : {articles_indisponibles}. "
                    f"Un autre gestionnaire vient de les louer."
                )
            
            # 6. Calculer le prix final
            calcul_prix = ServiceTarification.calculer_prix_final(
                articles, client, date_debut, date_fin, db
            )
            
            # 7. Créer le contrat
            contrat = Contrat(
                client_id=client_id,
                date_debut=date_debut,
                date_fin=date_fin,
                prix_total=calcul_prix['prix_final'],
                statut=StatutContrat.EN_COURS
            )
            db.add(contrat)
            db.flush()  # Pour obtenir l'ID du contrat
            
            # 8. Lier les articles au contrat ET changer leur statut
            for article in articles:
                # Créer la liaison article-contrat
                article_contrat = ArticleContrat(
                    contrat_id=contrat.id,
                    article_id=article.id
                )
                db.add(article_contrat)
                
                # Changer le statut de l'article à "Loué"
                article.statut = StatutArticle.LOUE
            
            # 9. Commit de la transaction (tout ou rien)
            db.commit()
            
            return True, contrat, (
                f"Contrat créé avec succès. "
                f"Prix total : {calcul_prix['prix_final']:.2f} €. "
                f"Remise durée : {calcul_prix['remise_duree']:.2f} €. "
                f"Remise VIP : {calcul_prix['remise_vip']:.2f} €. "
                f"Surcharge retard : {calcul_prix['surcharge_retard']:.2f} €."
            )
            
        except IntegrityError as e:
            # Erreur d'intégrité (contrainte violée)
            db.rollback()
            return False, None, (
                f"Erreur d'intégrité : Impossible de créer le contrat. "
                f"Détails : {str(e)}"
            )
        
        except OperationalError as e:
            # Erreur opérationnelle (connexion, timeout, etc.)
            db.rollback()
            return False, None, (
                f"Erreur de connexion à la base de données. "
                f"Veuillez réessayer. Détails : {str(e)}"
            )
        
        except Exception as e:
            # Toute autre erreur inattendue
            db.rollback()
            return False, None, (
                f"Erreur inattendue lors de la création du contrat : {str(e)}"
            )
    
    @staticmethod
    def restituer_article(
        db: Session,
        contrat_id: int,
        article_id: int
    ) -> Tuple[bool, str]:
        """
        Restitue un article (met fin à sa location).
        
        Change le statut de l'article de "Loué" à "Disponible".
        
        Args:
            db: Session de base de données
            contrat_id: ID du contrat
            article_id: ID de l'article à restituer
            
        Returns:
            Tuple (succes, message)
        """
        try:
            # Récupérer le contrat
            contrat = ContratRepository.get_by_id(db, contrat_id)
            if not contrat:
                return False, f"Contrat {contrat_id} introuvable."
            
            # Récupérer l'article
            article = ArticleRepository.get_by_id(db, article_id)
            if not article:
                return False, f"Article {article_id} introuvable."
            
            # Vérifier que l'article est bien dans ce contrat
            article_contrat = db.query(ArticleContrat).filter(
                ArticleContrat.contrat_id == contrat_id,
                ArticleContrat.article_id == article_id
            ).first()
            
            if not article_contrat:
                return False, f"L'article {article_id} n'est pas dans le contrat {contrat_id}."
            
            # Changer le statut de l'article
            if article.statut == StatutArticle.LOUE:
                article.statut = StatutArticle.DISPONIBLE
            
            # Si tous les articles du contrat sont restitués, mettre à jour le contrat
            articles_du_contrat = ContratRepository.get_articles_du_contrat(db, contrat_id)
            articles_loues = [a for a in articles_du_contrat if a.statut == StatutArticle.LOUE]
            
            if not articles_loues:
                # Tous les articles sont restitués
                contrat.statut = StatutContrat.TERMINE
                contrat.date_retour_reelle = date.today()
            
            db.commit()
            return True, f"Article {article_id} restitué avec succès."
            
        except Exception as e:
            db.rollback()
            return False, f"Erreur lors de la restitution : {str(e)}"



