# Amazon Crawler

Un crawler automatique qui récupère les informations des produits sur Amazon.fr en utilisant Crawl4AI.

## Prérequis

- Python 3.7 ou supérieur
-crawl4ai>=0.1.0

## Installation

1. Clonez ce dépôt ou téléchargez les fichiers
2. Installez les dépendances :
```bash
pip install -r requirements.txt
```

## Utilisation

Lancez simplement le script :
```bash
python amazon_scraper.py
```

Le crawler va automatiquement :
- Scanner toutes les catégories technologiques :
  - Informatique
  - High-Tech
  - Téléphones
  - TV & Vidéo
  - Audio & HiFi
- Récupérer les informations de tous les produits
- Sauvegarder les résultats dans des fichiers CSV

### Arrêt manuel

Vous pouvez arrêter le scraping à tout moment en appuyant sur Entrée dans la console. Le script terminera proprement l'extraction en cours et sauvegardera les résultats déjà collectés.

## Fonctionnalités

- Crawling automatique de toutes les catégories tech
- Extraction d'informations détaillées pour chaque produit :
  - Catégorie
  - ASIN (identifiant unique Amazon)
  - Titre
  - Marque
  - Prix
  - URL de l'image
  - Lien du produit
- Sauvegarde des résultats :
  - Un fichier CSV par catégorie
  - Un fichier CSV global avec tous les produits
- Statistiques automatiques :
  - Nombre total de produits
  - Répartition par catégorie
  - Marques les plus fréquentes

## Structure des fichiers

Les résultats sont sauvegardés dans le dossier `data/` :
- `amazon_tech_[categorie]_[timestamp].csv` : Résultats par catégorie
- `amazon_tech_all_categories_[timestamp].csv` : Tous les résultats

## Notes

- Le crawler parcourt automatiquement jusqu'à 10 pages par catégorie
- Une pause d'1 seconde entre chaque page évite de surcharger les serveurs
- Les fichiers sont horodatés pour éviter les écrasements
- Le script gère automatiquement les erreurs et les cas particuliers
