import streamlit as st
import trafilatura
from trafilatura.spider import focused_crawler
import google.generativeai as genai
from typing import List, Dict
import os
import hashlib
import random
import time
from playwright.sync_api import sync_playwright
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

# Constants
KEYS = ["AIzaSyBkTJsctYOkljL0tx-6Y8NwYCaSz-r0XmU", "AIzaSyDbzt8ZGVd3P15MMuIUh8wz1lzT5jRLWlc"]
MODEL_NAME = "gemini-1.5-flash"
UPLOAD_DIR = "uploads"
MAX_URLS = 5
MAX_WORKERS = 4

# Configure genai
genai.configure(api_key=random.choice(KEYS))  # Use a random key for better load distribution


class WebScraper:
    def __init__(self, url, cookies=None):
        self.url = url
        self.cookies = cookies or []
        self.extracted_text = ""
        self.metadata = {}
        self.crawled_links = []
        self.all_text = ""

    def scrape(self):
        try:
            downloaded = trafilatura.fetch_url(self.url)
            self.extracted_text = trafilatura.extract(downloaded)
            self.all_text += self.extracted_text
        except Exception as e:
            #st.error(f"An error occurred during scraping with trafilatura: {e}")
            self._scrape_with_playwright()

    def _scrape_with_playwright(self):
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=False)
                context = browser.new_context()
                if self.cookies:
                    context.add_cookies(self.cookies)
                page = context.new_page()
                page.goto(self.url)
                page.wait_for_selector('.pb-0 > div:nth-child(1) > h1:nth-child(1)')
                content = page.content()
                # find all links on the page
                links = page.query_selector_all('a')
                for link in links:
                    if link.get_attribute('href'):
                        self.crawled_links.append(self.url + link.get_attribute('href'))
                browser.close()

            self.extracted_text = trafilatura.extract(content)
            self.all_text += self.extracted_text 
        except Exception as e:
            st.error(f"An error occurred during scraping with Playwright: {e}")

    def crawl(self, max_urls=MAX_URLS):
        try:
            with st.spinner('Crawling in progress...'):
                progress_bar = st.progress(0)
                #self.crawled_links, _ = focused_crawler(self.url, max_seen_urls=max_urls)
                
                def process_link(link):
                    try:
                        with sync_playwright() as p:
                            browser = p.chromium.launch()
                            context = browser.new_context()
                            if self.cookies:
                                context.add_cookies(self.cookies)
                            page = context.new_page()
                            page.goto(link)
                            page.wait_for_selector('.pb-0 > div:nth-child(1) > h1:nth-child(1)')

                            content = page.content()
                            browser.close()
                        return trafilatura.extract(content)
                    except Exception as e:
                        st.warning(f"Error processing {link}: {e}")
                        return ""

                with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                    future_to_link = {executor.submit(process_link, link): link for link in self.crawled_links[:5] }
                    for i, future in enumerate(as_completed(future_to_link)):
                        self.all_text += future.result()
                        progress_bar.progress((i + 1) / len(self.crawled_links))

            st.success('Crawling completed!')
        except Exception as e:
            st.error(f"An error occurred during crawling: {e}")


class CanadaVisaAIApp:
    def __init__(self, model_name=MODEL_NAME):
        self.model_name = model_name
        self.generation_config = {
            "temperature": 0.7,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 4096,
        }

    def generate_response(self, context: str, num_urls: int) -> str:
        model = genai.GenerativeModel(model_name=self.model_name, generation_config=self.generation_config)
        
        prompt = f"""
        Vous êtes un expert en analyse de données, en immigration, et en génération de rapports. Vous avez reçu le contenu de {num_urls} pages web. Votre tâche est d'analyser ce contenu et de fournir un rapport complet.

        Contexte (extrait des pages web récupérées):
        {context}

        Veuillez générer un rapport avec la structure suivante :

        1. Résumé:
        - Fournissez un aperçu des principaux sujets abordés dans le contenu récupéré.
        - Identifiez et expliquez les thèmes, tendances ou motifs clés que vous observez.
        - Mettez en évidence les points de données, statistiques ou citations significatifs.
        - Offrez des insights ou des conclusions basés sur le contenu analysé.
        - Fournissez des commentaires ou un contexte supplémentaire.
        - Statistiques ou liens vers des documents additionnels
        - lien vers formulaire, demandes etc
        2. Tableau des principaux sujets et informations clés ainsi que des statistiques, et analyse , liens en tant qu'expert en immigration canada au format markdown :
        3. Sortie JSON :
        Générez un objet JSON avec la structure suivante :
        {{
          "sujets_principaux": ["sujet1", "sujet2", "sujet3"],
          "thèmes_clés": [
            {{
              "thème": "Thème 1",
              "description": "Brève description du thème 1",
              "sujets_connexes": ["sujet1", "sujet2"]
            }},
            // ... plus de thèmes
          ],
          "points_de_données_significatifs": [
            {{
              "point_de_donnée": "Point de donnée ou statistique spécifique",
              "contexte": "Brève explication ou contexte",
              "source": "Source du point de donnée (si disponible)"
            }},
            // ... plus de points de données
          ],
          "insights": [
            {{
              "insight": "Insight ou conclusion clé",
              "explication": "Brève explication ou preuve à l'appui"
            }},
            // ... plus dinfos max que possible
          ]
        }}

        Assurez-vous que votre JSON est valide et correctement formaté.
        Commencez votre rapport par "Résumé:" et terminez-le par "Sortie JSON:"
        """
        
        return model.generate_content(prompt).text


def save_extracted_text(text, filename):
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(UPLOAD_DIR, filename)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(text)
    return file_path

def main():
    url = st.text_input("Enter the URL of the website:", value="https://visa.vfsglobal.com/tun/fr/can")

    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    if st.button("Scrape, Crawl, and Analyze"):
        if url:
            scraper = WebScraper(url)
            scraper.scrape()
            scraper.crawl(max_urls=MAX_URLS)
            
            if scraper.crawled_links:
                st.subheader("Crawled Links:")
                st.json(scraper.crawled_links)

            file_name = f"{hashlib.md5(url.encode()).hexdigest()}.txt"
            file_path = save_extracted_text(scraper.all_text, file_name)
            st.success(f"Extracted text saved to: {file_path}")

            canada_visa_ai = CanadaVisaAIApp()
            response = canada_visa_ai.generate_response(scraper.all_text + str(scraper.crawled_links), len(scraper.crawled_links) + 1)

            st.markdown("<style> pre {white-space: pre-wrap;}</style>", unsafe_allow_html=True)

            parts = response.split('```json', 1)
            
            if len(parts) == 2:
                summary_part, json_part = parts
                st.write(summary_part.strip())
                
                try:
                    json_data = json.loads(json_part.strip().rstrip('`'))
                    st.json(json_data)
                except json.JSONDecodeError:
                    st.error("Failed to parse JSON. Raw output:")
                    st.code(json_part.strip(), language='json')
            else:
                st.write(response)

            st.session_state.chat_history.append({"role": "user", "content": "Generate comprehensive report"})
            st.session_state.chat_history.append({"role": "model", "content": response})

        else:
            st.warning("Please enter a valid URL.")

if __name__ == "__main__":
    main()
