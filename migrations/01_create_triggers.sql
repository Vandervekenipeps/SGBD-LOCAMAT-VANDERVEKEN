-- Script SQL pour créer les triggers et contraintes supplémentaires
-- Ce script peut être exécuté après la création des tables par SQLAlchemy

-- Trigger pour valider le changement de statut : Un article ne peut passer à "Loué" que s'il est "Disponible"
-- Cette contrainte est également gérée dans la couche BLL, mais le trigger SQL offre une protection supplémentaire

CREATE OR REPLACE FUNCTION check_statut_loue()
RETURNS TRIGGER AS $$
BEGIN
    -- Si on essaie de mettre le statut à "Loué"
    IF NEW.statut = 'Loué' THEN
        -- Vérifier que l'ancien statut était "Disponible"
        IF OLD.statut != 'Disponible' THEN
            RAISE EXCEPTION 'Un article ne peut passer au statut "Loué" que s''il est actuellement "Disponible". Statut actuel : %', OLD.statut;
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Créer le trigger sur la table articles
DROP TRIGGER IF EXISTS trigger_check_statut_loue ON articles;
CREATE TRIGGER trigger_check_statut_loue
    BEFORE UPDATE OF statut ON articles
    FOR EACH ROW
    EXECUTE FUNCTION check_statut_loue();

-- Commentaire pour documenter le trigger
COMMENT ON FUNCTION check_statut_loue() IS 
'Valide que le changement de statut vers "Loué" est autorisé uniquement depuis "Disponible"';

