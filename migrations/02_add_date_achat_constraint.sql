-- Migration : Ajout de la contrainte CHECK pour la date d'achat
-- La date d'achat ne peut pas être dans le futur

-- Ajouter la contrainte CHECK sur la date d'achat
ALTER TABLE articles 
ADD CONSTRAINT check_date_achat_passee 
CHECK (date_achat <= CURRENT_DATE);

COMMENT ON CONSTRAINT check_date_achat_passee ON articles IS 
'Contrainte garantissant que la date d''achat ne peut pas être dans le futur';

-- Afficher un message de confirmation
DO $$
BEGIN
    RAISE NOTICE 'Contrainte check_date_achat_passee ajoutee avec succes !';
END $$;

