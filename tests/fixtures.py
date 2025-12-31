"""
Script de données de test (fixtures) pour l'application LOCA-MAT.

Ce script crée des données de test réalistes pour tester toutes les fonctionnalités :
- Articles de différentes catégories
- Clients (VIP et non-VIP)
- Contrats de location (en cours, terminés, avec retards)
- Historique de locations

Permet de tester :
- Le tableau de bord avec des données réelles
- Les requêtes d'agrégation
- Les calculs de tarification
- Les alertes de retards
"""

import sys
import os
# Ajouter le répertoire parent au chemin Python
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from datetime import date, timedelta
from decimal import Decimal

from config.database import SessionLocal
from dal.models import Article, Client, Contrat, ArticleContrat, StatutArticle, StatutContrat
from dal.repositories import ArticleRepository, ClientRepository, ContratRepository


def creer_donnees_test():
    """
    Crée des données de test complètes pour l'application.
    """
    db: Session = SessionLocal()
    
    try:
        print("=" * 80)
        print("CREATION DES DONNEES DE TEST")
        print("=" * 80)
        
        # Nettoyer les données existantes (optionnel)
        print("\n1. Nettoyage des donnees existantes...")
        db.query(ArticleContrat).delete()
        db.query(Contrat).delete()
        db.query(Article).delete()
        db.query(Client).delete()
        db.commit()
        print("   [OK] Donnees nettoyees")
        
        # 2. Créer des articles
        print("\n2. Creation des articles...")
        articles = []
        
        # Articles informatiques
        articles.append(Article(
            categorie="Ordinateur",
            marque="Dell",
            modele="Latitude 5520",
            numero_serie="DELL-001",
            date_achat=date(2023, 1, 15),
            prix_journalier=Decimal('25.00'),
            statut=StatutArticle.DISPONIBLE
        ))
        
        articles.append(Article(
            categorie="Ordinateur",
            marque="HP",
            modele="EliteBook 850",
            numero_serie="HP-001",
            date_achat=date(2023, 3, 20),
            prix_journalier=Decimal('30.00'),
            statut=StatutArticle.DISPONIBLE
        ))
        
        articles.append(Article(
            categorie="Imprimante",
            marque="Canon",
            modele="PIXMA TR8620",
            numero_serie="CANON-001",
            date_achat=date(2023, 5, 10),
            prix_journalier=Decimal('15.00'),
            statut=StatutArticle.DISPONIBLE
        ))
        
        articles.append(Article(
            categorie="Projecteur",
            marque="Epson",
            modele="EB-X41",
            numero_serie="EPSON-001",
            date_achat=date(2023, 2, 5),
            prix_journalier=Decimal('40.00'),
            statut=StatutArticle.EN_MAINTENANCE
        ))
        
        articles.append(Article(
            categorie="Tablette",
            marque="Samsung",
            modele="Galaxy Tab S8",
            numero_serie="SAMSUNG-001",
            date_achat=date(2023, 6, 1),
            prix_journalier=Decimal('20.00'),
            statut=StatutArticle.DISPONIBLE
        ))
        
        articles.append(Article(
            categorie="Ordinateur",
            marque="Lenovo",
            modele="ThinkPad X1",
            numero_serie="LENOVO-001",
            date_achat=date(2023, 4, 12),
            prix_journalier=Decimal('35.00'),
            statut=StatutArticle.DISPONIBLE
        ))
        
        for article in articles:
            ArticleRepository.create(db, article)
        
        print(f"   [OK] {len(articles)} articles crees")
        
        # 3. Créer des clients
        print("\n3. Creation des clients...")
        clients = []
        
        clients.append(Client(
            nom="Dupont",
            prenom="Jean",
            email="jean.dupont@example.com",
            telephone="0123456789",
            adresse="123 Rue de la Paix, 75001 Paris",
            est_vip=True  # Client VIP
        ))
        
        clients.append(Client(
            nom="Martin",
            prenom="Marie",
            email="marie.martin@example.com",
            telephone="0987654321",
            adresse="456 Avenue des Champs, 69000 Lyon",
            est_vip=False
        ))
        
        clients.append(Client(
            nom="Bernard",
            prenom="Pierre",
            email="pierre.bernard@example.com",
            telephone="0555666777",
            est_vip=True  # Client VIP
        ))
        
        clients.append(Client(
            nom="Dubois",
            prenom="Sophie",
            email="sophie.dubois@example.com",
            telephone="0444555666",
            est_vip=False
        ))
        
        for client in clients:
            ClientRepository.create(db, client)
        
        print(f"   [OK] {len(clients)} clients crees (dont {sum(1 for c in clients if c.est_vip)} VIP)")
        
        # 4. Créer des contrats (pour tester le tableau de bord)
        print("\n4. Creation des contrats de location...")
        
        # Contrat 1 : Location en cours (normal)
        date_debut1 = date.today() - timedelta(days=5)
        date_fin1 = date.today() + timedelta(days=2)
        contrat1 = Contrat(
            client_id=clients[0].id,  # Jean Dupont (VIP)
            date_debut=date_debut1,
            date_fin=date_fin1,
            prix_total=Decimal('350.00'),
            statut=StatutContrat.EN_COURS,
            date_creation=date_debut1
        )
        contrat1 = ContratRepository.create(db, contrat1)
        ContratRepository.ajouter_article(db, contrat1.id, articles[0].id)  # Dell
        articles[0].statut = StatutArticle.LOUE
        ArticleRepository.update(db, articles[0])
        print(f"   [OK] Contrat 1 cree (en cours, client VIP)")
        
        # Contrat 2 : Location terminée (dans les 30 derniers jours)
        date_debut2 = date.today() - timedelta(days=20)
        date_fin2 = date.today() - timedelta(days=10)
        contrat2 = Contrat(
            client_id=clients[1].id,  # Marie Martin
            date_debut=date_debut2,
            date_fin=date_fin2,
            date_retour_reelle=date_fin2,
            prix_total=Decimal('200.00'),
            statut=StatutContrat.TERMINE,
            date_creation=date_debut2
        )
        contrat2 = ContratRepository.create(db, contrat2)
        ContratRepository.ajouter_article(db, contrat2.id, articles[1].id)  # HP
        articles[1].statut = StatutArticle.DISPONIBLE  # Restitué
        ArticleRepository.update(db, articles[1])
        print(f"   [OK] Contrat 2 cree (termine, dans les 30 derniers jours)")
        
        # Contrat 3 : Location EN RETARD (pour tester les alertes)
        date_debut3 = date.today() - timedelta(days=15)
        date_fin3 = date.today() - timedelta(days=3)  # Date dépassée !
        contrat3 = Contrat(
            client_id=clients[2].id,  # Pierre Bernard (VIP)
            date_debut=date_debut3,
            date_fin=date_fin3,
            prix_total=Decimal('280.00'),
            statut=StatutContrat.EN_COURS,
            date_creation=date_debut3
        )
        contrat3 = ContratRepository.create(db, contrat3)
        ContratRepository.ajouter_article(db, contrat3.id, articles[4].id)  # Samsung
        articles[4].statut = StatutArticle.LOUE
        ArticleRepository.update(db, articles[4])
        print(f"   [OK] Contrat 3 cree (EN RETARD - date depassee)")
        
        # Contrat 4 : Location récente (pour le Top 5)
        date_debut4 = date.today() - timedelta(days=10)
        date_fin4 = date.today() + timedelta(days=5)
        contrat4 = Contrat(
            client_id=clients[3].id,  # Sophie Dubois
            date_debut=date_debut4,
            date_fin=date_fin4,
            prix_total=Decimal('150.00'),
            statut=StatutContrat.EN_COURS,
            date_creation=date_debut4
        )
        contrat4 = ContratRepository.create(db, contrat4)
        ContratRepository.ajouter_article(db, contrat4.id, articles[2].id)  # Canon
        articles[2].statut = StatutArticle.LOUE
        ArticleRepository.update(db, articles[2])
        print(f"   [OK] Contrat 4 cree (en cours, recent)")
        
        # Contrat 5 : Location terminée ce mois (pour le Top 5)
        date_debut5 = date.today().replace(day=1) + timedelta(days=5)  # Début du mois
        date_fin5 = date.today().replace(day=1) + timedelta(days=12)
        contrat5 = Contrat(
            client_id=clients[0].id,  # Jean Dupont (VIP)
            date_debut=date_debut5,
            date_fin=date_fin5,
            date_retour_reelle=date_fin5,
            prix_total=Decimal('420.00'),  # Prix élevé pour être dans le Top 5
            statut=StatutContrat.TERMINE,
            date_creation=date_debut5
        )
        contrat5 = ContratRepository.create(db, contrat5)
        ContratRepository.ajouter_article(db, contrat5.id, articles[5].id)  # Lenovo
        articles[5].statut = StatutArticle.DISPONIBLE  # Restitué
        ArticleRepository.update(db, articles[5])
        print(f"   [OK] Contrat 5 cree (termine ce mois, prix eleve)")
        
        print(f"\n   [OK] {5} contrats crees")
        
        print("\n" + "=" * 80)
        print("[SUCCES] DONNEES DE TEST CREEES AVEC SUCCES")
        print("=" * 80)
        print("\nResume :")
        print(f"  - {len(articles)} articles (dont {sum(1 for a in articles if a.statut == StatutArticle.DISPONIBLE)} disponibles)")
        print(f"  - {len(clients)} clients (dont {sum(1 for c in clients if c.est_vip)} VIP)")
        print(f"  - 5 contrats (en cours, termines, en retard)")
        print("\nVous pouvez maintenant tester :")
        print("  - Le tableau de bord (Top 5, CA 30 jours, alertes retards)")
        print("  - Les locations avec calcul tarifaire")
        print("  - Les requetes d'agregation")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n[ERREUR] Erreur lors de la creation des donnees : {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    creer_donnees_test()

