-- Script SQL pour créer toutes les tables de l'application LOCA-MAT
-- À exécuter directement dans Neon (via l'éditeur SQL ou psql)

-- Supprimer les tables si elles existent déjà (optionnel, décommenter si besoin)
-- DROP TABLE IF EXISTS articles_contrats CASCADE;
-- DROP TABLE IF EXISTS contrats CASCADE;
-- DROP TABLE IF EXISTS articles CASCADE;
-- DROP TABLE IF EXISTS clients CASCADE;

-- Table des clients
CREATE TABLE IF NOT EXISTS clients (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    prenom VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    telephone VARCHAR(20),
    adresse VARCHAR(255),
    est_vip BOOLEAN NOT NULL DEFAULT FALSE
);

COMMENT ON TABLE clients IS 'Table des clients de l''entreprise';
COMMENT ON COLUMN clients.est_vip IS 'Indique si le client bénéficie du statut VIP (15% de remise)';

-- Table des articles (matériel)
CREATE TABLE IF NOT EXISTS articles (
    id SERIAL PRIMARY KEY,
    categorie VARCHAR(100) NOT NULL,
    marque VARCHAR(100) NOT NULL,
    modele VARCHAR(100) NOT NULL,
    numero_serie VARCHAR(100) NOT NULL UNIQUE,
    date_achat DATE NOT NULL,
    statut VARCHAR(20) NOT NULL DEFAULT 'Disponible',
    prix_journalier NUMERIC(10, 2) NOT NULL,
    CONSTRAINT check_statut_article CHECK (statut IN ('Disponible', 'Loué', 'En Maintenance', 'Rebut'))
);

COMMENT ON TABLE articles IS 'Table du parc de matériel disponible à la location';
COMMENT ON COLUMN articles.statut IS 'Statut de l''article : Disponible, Loué, En Maintenance, Rebut';

-- Table des contrats de location
CREATE TABLE IF NOT EXISTS contrats (
    id SERIAL PRIMARY KEY,
    client_id INTEGER NOT NULL,
    date_debut DATE NOT NULL,
    date_fin DATE NOT NULL,
    date_retour_reelle DATE,
    prix_total NUMERIC(10, 2) NOT NULL,
    statut VARCHAR(20) NOT NULL DEFAULT 'En Attente',
    date_creation DATE NOT NULL DEFAULT CURRENT_DATE,
    CONSTRAINT fk_contrat_client FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE RESTRICT,
    CONSTRAINT check_dates_contrat CHECK (date_fin >= date_debut),
    CONSTRAINT check_statut_contrat CHECK (statut IN ('En Attente', 'En Cours', 'Terminé', 'Annulé'))
);

COMMENT ON TABLE contrats IS 'Table des contrats de location';
COMMENT ON COLUMN contrats.prix_total IS 'Prix total calculé selon les règles métier (remises, surcharges)';

-- Table de liaison articles-contrats (normalisation 3NF)
CREATE TABLE IF NOT EXISTS articles_contrats (
    id SERIAL PRIMARY KEY,
    article_id INTEGER NOT NULL,
    contrat_id INTEGER NOT NULL,
    CONSTRAINT fk_article_contrat_article FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE RESTRICT,
    CONSTRAINT fk_article_contrat_contrat FOREIGN KEY (contrat_id) REFERENCES contrats(id) ON DELETE CASCADE,
    CONSTRAINT check_article_contrat_not_null CHECK (article_id IS NOT NULL AND contrat_id IS NOT NULL)
);

COMMENT ON TABLE articles_contrats IS 'Table de liaison entre articles et contrats (normalisation 3NF)';

-- Créer des index pour améliorer les performances
CREATE INDEX IF NOT EXISTS idx_articles_statut ON articles(statut);
CREATE INDEX IF NOT EXISTS idx_contrats_client_id ON contrats(client_id);
CREATE INDEX IF NOT EXISTS idx_contrats_date_creation ON contrats(date_creation);
CREATE INDEX IF NOT EXISTS idx_articles_contrats_article_id ON articles_contrats(article_id);
CREATE INDEX IF NOT EXISTS idx_articles_contrats_contrat_id ON articles_contrats(contrat_id);

-- Afficher un message de confirmation
DO $$
BEGIN
    RAISE NOTICE 'Tables creees avec succes !';
    RAISE NOTICE 'Tables: clients, articles, contrats, articles_contrats';
END $$;

