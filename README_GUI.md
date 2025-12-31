# Interface Graphique LOCA-MAT

## Lancement

Pour lancer l'interface graphique Tkinter :

```bash
python main_gui.py
```

Pour lancer l'interface console (version originale) :

```bash
python main.py
```

## Structure

L'interface graphique est séparée dans le dossier `ui_gui/` pour ne pas interférer avec la version console :

```
ui/          # Interface console (inchangée)
ui_gui/      # Interface graphique (nouvelle)
  ├── main_window.py           # Fenêtre principale
  ├── gestion_parc_gui.py      # Gestion du parc
  ├── gestion_clients_gui.py    # Gestion des clients
  ├── creation_location_gui.py  # Création de location
  ├── restitution_gui.py         # Restitution d'article
  └── tableau_bord_gui.py       # Tableau de bord
```

## Fonctionnalités

L'interface graphique offre les mêmes fonctionnalités que la version console :

- ✅ **Tableau de Bord** : Top 5, CA 30 jours, alertes retards
- ✅ **Gestion du Parc** : Liste, ajout, modification statut, suppression
- ✅ **Gestion des Clients** : Liste, ajout
- ✅ **Création de Location** : Sélection client/articles, calcul prix, validation transactionnelle
- ✅ **Restitution** : Liste contrats en cours, sélection article à restituer

## Architecture

L'interface graphique respecte la même architecture 3-tier :

- **DAL** : Réutilisée (aucun changement)
- **BLL** : Réutilisée (aucun changement)
- **UI** : Nouvelle couche graphique (Tkinter)

Toute la logique métier reste dans la couche BLL, aucune requête SQL dans l'interface graphique.

