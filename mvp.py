import streamlit as st
import random
from datetime import datetime, timedelta
from scrape import main as website_crawl_main
from ai import main as ai_main
from chek import main as chek_main

class CanadaVisaAIApp:
    def __init__(self):
        self.setup_page()
        self.hide_elements()
        self.apply_styles()

    def setup_page(self):
        st.set_page_config(layout='wide', page_title='ImmCAI', page_icon='📄')

    def hide_elements(self):
        hide_st_style = """
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        </style>
        """
        st.markdown(hide_st_style, unsafe_allow_html=True)

    def apply_styles(self):
        page_style = """
        <style>
        .big-font {
            font-size: 30px !important;
            font-weight: bold;
        }
        .medium-font {
            font-size: 20px !important;
        }
        .centered {
            text-align: center;
        }
        .service {
            background-color: #6e166d;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        .service h3 {
            color: #fff;
            margin-bottom: 10px;
        }
        .service p {
            color: #fff;
        }
        </style>
        """
        st.markdown(page_style, unsafe_allow_html=True)

    def predict_immigration_success(self, age, education, language_score, work_experience):
        # Évaluation de l'âge (basée sur le système de points d'Express Entry)
        if 18 <= age <= 35:
            age_score = 1
        elif 36 <= age <= 47:
            age_score = 1 - (age - 35) * 0.05  # Perte de 5% par an après 35 ans
        else:
            age_score = 0
        
        # Évaluation de l'éducation
        edu_scores = {
            "Secondaire": 0.4,
            "Baccalauréat": 0.5,
            "Master": 0.7,
            "Doctorat": 1
        }
        education_score = edu_scores[education]
        
        # Évaluation des compétences linguistiques (basée sur IELTS ou équivalent)
        language_score = min(language_score / 9, 1)  # 9 est le score maximum pour IELTS
        
        # Évaluation de l'expérience professionnelle
        experience_score = min(work_experience / 6, 1)  # 6 ans ou plus donne le maximum de points
        
        # Calcul de la moyenne pondérée
        weights = [0.25, 0.3, 0.3, 0.25]  # Poids pour chaque facteur
        total_score = (
            age_score * weights[0] +
            education_score * weights[1] +
            language_score * weights[2] +
            experience_score * weights[3]
        )
        
        # Ajout d'un facteur aléatoire (±5%) pour simuler d'autres facteurs
        random_factor = random.uniform(-0.05, 0.05)
        
        # Calcul de la probabilité finale
        probability = max(0, min(1, total_score + random_factor))
        
        return probability

    def check_documents(self, documents):
        required_docs = {"passeport", "photos", "relevé_bancaire", "lettre_invitation", "preuve_linguistique"}
        missing_docs = required_docs - set(documents)
        return list(missing_docs)

    def display_tabs(self):
        st.title("ImmCAI: Assistant d'Immigration Canada powered by AI")

        tab1, tab2, tab3, tab4, tab5 = st.tabs(["Chatbot", "Analyse Prédictive", "Vérification des Documents", "Scrapping", "ECAS Status Checker"])

        with tab1:
            ai_main()

        with tab2:
            self.display_predictive_analysis()

        with tab3:
            self.display_document_verification()

        with tab4:
            website_crawl_main()

        with tab5:
            chek_main()

    def display_predictive_analysis(self):
        st.header("Analyse Prédictive")
        col1, col2 = st.columns(2)

        with col1:
            age = st.slider("Âge", 18, 60, 30)
            education = st.selectbox("Niveau d'éducation", ["Secondaire", "Baccalauréat", "Master", "Doctorat"])
            language_score = st.slider("Score linguistique (IELTS ou équivalent, 0-9)", 0.0, 9.0, 6.0, 0.5)
            work_experience = st.slider("Années d'expérience professionnelle pertinente", 0, 15, 3)
            probability = self.predict_immigration_success(age, education, language_score, work_experience)
        with col2:
            st.subheader("Probabilité d'éligibilité:")
            st.markdown(f"- Vos chances estimées de succès pour l'immigration au Canada sont de {probability:.2%}")

            # Ajout de commentaires basés sur la probabilité
            if probability < 0.3:
                st.error("- Vos chances semblent limitées. Vous pourriez envisager d'améliorer vos qualifications ou d'explorer d'autres options d'immigration.")
            elif 0.3 <= probability < 0.6:
                st.markdown("- Vos chances sont moyennes. Il pourrait être utile d'améliorer certains aspects de votre profil pour augmenter vos chances.")
            elif 0.6 <= probability < 0.8:
                st.markdown("- Vos chances semblent bonnes. Continuez à maintenir ou à améliorer votre profil.")
            else:
                st.success("- Vos chances sont super. Continuez à améliorer votre profil pour augmenter vos chances.")

    def display_document_verification(self):
        st.header("Vérification des Documents")
        docs = st.multiselect("Sélectionnez les documents que vous avez préparés:", 
                              ["passeport", "photos", "relevé_bancaire", "lettre_invitation", "preuve_linguistique"])
        if st.button("Vérifier mes documents"):
            missing = self.check_documents(docs)
            if missing:
                st.write(f"Documents manquants : {', '.join(missing)}")
            else:
                st.write("Tous les documents requis sont présents!")

    def display_sidebar(self):
        st.sidebar.title("À propos")
        st.sidebar.info("Ceci est un MVP pour un assistant d'immigration utilisant l'IA.")

    def run(self):
        self.display_tabs()
        self.display_sidebar()

class CanadaVisaAISlideshow:
    def __init__(self):
        self.slides = [
            {
                "title": "Introduction à CanadaVisa AI",
                "content": self.introduction_slide
            },
            {
                "title": "Le Problème que Nous Résolvons",
                "content": self.problem_slide
            },
            {
                "title": "Notre Solution",
                "content": self.solution_slide
            },
            {
                "title": "Avantages",
                "content": self.benefits_slide
            },
            {
                "title": "Modèles de Partenariat",
                "content": self.partnership_slide
            },
            {
                "title": "Prochaines Étapes",
                "content": self.next_steps_slide
            }
        ]
        if 'current_slide' not in st.session_state:
            st.session_state.current_slide = 0

    def display_navigation(self):
        col1, col2, col3 = st.columns([1, 3, 1])
        with col1:
            if st.button("Précédent") and st.session_state.current_slide > 0:
                st.session_state.current_slide -= 1
        with col3:
            if st.button("Suivant") and st.session_state.current_slide < len(self.slides) - 1:
                st.session_state.current_slide += 1

    def display_current_slide(self):
        st.header(self.slides[st.session_state.current_slide]["title"])
        self.slides[st.session_state.current_slide]["content"]()

    def introduction_slide(self):
        st.write("CanadaVisa AI est une start-up tunisienne innovante qui utilise l'intelligence artificielle pour simplifier et optimiser le processus d'immigration au Canada.")
        st.info("**Notre Mission**: Démocratiser l'accès aux opportunités d'immigration canadienne grâce à une technologie innovante, rendant le processus plus efficace, précis et accessible à tous.")

    def problem_slide(self):
        st.write("Défis des Services d'Immigration Traditionnels:")
        st.markdown("""
        - Processus de demande chronophages
        - Conseils et informations incohérents
        - Disponibilité limitée de consultation d'experts
        - Coûts élevés pour des services personnalisés
        - Difficulté à évaluer l'éligibilité avec précision
        """)
        st.error('"Le processus d\'immigration canadienne est complexe et souvent accablant pour les candidats. Les méthodes traditionnelles peinent à suivre la demande et les réglementations en constante évolution."')

    def solution_slide(self):
        st.write("La Plateforme CanadaVisa AI")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Chatbot IA")
            st.write("Réponses instantanées 24/7 aux questions courantes")
            st.subheader("Analyse Prédictive")
            st.write("Évaluations d'éligibilité basées sur             les données")
        
        with col2:
            st.subheader("Vérification de Documents")
            st.write("Examen initial automatisé et signalement d'erreurs")
            st.subheader("Feuilles de Route Personnalisées")
            st.write("Plans d'immigration sur mesure pour chaque candidat")

    def benefits_slide(self):
        st.write("Avantages du Partenariat")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Efficacité")
            st.write("Gérez plus de dossiers sans augmenter le personnel")
            st.subheader("Croissance des Revenus")
            st.write("Accédez à de nouvelles sources de revenus")
        
        with col2:
            st.subheader("Satisfaction Client")
            st.write("Améliorez les temps de réponse et la précision")
            st.subheader("Avantage Concurrentiel")
            st.write("Restez en tête avec une technologie de pointe")

    def partnership_slide(self):
        st.write("Options de Partenariat Flexibles:")
        st.markdown("""
        - **Solution en Marque Blanche :** Intégrez notre technologie sous votre marque
        - **Partenariat Co-Marqué :** Proposez les services CanadaVisa AI aux côtés de vos offres traditionnelles
        - **Programme de Parrainage :** Gagnez des commissions en référant des clients à notre plateforme
        - **Modèle Hybride :** Personnalisez un partenariat adapté à vos besoins uniques
        """)
        st.info('"Nous nous engageons à trouver le modèle de collaboration parfait qui s\'aligne sur les objectifs et les valeurs de votre agence."')

    def next_steps_slide(self):
        st.write("Révolutionnons Ensemble l'Immigration")
        st.markdown("""
        1. Planifiez une démonstration de nos outils IA
        2. Discutez des options de personnalisation pour votre agence
        3. Développez un plan d'intégration sur mesure
        4. Lancez un programme pilote
        """)
        st.success("Prêt à faire passer votre agence au niveau supérieur ?")
        if st.button("Contactez-Nous Aujourd'hui"):
            st.markdown("""
             - Email: abraich.jobs+canadavisai@gmail.com
             - Téléphone: tel:+21655000000
            """)

    def run(self):
        self.display_navigation()
        self.display_current_slide()

def main():
    app = CanadaVisaAIApp()
    slideshow = CanadaVisaAISlideshow()
    with st.expander("Présentation"):
        slideshow.run()
    app.run()

if __name__ == "__main__":
    main()

