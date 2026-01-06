"""
Couche métier (BLL) - Logique de tarification.

Ce module contient l'algorithme de calcul des prix selon les règles métier :
- Remise de 10% si durée > 7 jours
- Remise de 15% supplémentaire si client VIP (cumulable)
- Surcharge de 5% si le client a eu un retard lors de sa dernière location

Cette logique ne peut pas être gérée uniquement par le SGBD, elle doit
être implémentée dans le code applicatif.
"""

from decimal import Decimal
from datetime import date, timedelta
from typing import List

from dal.models import Article, Client, StatutArticle
from dal.repositories import ClientRepository, ArticleRepository
from sqlalchemy.orm import Session


class ServiceTarification:
    """
    Service de calcul des prix pour les locations.
    
    Implémente toutes les règles métier de tarification.
    """
    
    @staticmethod
    def calculer_prix_base(articles: List[Article], date_debut: date, date_fin: date) -> Decimal:
        """
        Calcule le prix de base (sans remises ni surcharges).
        
        Le prix de base = somme des prix journaliers × nombre de jours
        
        Args:
            articles: Liste des articles à louer
            date_debut: Date de début de location
            date_fin: Date de fin de location
            
        Returns:
            Prix de base en euros
        """
        if not articles:
            return Decimal('0.00')
        
        # Calculer le nombre de jours (inclusif)
        nombre_jours = (date_fin - date_debut).days + 1
        
        # Somme des prix journaliers de tous les articles
        prix_journalier_total = sum(article.prix_journalier for article in articles)
        
        # Prix de base = prix journalier total × nombre de jours
        prix_base = Decimal(str(prix_journalier_total)) * Decimal(str(nombre_jours))
        
        return prix_base
    
    @staticmethod
    def calculer_remise_duree(prix_base: Decimal, date_debut: date, date_fin: date) -> Decimal:
        """
        Applique la remise de 10% si la durée de location est supérieure à 7 jours.
        
        Règle métier : Durée > 7 jours → 10% de remise
        
        Args:
            prix_base: Prix de base avant remise
            date_debut: Date de début
            date_fin: Date de fin
            
        Returns:
            Montant de la remise en euros
        """
        nombre_jours = (date_fin - date_debut).days + 1
        
        if nombre_jours > 7:
            # Remise de 10%
            remise = prix_base * Decimal('0.10')
            return remise
        
        return Decimal('0.00')
    
    @staticmethod
    def calculer_remise_vip(prix_base: Decimal, client: Client) -> Decimal:
        """
        Applique la remise de 15% si le client est VIP.
        
        Règle métier : Client VIP → 15% de remise supplémentaire (cumulable)
        
        Args:
            prix_base: Prix de base avant remise
            client: Client qui effectue la location
            
        Returns:
            Montant de la remise en euros
        """
        if bool(client.est_vip):  # type: ignore[comparison-overlap]
            # Remise de 15%
            remise = prix_base * Decimal('0.15')
            return remise
        
        return Decimal('0.00')
    
    @staticmethod
    def calculer_surcharge_retard(prix_base: Decimal, db: Session, client_id: int) -> Decimal:
        """
        Applique une surcharge de 5% si le client a eu un retard lors de sa dernière location.
        
        Règle métier : Si le client a eu un retard → +5% de surcharge
        
        Args:
            prix_base: Prix de base
            db: Session de base de données
            client_id: ID du client
            
        Returns:
            Montant de la surcharge en euros
        """
        if ClientRepository.a_eu_retard(db, client_id):
            # Surcharge de 5%
            surcharge = prix_base * Decimal('0.05')
            return surcharge
        
        return Decimal('0.00')
    
    @staticmethod
    def calculer_prix_final(
        articles: List[Article],
        client: Client,
        date_debut: date,
        date_fin: date,
        db: Session
    ) -> dict:
        """
        Calcule le prix final d'une location en appliquant toutes les règles métier.
        
        Algorithme complet :
        1. Calculer le prix de base
        2. Appliquer la remise durée (10% si > 7 jours)
        3. Appliquer la remise VIP (15% si client VIP) - cumulable
        4. Appliquer la surcharge retard (5% si retard précédent)
        5. Prix final = prix_base - remises + surcharge
        
        Args:
            articles: Liste des articles à louer
            client: Client qui effectue la location
            date_debut: Date de début
            date_fin: Date de fin
            db: Session de base de données
            
        Returns:
            Dictionnaire contenant :
            - prix_base: Prix de base
            - remise_duree: Montant de la remise durée
            - remise_vip: Montant de la remise VIP
            - surcharge_retard: Montant de la surcharge retard
            - prix_final: Prix final à payer
        """
        # 1. Calculer le prix de base
        prix_base = ServiceTarification.calculer_prix_base(articles, date_debut, date_fin)
        
        # 2. Calculer les remises
        remise_duree = ServiceTarification.calculer_remise_duree(prix_base, date_debut, date_fin)
        remise_vip = ServiceTarification.calculer_remise_vip(prix_base, client)
        
        # 3. Calculer la surcharge
        surcharge_retard = ServiceTarification.calculer_surcharge_retard(prix_base, db, client.id)  # type: ignore[arg-type]
        
        # 4. Calculer le prix final
        prix_final = prix_base - remise_duree - remise_vip + surcharge_retard
        
        # S'assurer que le prix final n'est jamais négatif
        if prix_final < Decimal('0.00'):
            prix_final = Decimal('0.00')
        
        return {
            'prix_base': prix_base,
            'remise_duree': remise_duree,
            'remise_vip': remise_vip,
            'surcharge_retard': surcharge_retard,
            'prix_final': prix_final
        }


