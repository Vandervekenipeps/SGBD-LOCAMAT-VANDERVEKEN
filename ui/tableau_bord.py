"""
Interface utilisateur - Tableau de bord décisionnel.

Ce module affiche les indicateurs calculés en temps réel avec des requêtes
d'agrégation SQL optimisées.

Indicateurs affichés :
- Top 5 des matériels les plus rentables du mois
- Chiffre d'affaires total des 30 derniers jours
- Liste d'alerte : Articles non restitués avec date de retour dépassée
"""

from sqlalchemy.orm import Session
from datetime import date
from decimal import Decimal

from dal.repositories import ContratRepository
from config.database import get_db


class TableauBord:
    """
    Classe pour afficher le tableau de bord décisionnel.
    
    Toutes les requêtes d'agrégation sont exécutées ici, pas dans la couche UI.
    """
    
    @staticmethod
    def afficher_tableau_bord(db: Session):
        """
        Affiche le tableau de bord complet avec tous les indicateurs.
        
        Args:
            db: Session de base de données
        """
        print("\n" + "=" * 80)
        print("TABLEAU DE BORD - LOCA-MAT ENTREPRISE")
        print("=" * 80)
        
        # 1. Top 5 des matériels les plus rentables du mois
        print("\n📊 TOP 5 DES MATÉRIELS LES PLUS RENTABLES DU MOIS")
        print("-" * 80)
        top_5 = ContratRepository.get_top_5_rentables(db)
        
        if top_5:
            for i, materiel in enumerate(top_5, 1):
                print(
                    f"{i}. {materiel['marque']} {materiel['modele']} "
                    f"({materiel['categorie']}) - "
                    f"CA: {materiel['ca_total']:.2f} €"
                )
        else:
            print("Aucun matériel loué ce mois-ci.")
        
        # 2. Chiffre d'affaires des 30 derniers jours
        print("\n💰 CHIFFRE D'AFFAIRES DES 30 DERNIERS JOURS")
        print("-" * 80)
        ca_30_jours = ContratRepository.get_ca_30_jours(db)
        print(f"Total : {float(ca_30_jours):.2f} €")
        
        # 3. Liste d'alerte : Articles en retard
        print("\n⚠️  ALERTES - ARTICLES NON RESTITUÉS (DATE DÉPASSÉE)")
        print("-" * 80)
        retards = ContratRepository.get_retards(db)
        
        if retards:
            for contrat in retards:
                jours_retard = (date.today() - contrat.date_fin).days
                print(
                    f"Contrat #{contrat.id} - Client ID: {contrat.client_id} - "
                    f"Date de retour prévue: {contrat.date_fin} - "
                    f"Retard: {jours_retard} jour(s)"
                )
        else:
            print("Aucun retard à signaler.")
        
        print("\n" + "=" * 80)

