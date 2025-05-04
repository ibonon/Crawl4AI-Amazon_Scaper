import asyncio
import csv
import json
import logging
from datetime import datetime
import os
import threading
from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CacheMode,
    CrawlerRunConfig,
    JsonCssExtractionStrategy
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class AmazonScraper:
    def __init__(self):
        self.browser_config = BrowserConfig(
            headless=True,
            verbose=True,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        self.stop_flag = threading.Event()
        
        # Schéma d'extraction amélioré
        self.schema = {
            "name": "Product",
            "baseSelector": "div[data-component-type='s-search-result']",
            "fields": [
                {
                    "name": "Nom du produit",
                    "selector": "h2 a span, div.a-section.a-spacing-none.a-spacing-top-small.s-title-instructions-style > a > h2",
                    "type": "text"
                },
                {
                    "name": "Lien",
                    "selector": "h2 a, div.a-section.a-spacing-none.a-spacing-top-small.s-title-instructions-style > a",
                    "type": "attribute",
                    "attribute": "href"
                },
                {
                    "name": "Prix",
                    "selector": "span.a-price > span.a-offscreen, span.a-price-whole, span.a-price-fraction, span.a-price-symbol",
                    "type": "text"
                },
                {
                    "name": "Note",
                    "selector": "span.a-icon-alt, i.a-icon-star",
                    "type": "text"
                },
                {
                    "name": "Nombre d'avis",
                    "selector": "span.a-size-base.s-underline-text, span.a-size-base",
                    "type": "text"
                }
            ]
        }

        # Toutes les catégories principales d'Amazon
        self.categories = {
            'Informatique': {
                'url': 'https://www.amazon.fr/s?i=computers&rh=n%3A340858031&fs=true',
                'subcategories': ['ordinateurs', 'composants', 'périphériques', 'stockage', 'logiciels']
            },
            'High-Tech': {
                'url': 'https://www.amazon.fr/s?i=electronics&rh=n%3A13921051&fs=true',
                'subcategories': ['smartphones', 'tablettes', 'accessoires', 'gadgets']
            },
            'Téléphones': {
                'url': 'https://www.amazon.fr/s?i=mobile&rh=n%3A218193031&fs=true',
                'subcategories': ['téléphones', 'accessoires', 'étuis', 'chargeurs']
            },
            'TV & Vidéo': {
                'url': 'https://www.amazon.fr/s?i=tv&rh=n%3A1055398&fs=true',
                'subcategories': ['téléviseurs', 'projecteurs', 'accessoires', 'home cinéma']
            },
            'Audio & HiFi': {
                'url': 'https://www.amazon.fr/s?i=hifi&rh=n%3A677338011&fs=true',
                'subcategories': ['enceintes', 'casques', 'amplificateurs', 'systèmes audio']
            },
            'Livres': {
                'url': 'https://www.amazon.fr/s?i=stripbooks&rh=n%3A301061&fs=true',
                'subcategories': ['romans', 'bd', 'manuels', 'jeunesse']
            },
            'Jeux vidéo': {
                'url': 'https://www.amazon.fr/s?i=videogames&rh=n%3A409488&fs=true',
                'subcategories': ['consoles', 'jeux', 'accessoires', 'manettes']
            },
            'Jouets': {
                'url': 'https://www.amazon.fr/s?i=toys&rh=n%3A548012&fs=true',
                'subcategories': ['jeux', 'poupées', 'figurines', 'jeux de société']
            },
            'Mode': {
                'url': 'https://www.amazon.fr/s?i=fashion&rh=n%3A197858031&fs=true',
                'subcategories': ['vêtements', 'chaussures', 'accessoires', 'bijoux']
            },
            'Maison': {
                'url': 'https://www.amazon.fr/s?i=garden&rh=n%3A197266031&fs=true',
                'subcategories': ['décoration', 'mobilier', 'cuisine', 'jardin']
            },
            'Beauté': {
                'url': 'https://www.amazon.fr/s?i=beauty&rh=n%3A197858031&fs=true',
                'subcategories': ['parfums', 'maquillage', 'soins', 'accessoires']
            },
            'Sports': {
                'url': 'https://www.amazon.fr/s?i=sports&rh=n%3A197858031&fs=true',
                'subcategories': ['fitness', 'vélos', 'randonnée', 'tennis']
            },
            'Auto': {
                'url': 'https://www.amazon.fr/s?i=automotive&rh=n%3A197858031&fs=true',
                'subcategories': ['pièces', 'accessoires', 'entretien', 'gps']
            },
            'Bébé': {
                'url': 'https://www.amazon.fr/s?i=baby&rh=n%3A197858031&fs=true',
                'subcategories': ['vêtements', 'jouets', 'puériculture', 'alimentation']
            },
            'Animalerie': {
                'url': 'https://www.amazon.fr/s?i=pets&rh=n%3A197858031&fs=true',
                'subcategories': ['alimentation', 'accessoires', 'soins', 'jouets']
            }
        }

    def clean_text(self, text):
        """Nettoie le texte des caractères spéciaux et espaces superflus"""
        if not text:
            return "N/A"
        return text.strip()

    async def scrape_category(self, crawler, name, category_info):
        logging.info(f"Scraping catégorie: {name}")
        all_products = []
        seen_products = set()
        max_retries = 3
        retry_delay = 5  # secondes
        run_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            extraction_strategy=JsonCssExtractionStrategy(self.schema)
        )
        max_pages = 10  # Nombre de pages à scraper simultanément (modifiable)
        async def scrape_page(page):
            paged_url = f"{category_info['url']}&page={page}"
            for retry in range(max_retries):
                try:
                    result = await crawler.arun(url=paged_url, config=run_config)
                    if not result.success:
                        logging.error(f"Erreur page {page} : {result.error_message}")
                        if retry < max_retries - 1:
                            await asyncio.sleep(retry_delay)
                            continue
                        return []
                    data = json.loads(result.extracted_content)
                    if not data:
                        return []
                    page_products = []
                    for item in data:
                        title = item.get("Nom du produit", "").lower()
                        if not title:
                            continue
                        lien = item.get("Lien", "")
                        if lien and not lien.startswith("http"):
                            lien = "https://www.amazon.fr" + lien
                        prix = item.get("Prix", "")
                        if isinstance(prix, list):
                            prix = " ".join(prix)
                        product_data = {
                            "Catégorie": name,
                            "Nom du produit": self.clean_text(item.get("Nom du produit", "N/A")),
                            "Prix": self.clean_text(prix),
                            "Note": self.clean_text(item.get("Note", "N/A")),
                            "Nombre d'avis": self.clean_text(item.get("Nombre d'avis", "N/A")),
                            "Lien": lien
                        }
                        product_key = f"{product_data['Nom du produit']}_{product_data['Prix']}"
                        if product_key not in seen_products:
                            seen_products.add(product_key)
                            page_products.append(product_data)
                    logging.info(f"{len(page_products)} nouveaux produits trouvés sur la page {page}")
                    return page_products
                except Exception as e:
                    logging.error(f"Exception page {page} (tentative {retry + 1}/{max_retries}): {e}")
                    if retry < max_retries - 1:
                        await asyncio.sleep(retry_delay)
                        continue
                    return []
        page = 1
        while not self.stop_flag.is_set():
            tasks = []
            for i in range(max_pages):
                if self.stop_flag.is_set():
                    break
                tasks.append(scrape_page(page + i))
            if not tasks:
                break
            results = await asyncio.gather(*tasks)
            batch_products = [prod for sublist in results for prod in sublist]
            if not batch_products:
                break
            all_products.extend(batch_products)
            page += max_pages
            await asyncio.sleep(2)
        logging.info(f"Arrêt manuel détecté pour la catégorie {name}.")
        return all_products

    def save_to_csv(self, data, filename):
        if not data:
            logging.warning("Aucun produit à sauvegarder.")
            return

        with open(filename, mode="w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "Catégorie", "Nom du produit", "Prix", "Note", "Nombre d'avis", "Lien"
            ])
            writer.writeheader()
            writer.writerows(data)
        logging.info(f"Données enregistrées dans : {filename}")

    async def start(self, selected_category=None):
        all_data = []
        os.makedirs("data", exist_ok=True)
        categories = {selected_category: self.categories[selected_category]} if selected_category else self.categories
        def wait_for_stop():
            input("Appuyez sur Entrée à tout moment pour arrêter le scraping...\n")
            self.stop_flag.set()
        stop_thread = threading.Thread(target=wait_for_stop, daemon=True)
        stop_thread.start()
        try:
            async with AsyncWebCrawler(config=self.browser_config) as crawler:
                scrape_tasks = []
                for name, info in categories.items():
                    if self.stop_flag.is_set():
                        logging.info("Arrêt manuel demandé. Fin du scraping.")
                        break
                    scrape_tasks.append(self.scrape_category(crawler, name, info))
                if scrape_tasks:
                    results = await asyncio.gather(*scrape_tasks)
                    for idx, produits in enumerate(results):
                        name = list(categories.keys())[idx]
                        info = categories[name]
                        if produits:
                            all_data.extend(produits)
                            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                            filename = f"data/amazon_{name.lower().replace(' ', '_')}_{ts}.csv"
                            self.save_to_csv(produits, filename)
        except Exception as e:
                        logging.error(f"Erreur lors du scraping de la catégorie {name}: {e}")
        except Exception as e:
            logging.error(f"Erreur critique: {e}")
            return
        if all_data:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"data/amazon_all_categories_{ts}.csv"
            self.save_to_csv(all_data, filename)
            logging.info("Statistiques:")
            logging.info(f"Total produits récupérés: {len(all_data)}")
            logging.info("Répartition par catégorie:")
            categories_count = {}
            for item in all_data:
                categories_count[item["Catégorie"]] = categories_count.get(item["Catégorie"], 0) + 1
            for cat, count in categories_count.items():
                logging.info(f"{cat}: {count} produits")

async def main():
    scraper = AmazonScraper()
    await scraper.start()

if __name__ == "__main__":
    asyncio.run(main())
