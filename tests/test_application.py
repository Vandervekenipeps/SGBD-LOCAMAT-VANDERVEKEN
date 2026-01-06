"""
Script de test complet de l'application LOCA-MAT.

Ce script teste toutes les fonctionnalités principales :
- Connexion à la base de données
- Contraintes d'intégrité
- Trigger de validation de statut
- Transactions ACID
- Calcul tarifaire
- Requêtes d'agrégation

UTILISATION DES BREAKPOINTS :
Ce script contient des breakpoints stratégiques pour le débogage.
Pour utiliser les breakpoints :
1. Exécuter le script : python tests/test_application.py
2. Quand un breakpoint est atteint, le débogueur s'arrête
3. Utiliser les commandes du débogueur :
   - 'n' (next) : ligne suivante
   - 's' (step) : entrer dans une fonction
   - 'c' (continue) : continuer jusqu'au prochain breakpoint
   - 'p variable' : afficher la valeur d'une variable
   - 'pp variable' : afficher joliment une variable
   - 'l' (list) : afficher le code autour de la ligne actuelle
   - 'q' (quit) : quitter le débogueur

Pour activer les breakpoints (mode débogage) :
- Windows PowerShell: $env:DEBUG_MODE="True"; python tests/test_application.py
- Windows CMD: set DEBUG_MODE=True && python tests/test_application.py

Par défaut, les breakpoints sont désactivés pour permettre l'exécution normale des tests.
"""

import sys
import os
# Ajouter le répertoire parent au chemin Python
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text

from config.database import SessionLocal, engine
from dal.models import Article, Client, Contrat, ArticleContrat, StatutArticle, StatutContrat
from dal.repositories import ArticleRepository, ClientRepository, ContratRepository
from bll.tarification import ServiceTarification
from bll.transactions import ServiceTransaction
from bll.validation import ServiceValidation

# Variable globale pour activer/désactiver les breakpoints
# Utiliser: DEBUG_MODE=True python tests/test_application.py
# Ou définir la variable d'environnement: set DEBUG_MODE=True
DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"

def debug_breakpoint(*args):
    """Breakpoint conditionnel basé sur DEBUG_MODE."""
    if DEBUG_MODE:
        breakpoint()  # type: ignore[call-arg]


class TestsApplication:
    """Classe pour exécuter tous les tests de l'application."""
    
    def __init__(self):
        """Initialise les tests."""
        self.db: Session = SessionLocal()
        self.erreurs = []
        self.succes = []
    
    def test_connexion(self):
        """Test 1 : Vérification de la connexion à la base de données."""
        print("\n" + "=" * 80)
        print("TEST 1 : CONNEXION A LA BASE DE DONNEES")
        print("=" * 80)
        try:
            with engine.connect() as conn:
                result = conn.execute(text("SELECT version()"))
                row = result.fetchone()
                version = row[0] if row else "Version inconnue"  # type: ignore[index]
                print(f"[OK] Connexion reussie")
                print(f"     PostgreSQL: {version[:50]}...")
                # BREAKPOINT : Inspecter la connexion et la version
                debug_breakpoint()  # Inspecter: conn, version
                self.succes.append("Connexion DB")
        except Exception as e:
            print(f"[ERREUR] Echec de connexion : {e}")
            self.erreurs.append(f"Connexion DB : {e}")
    
    def test_contraintes_integrite(self):
        """Test 2 : Vérification des contraintes d'intégrité."""
        print("\n" + "=" * 80)
        print("TEST 2 : CONTRAINTES D'INTEGRITE")
        print("=" * 80)
        
        # Test 2.1 : Contrainte UNIQUE sur email client
        print("\n2.1 Test contrainte UNIQUE (email client)...")
        try:
            import random
            email_unique = f"test{random.randint(10000, 99999)}@example.com"
            client1 = Client(
                nom="Dupont", prenom="Jean", email=email_unique, est_vip=False
            )
            ClientRepository.create(self.db, client1)
            print("   [OK] Premier client cree")
            # BREAKPOINT : Inspecter le client créé avant test de contrainte UNIQUE
            debug_breakpoint()  # Inspecter: client1, email_unique
            
            # Essayer de créer un deuxième client avec le même email
            client2 = Client(
                nom="Martin", prenom="Pierre", email=email_unique, est_vip=False
            )
            try:
                ClientRepository.create(self.db, client2)
                print("   [ERREUR] Contrainte UNIQUE non respectee !")
                self.erreurs.append("Contrainte UNIQUE email")
                self.db.rollback()
            except IntegrityError:
                print("   [OK] Contrainte UNIQUE respectee (email duplique refuse)")
                self.succes.append("Contrainte UNIQUE email")
                self.db.rollback()
            
            # Nettoyer le premier client
            self.db.delete(client1)
            self.db.commit()
        except Exception as e:
            print(f"   [ERREUR] {e}")
            self.erreurs.append(f"Test UNIQUE : {e}")
            self.db.rollback()
        
        # Test 2.2 : Contrainte FK RESTRICT (suppression article lié)
        print("\n2.2 Test contrainte FK RESTRICT (suppression article lie)...")
        try:
            import random
            # Créer un article et un contrat avec valeurs uniques
            numero_serie_unique = f"TEST-RESTRICT-{random.randint(10000, 99999)}"
            article = Article(
                categorie="Test", marque="Test", modele="Test",
                numero_serie=numero_serie_unique, date_achat=date.today(),
                prix_journalier=Decimal('10.00'), statut=StatutArticle.DISPONIBLE
            )
            article = ArticleRepository.create(self.db, article)
            
            email_client_unique = f"client{random.randint(10000, 99999)}@test.com"
            client = Client(
                nom="Client", prenom="Test", email=email_client_unique, est_vip=False
            )
            client = ClientRepository.create(self.db, client)
            
            contrat = Contrat(
                client_id=client.id, date_debut=date.today(),
                date_fin=date.today() + timedelta(days=7),
                prix_total=Decimal('70.00'), statut=StatutContrat.EN_COURS
            )
            # Forcer la valeur du statut pour correspondre à la contrainte CHECK
            contrat.statut = StatutContrat.EN_COURS  # type: ignore[assignment]
            contrat = ContratRepository.create(self.db, contrat)
            
            # Lier l'article au contrat
            ContratRepository.ajouter_article(self.db, contrat.id, article.id)  # type: ignore[arg-type]
            self.db.commit()  # S'assurer que la liaison est commitée
            
            # Vérifier que la liaison existe vraiment dans la base
            from dal.models import ArticleContrat
            liaison = self.db.query(ArticleContrat).filter(
                ArticleContrat.article_id == article.id,
                ArticleContrat.contrat_id == contrat.id
            ).first()
            
            if not liaison:
                print("   [ERREUR] La liaison article-contrat n'a pas ete creee")
                self.erreurs.append("Liaison article-contrat")
                self.db.rollback()
                return
            
            print(f"   [OK] Liaison creee (Article {article.id} <-> Contrat {contrat.id})")
            # BREAKPOINT : Inspecter la liaison avant test de contrainte RESTRICT
            debug_breakpoint()  # Inspecter: article, contrat, liaison
            
            # Essayer de supprimer l'article (doit échouer avec RESTRICT)
            # Utiliser une requête SQL directe pour tester la contrainte au niveau SGBD
            try:
                from sqlalchemy import text
                # Tentative de suppression via SQL direct pour déclencher la contrainte RESTRICT
                result = self.db.execute(
                    text(f"DELETE FROM articles WHERE id = :article_id"),
                    {"article_id": article.id}
                )
                self.db.commit()
                
                # Si on arrive ici, la contrainte n'a pas fonctionné
                print("   [ERREUR] Contrainte RESTRICT non respectee ! L'article a ete supprime alors qu'il est lie a un contrat.")
                self.erreurs.append("Contrainte RESTRICT")
                
            except IntegrityError as e:
                error_msg = str(e).lower()
                self.db.rollback()
                # La contrainte RESTRICT devrait lever une IntegrityError
                print(f"   [OK] Contrainte RESTRICT respectee (suppression article lie refusee)")
                print(f"        Erreur PostgreSQL: {str(e)[:100]}...")
                self.succes.append("Contrainte RESTRICT")
            except Exception as e:
                self.db.rollback()
                error_msg = str(e).lower()
                # Toute exception lors de la suppression d'un article lié est un signe que ça fonctionne
                if "foreign" in error_msg or "constraint" in error_msg or "violates" in error_msg:
                    print(f"   [OK] Contrainte RESTRICT respectee (exception levee: {type(e).__name__})")
                    self.succes.append("Contrainte RESTRICT")
                else:
                    print(f"   [ERREUR] Exception inattendue : {e}")
                    self.erreurs.append(f"Contrainte RESTRICT : {e}")
            
            # Nettoyer
            self.db.rollback()
        except Exception as e:
            print(f"   [ERREUR] {e}")
            self.erreurs.append(f"Test RESTRICT : {e}")
            self.db.rollback()
    
    def test_trigger_statut(self):
        """Test 3 : Vérification du trigger de validation de statut."""
        print("\n" + "=" * 80)
        print("TEST 3 : TRIGGER DE VALIDATION DE STATUT")
        print("=" * 80)
        
        try:
            # Créer un article en maintenance
            article = Article(
                categorie="Test", marque="Test", modele="Test",
                numero_serie="TEST-TRIGGER-001", date_achat=date.today(),
                prix_journalier=Decimal('10.00'), statut=StatutArticle.EN_MAINTENANCE
            )
            article = ArticleRepository.create(self.db, article)
            print(f"\n3.1 Article cree avec statut 'En Maintenance' (ID: {article.id})")
            # BREAKPOINT : Inspecter l'article avant test du trigger
            debug_breakpoint()  # Inspecter: article, article.statut
            
            # Essayer de passer directement à "Loué" (doit échouer avec le trigger)
            try:
                # Mise à jour directe via SQL pour tester le trigger
                self.db.execute(
                    text(f"UPDATE articles SET statut = 'Loué' WHERE id = {article.id}")
                )
                self.db.commit()
                print("   [ERREUR] Trigger ne fonctionne pas ! L'article est passe a 'Loue' sans etre 'Disponible'")
                self.erreurs.append("Trigger validation statut")
            except Exception as e:
                error_msg = str(e)
                if "ne peut passer au statut" in error_msg or "Disponible" in error_msg:
                    print("   [OK] Trigger fonctionne : passage a 'Loue' refuse (article doit etre 'Disponible')")
                    self.succes.append("Trigger validation statut")
                else:
                    print(f"   [ATTENTION] Erreur inattendue : {e}")
                    self.erreurs.append(f"Trigger : {e}")
                self.db.rollback()
            
            # Test du passage correct : Maintenance -> Disponible -> Loué
            print("\n3.2 Test passage correct Maintenance -> Disponible -> Loue...")
            article.statut = StatutArticle.DISPONIBLE  # type: ignore[assignment]
            ArticleRepository.update(self.db, article)
            print("   [OK] Statut change a 'Disponible'")
            
            article.statut = StatutArticle.LOUE  # type: ignore[assignment]
            ArticleRepository.update(self.db, article)
            print("   [OK] Statut change a 'Loue' (depuis 'Disponible')")
            self.succes.append("Changement statut correct")
            
            # Nettoyer
            self.db.delete(article)
            self.db.commit()
            
        except Exception as e:
            print(f"   [ERREUR] {e}")
            self.erreurs.append(f"Test trigger : {e}")
            self.db.rollback()
    
    def test_calcul_tarification(self):
        """Test 4 : Vérification du calcul tarifaire."""
        print("\n" + "=" * 80)
        print("TEST 4 : CALCUL TARIFAIRE")
        print("=" * 80)
        
        try:
            # Créer des articles de test
            article1 = Article(
                categorie="Test", marque="Test", modele="Article1",
                numero_serie="TARIF-001", date_achat=date.today(),
                prix_journalier=Decimal('20.00'), statut=StatutArticle.DISPONIBLE
            )
            article2 = Article(
                categorie="Test", marque="Test", modele="Article2",
                numero_serie="TARIF-002", date_achat=date.today(),
                prix_journalier=Decimal('30.00'), statut=StatutArticle.DISPONIBLE
            )
            article1 = ArticleRepository.create(self.db, article1)
            article2 = ArticleRepository.create(self.db, article2)
            
            # Créer un client VIP
            client_vip = Client(
                nom="VIP", prenom="Client", email="vip@test.com", est_vip=True
            )
            client_vip = ClientRepository.create(self.db, client_vip)
            
            # Test 4.1 : Prix de base (8 jours, 2 articles)
            date_debut = date.today()
            date_fin = date.today() + timedelta(days=7)  # 8 jours au total
            articles = [article1, article2]
            
            prix_base = ServiceTarification.calculer_prix_base(articles, date_debut, date_fin)
            prix_attendu = Decimal('50.00') * Decimal('8')  # (20+30) * 8 = 400
            print(f"\n4.1 Prix de base : {prix_base} € (attendu: {prix_attendu} €)")
            # BREAKPOINT : Inspecter le calcul tarifaire
            debug_breakpoint()  # Inspecter: articles, date_debut, date_fin, prix_base, prix_attendu
            if prix_base == prix_attendu:
                print("   [OK] Calcul prix de base correct")
                self.succes.append("Calcul prix base")
            else:
                print(f"   [ERREUR] Prix incorrect")
                self.erreurs.append("Calcul prix base")
            
            # Test 4.2 : Remise durée (> 7 jours)
            remise_duree = ServiceTarification.calculer_remise_duree(prix_base, date_debut, date_fin)
            remise_attendu = prix_base * Decimal('0.10')  # 10% de 400 = 40
            print(f"\n4.2 Remise duree : {remise_duree} € (attendu: {remise_attendu} €)")
            if remise_duree == remise_attendu:
                print("   [OK] Remise duree correcte")
                self.succes.append("Remise duree")
            else:
                print(f"   [ERREUR] Remise incorrecte")
                self.erreurs.append("Remise duree")
            
            # Test 4.3 : Remise VIP
            remise_vip = ServiceTarification.calculer_remise_vip(prix_base, client_vip)
            remise_vip_attendu = prix_base * Decimal('0.15')  # 15% de 400 = 60
            print(f"\n4.3 Remise VIP : {remise_vip} € (attendu: {remise_vip_attendu} €)")
            if remise_vip == remise_vip_attendu:
                print("   [OK] Remise VIP correcte")
                self.succes.append("Remise VIP")
            else:
                print(f"   [ERREUR] Remise VIP incorrecte")
                self.erreurs.append("Remise VIP")
            
            # Test 4.4 : Calcul final complet
            calcul = ServiceTarification.calculer_prix_final(
                articles, client_vip, date_debut, date_fin, self.db
            )
            prix_final_attendu = prix_base - remise_duree - remise_vip  # 400 - 40 - 60 = 300
            print(f"\n4.4 Prix final : {calcul['prix_final']} € (attendu: {prix_final_attendu} €)")
            print(f"     Detail: {prix_base} - {remise_duree} - {remise_vip} = {calcul['prix_final']}")
            # BREAKPOINT : Inspecter le calcul final complet
            debug_breakpoint()  # Inspecter: calcul, prix_base, remise_duree, remise_vip, prix_final_attendu
            if calcul['prix_final'] == prix_final_attendu:
                print("   [OK] Calcul prix final correct")
                self.succes.append("Calcul prix final")
            else:
                print(f"   [ERREUR] Prix final incorrect")
                self.erreurs.append("Calcul prix final")
            
            # Nettoyer
            self.db.delete(article1)
            self.db.delete(article2)
            self.db.delete(client_vip)
            self.db.commit()
            
        except Exception as e:
            print(f"   [ERREUR] {e}")
            self.erreurs.append(f"Test tarification : {e}")
            self.db.rollback()
    
    def test_transaction_atomique(self):
        """Test 5 : Vérification des transactions ACID."""
        print("\n" + "=" * 80)
        print("TEST 5 : TRANSACTIONS ACID")
        print("=" * 80)
        
        try:
            # Créer un client et des articles (avec email unique)
            import random
            email_unique = f"trans{random.randint(1000, 9999)}@test.com"
            client = Client(
                nom="Test", prenom="Transaction", email=email_unique, est_vip=False
            )
            client = ClientRepository.create(self.db, client)
            
            article1 = Article(
                categorie="Test", marque="Test", modele="Trans1",
                numero_serie="TRANS-001", date_achat=date.today(),
                prix_journalier=Decimal('10.00'), statut=StatutArticle.DISPONIBLE
            )
            article2 = Article(
                categorie="Test", marque="Test", modele="Trans2",
                numero_serie="TRANS-002", date_achat=date.today(),
                prix_journalier=Decimal('15.00'), statut=StatutArticle.DISPONIBLE
            )
            article1 = ArticleRepository.create(self.db, article1)
            article2 = ArticleRepository.create(self.db, article2)
            
            # Test 5.1 : Transaction réussie
            print("\n5.1 Test transaction reussie...")
            date_debut = date.today()
            date_fin = date.today() + timedelta(days=3)
            
            succes, contrat, message = ServiceTransaction.valider_panier_transactionnel(
                self.db, client.id, [article1.id, article2.id], date_debut, date_fin  # type: ignore[arg-type]
            )
            # BREAKPOINT : Inspecter le résultat de la transaction ACID
            debug_breakpoint()  # Inspecter: succes, contrat, message, client, article1, article2
            
            if succes and contrat:
                print(f"   [OK] Transaction reussie (Contrat ID: {contrat.id})")
                print(f"        Message: {message}")
                
                # Vérifier que les articles sont bien passés à "Loué"
                article1 = ArticleRepository.get_by_id(self.db, article1.id)  # type: ignore[arg-type]
                article2 = ArticleRepository.get_by_id(self.db, article2.id)  # type: ignore[arg-type]
                # BREAKPOINT : Inspecter les statuts des articles après transaction
                debug_breakpoint()  # Inspecter: article1.statut, article2.statut, contrat
                if article1 and article2 and article1.statut == StatutArticle.LOUE and article2.statut == StatutArticle.LOUE:  # type: ignore[comparison-overlap]
                    print("   [OK] Statuts des articles mis a jour correctement")
                    self.succes.append("Transaction ACID")
                else:
                    print("   [ERREUR] Statuts des articles non mis a jour")
                    self.erreurs.append("Transaction statuts")
            else:
                print(f"   [ERREUR] Transaction echouee : {message}")
                self.erreurs.append("Transaction ACID")
            
            # Nettoyer
            if contrat:
                self.db.delete(contrat)
            self.db.delete(article1)
            self.db.delete(article2)
            self.db.delete(client)
            self.db.commit()
            
        except Exception as e:
            print(f"   [ERREUR] {e}")
            self.erreurs.append(f"Test transaction : {e}")
            self.db.rollback()
    
    def test_requetes_agregation(self):
        """Test 6 : Vérification des requêtes d'agrégation."""
        print("\n" + "=" * 80)
        print("TEST 6 : REQUETES D'AGREGATION (TABLEAU DE BORD)")
        print("=" * 80)
        
        try:
            # Test 6.1 : CA des 30 derniers jours
            print("\n6.1 Test CA des 30 derniers jours...")
            ca = ContratRepository.get_ca_30_jours(self.db)
            print(f"   CA total : {float(ca):.2f} €")
            # BREAKPOINT : Inspecter le résultat de l'agrégation CA
            debug_breakpoint()  # Inspecter: ca, self.db
            print("   [OK] Requete d'agregation executee sans erreur")
            self.succes.append("Requete CA 30 jours")
            
            # Test 6.2 : Top 5 matériels rentables
            print("\n6.2 Test Top 5 materiaels rentables...")
            top_5 = ContratRepository.get_top_5_rentables(self.db)
            print(f"   Nombre de resultats : {len(top_5)}")
            # BREAKPOINT : Inspecter le résultat de l'agrégation Top 5
            debug_breakpoint()  # Inspecter: top_5, len(top_5)
            if isinstance(top_5, list):
                print("   [OK] Requete d'agregation executee sans erreur")
                self.succes.append("Requete Top 5")
            else:
                print("   [ERREUR] Format de retour incorrect")
                self.erreurs.append("Requete Top 5")
            
            # Test 6.3 : Liste des retards
            print("\n6.3 Test liste des retards...")
            retards = ContratRepository.get_retards(self.db)
            print(f"   Nombre de retards : {len(retards)}")
            if isinstance(retards, list):
                print("   [OK] Requete d'agregation executee sans erreur")
                self.succes.append("Requete retards")
            else:
                print("   [ERREUR] Format de retour incorrect")
                self.erreurs.append("Requete retards")
            
        except Exception as e:
            print(f"   [ERREUR] {e}")
            self.erreurs.append(f"Test agregations : {e}")
    
    def afficher_resume(self):
        """Affiche le résumé des tests."""
        print("\n" + "=" * 80)
        print("RESUME DES TESTS")
        print("=" * 80)
        print(f"\nTests reussis : {len(self.succes)}")
        for test in self.succes:
            print(f"  [OK] {test}")
        
        print(f"\nTests echoues : {len(self.erreurs)}")
        for erreur in self.erreurs:
            print(f"  [ERREUR] {erreur}")
        
        print("\n" + "=" * 80)
        if len(self.erreurs) == 0:
            print("[SUCCES] TOUS LES TESTS SONT PASSES !")
        else:
            print(f"[ATTENTION] {len(self.erreurs)} test(s) ont echoue")
        print("=" * 80)
    
    def executer_tous_les_tests(self):
        """Exécute tous les tests."""
        print("\n" + "=" * 80)
        print("SUITE DE TESTS - APPLICATION LOCA-MAT")
        print("=" * 80)
        
        self.test_connexion()
        self.test_contraintes_integrite()
        self.test_trigger_statut()
        self.test_calcul_tarification()
        self.test_transaction_atomique()
        self.test_requetes_agregation()
        self.afficher_resume()
        
        self.db.close()


if __name__ == "__main__":
    tests = TestsApplication()
    tests.executer_tous_les_tests()

