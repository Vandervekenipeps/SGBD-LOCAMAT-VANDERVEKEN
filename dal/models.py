"""
Modèles de données SQLAlchemy pour l'application LOCA-MAT.

Ce module contient toutes les définitions de tables (ORM) correspondant
au schéma de base de données normalisé (3NF).

Les contraintes d'intégrité sont définies ici :
- Clés primaires (PK)
- Clés étrangères (FK)
- Contraintes NOT NULL
- Contraintes UNIQUE
- Contraintes CHECK pour les validations métier
"""

from sqlalchemy import Column, Integer, String, Date, Boolean, ForeignKey, CheckConstraint, Enum as SQLEnum, Numeric
from sqlalchemy.orm import relationship
from datetime import date
import enum

from config.database import Base


class StatutArticle(enum.Enum):
    """
    Énumération des statuts possibles pour un article.
    
    Les statuts sont :
    - DISPONIBLE : Article disponible pour la location
    - LOUE : Article actuellement loué
    - EN_MAINTENANCE : Article en cours de maintenance
    - REBUT : Article hors service
    """
    DISPONIBLE = "Disponible"
    LOUE = "Loué"
    EN_MAINTENANCE = "En Maintenance"
    REBUT = "Rebut"


class StatutContrat(enum.Enum):
    """
    Énumération des statuts possibles pour un contrat de location.
    """
    EN_ATTENTE = "En Attente"
    EN_COURS = "En Cours"
    TERMINE = "Terminé"
    ANNULE = "Annulé"


class Article(Base):
    """
    Modèle représentant un article du parc de matériel.
    
    Un article peut être un équipement informatique ou industriel
    disponible à la location.
    
    Contraintes d'intégrité :
    - PK : id (auto-incrémenté)
    - NOT NULL : tous les champs obligatoires
    - CHECK : Le statut doit être valide
    - Règle métier : Un article ne peut passer à "Loué" que s'il est "Disponible"
      (gérée dans la couche BLL et par trigger SQL si nécessaire)
    """
    __tablename__ = 'articles'
    
    # Clé primaire
    id = Column(Integer, primary_key=True, autoincrement=True, 
                comment="Identifiant unique de l'article")
    
    # Informations de base
    categorie = Column(String(100), nullable=False, 
                      comment="Catégorie de l'article (ex: Ordinateur, Imprimante)")
    marque = Column(String(100), nullable=False, 
                   comment="Marque du matériel")
    modele = Column(String(100), nullable=False, 
                   comment="Modèle du matériel")
    numero_serie = Column(String(100), nullable=False, unique=True, 
                        comment="Numéro de série unique de l'article")
    date_achat = Column(Date, nullable=False, 
                       comment="Date d'achat de l'article")
    
    # Statut de l'article
    # Utilisation de String au lieu de SQLEnum pour compatibilité avec PostgreSQL
    statut = Column(SQLEnum(StatutArticle, native_enum=False, values_callable=lambda x: [e.value for e in x]), 
                   nullable=False, 
                   default=StatutArticle.DISPONIBLE,
                   comment="Statut actuel de l'article")
    
    # Prix de location journalier (pour le calcul du CA)
    prix_journalier = Column(Numeric(10, 2), nullable=False, 
                            comment="Prix de location par jour en euros")
    
    # Relations
    # Un article peut être lié à plusieurs contrats (historique)
    contrats = relationship("ArticleContrat", back_populates="article", 
                          cascade="all, delete-orphan")
    
    # Contraintes CHECK pour valider le statut et la date d'achat
    __table_args__ = (
        CheckConstraint(
            "statut IN ('Disponible', 'Loué', 'En Maintenance', 'Rebut')",
            name='check_statut_article'
        ),
        CheckConstraint(
            "date_achat <= CURRENT_DATE",
            name='check_date_achat_passee'
        ),
    )
    
    def __repr__(self):
        return f"<Article(id={self.id}, {self.marque} {self.modele}, statut={self.statut.value})>"


class Client(Base):
    """
    Modèle représentant un client de l'entreprise.
    
    Un client peut être VIP, ce qui lui donne droit à une remise de 15%
    sur les locations.
    """
    __tablename__ = 'clients'
    
    # Clé primaire
    id = Column(Integer, primary_key=True, autoincrement=True,
               comment="Identifiant unique du client")
    
    # Informations du client
    nom = Column(String(100), nullable=False,
                comment="Nom du client")
    prenom = Column(String(100), nullable=False,
                   comment="Prénom du client")
    email = Column(String(255), nullable=False, unique=True,
                  comment="Adresse email unique du client")
    telephone = Column(String(20), nullable=True,
                       comment="Numéro de téléphone")
    adresse = Column(String(255), nullable=True,
                    comment="Adresse postale")
    
    # Statut VIP pour la remise
    est_vip = Column(Boolean, nullable=False, default=False,
                    comment="Indique si le client bénéficie du statut VIP (15% de remise)")
    
    # Relations
    # Un client peut avoir plusieurs contrats
    contrats = relationship("Contrat", back_populates="client",
                          cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Client(id={self.id}, {self.prenom} {self.nom}, VIP={self.est_vip})>"


class Contrat(Base):
    """
    Modèle représentant un contrat de location.
    
    Un contrat lie un client à plusieurs articles pour une période donnée.
    Le prix total est calculé selon les règles métier (BLL).
    """
    __tablename__ = 'contrats'
    
    # Clé primaire
    id = Column(Integer, primary_key=True, autoincrement=True,
               comment="Identifiant unique du contrat")
    
    # Clé étrangère vers le client
    client_id = Column(Integer, ForeignKey('clients.id', ondelete='RESTRICT'), 
                      nullable=False,
                      comment="Référence au client qui loue")
    
    # Période de location
    date_debut = Column(Date, nullable=False,
                       comment="Date de début de la location")
    date_fin = Column(Date, nullable=False,
                     comment="Date de fin prévue de la location")
    date_retour_reelle = Column(Date, nullable=True,
                               comment="Date de retour effective (NULL si pas encore retourné)")
    
    # Prix calculé (par la couche BLL)
    prix_total = Column(Numeric(10, 2), nullable=False,
                       comment="Prix total calculé selon les règles métier")
    
    # Statut du contrat
    # Utilisation de String au lieu de SQLEnum pour compatibilité avec PostgreSQL
    statut = Column(SQLEnum(StatutContrat, native_enum=False, values_callable=lambda x: [e.value for e in x]), 
                   nullable=False,
                   default=StatutContrat.EN_ATTENTE,
                   comment="Statut actuel du contrat")
    
    # Date de création
    date_creation = Column(Date, nullable=False, default=date.today,
                          comment="Date de création du contrat")
    
    # Relations
    client = relationship("Client", back_populates="contrats")
    articles_contrats = relationship("ArticleContrat", back_populates="contrat",
                                   cascade="all, delete-orphan")
    
    # Contrainte CHECK : date_fin doit être après date_debut
    __table_args__ = (
        CheckConstraint(
            "date_fin >= date_debut",
            name='check_dates_contrat'
        ),
        CheckConstraint(
            "statut IN ('En Attente', 'En Cours', 'Terminé', 'Annulé')",
            name='check_statut_contrat'
        ),
    )
    
    def __repr__(self):
        return f"<Contrat(id={self.id}, client_id={self.client_id}, prix={self.prix_total})>"


class ArticleContrat(Base):
    """
    Table de liaison entre les articles et les contrats.
    
    Cette table permet de gérer le panier de location (plusieurs articles
    par contrat) et de respecter la normalisation 3NF.
    
    Contrainte d'intégrité critique :
    - Un article lié à un contrat ne peut pas être supprimé
      (géré par ondelete='RESTRICT' sur la FK article_id)
    """
    __tablename__ = 'articles_contrats'
    
    # Clé primaire composite
    id = Column(Integer, primary_key=True, autoincrement=True,
               comment="Identifiant unique de la liaison")
    
    # Clés étrangères
    article_id = Column(Integer, 
                       ForeignKey('articles.id', ondelete='RESTRICT'), 
                       nullable=False,
                       comment="Référence à l'article loué")
    contrat_id = Column(Integer, 
                        ForeignKey('contrats.id', ondelete='CASCADE'), 
                        nullable=False,
                        comment="Référence au contrat")
    
    # Relations
    article = relationship("Article", back_populates="contrats")
    contrat = relationship("Contrat", back_populates="articles_contrats")
    
    # Contrainte UNIQUE : un article ne peut être dans un contrat qu'une seule fois
    __table_args__ = (
        CheckConstraint(
            "article_id IS NOT NULL AND contrat_id IS NOT NULL",
            name='check_article_contrat_not_null'
        ),
    )
    
    def __repr__(self):
        return f"<ArticleContrat(article_id={self.article_id}, contrat_id={self.contrat_id})>"


