import streamlit as st
import openai
import gspread
from google.oauth2.service_account import Credentials
import json
from datetime import datetime

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="BienDit - Assistant IA",
    page_icon="🏠",
    layout="centered"
)

# --- STYLE CSS ---
st.markdown("""
<style>
    .stButton>button {
        width: 100%;
        background-color: #4F46E5;
        color: white;
        font-weight: bold;
        border-radius: 8px;
        padding: 0.75rem;
    }
    .stButton>button:hover {
        background-color: #4338ca;
        color: white;
    }
    h1 { color: #1e1b4b; }
</style>
""", unsafe_allow_html=True)

# --- CONNEXION GOOGLE SHEETS ---
@st.cache_resource
def get_google_sheet():
    # Vérifie si les secrets sont configurés
    if "gcp_service_account" not in st.secrets:
        st.error("⚠️ Les secrets Google ne sont pas configurés sur Streamlit Cloud.")
        return None

    try:
        # Récupère les infos du compte de service
        secrets = st.secrets["gcp_service_account"]
        
        # Définit les droits d'accès
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        
        # Authentification
        creds = Credentials.from_service_account_info(secrets, scopes=scope)
        client = gspread.authorize(creds)
        
        # Ouvre le fichier (Attention : le nom doit être EXACTEMENT celui de votre Sheet)
        return client.open("DB_BienDit_MVP").sheet1 
    except Exception as e:
        st.error(f"Erreur de connexion Google Sheets : {e}")
        return None

# --- LE PROMPT ---
SYSTEM_PROMPT = """
Tu es "BienDit", un assistant expert en copywriting immobilier.
RÈGLES :
1. Titre en MAJUSCULES (Type + Atout + Ville).
2. Style storytelling chaleureux.
3. Pas de clichés ("coup de coeur assuré" interdit).
4. Structure aérée.
"""

# --- INTERFACE ---
st.title("BienDit 🏠")
st.markdown("L'assistant de rédaction pour les agents exigeants.")

with st.form("generation_form"):
    col1, col2 = st.columns(2)
    with col1:
        type_bien = st.text_input("Type de bien", placeholder="Ex: T3")
        ville = st.text_input("Ville", placeholder="Ex: Lyon 6ème")
    with col2:
        surface = st.number_input("Surface (m²)", min_value=0, step=1)
        prix = st.text_input("Prix (Optionnel)")

    points_forts = st.text_area("Points Forts", placeholder="Ex: Lumineux, balcon, calme...", height=100)
    points_faibles = st.text_input("Points Faibles (Optionnel)")

    submitted = st.form_submit_button("Générer l'annonce ✨")

# --- LOGIQUE ---
if submitted:
    if not type_bien or not ville or not points_forts:
        st.warning("Merci de remplir le Type, la Ville et les Points Forts.")
    else:
        if "OPENAI_API_KEY" not in st.secrets:
            st.error("⚠️ Clé API OpenAI manquante dans les secrets.")
        else:
            with st.spinner("Rédaction en cours..."):
                try:
                    client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
                    prompt = f"Type: {type_bien}, Ville: {ville}, Surface: {surface}, Prix: {prix}, Forts: {points_forts}, Faibles: {points_faibles}"
                    
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": prompt}
                        ]
                    )
                    annonce = response.choices[0].message.content
                    
                    st.success("Annonce générée !")
                    st.text_area("Résultat", value=annonce, height=300)
                    
                    # Sauvegarde
                    sheet = get_google_sheet()
                    if sheet:
                        sheet.append_row([str(datetime.now()), type_bien, ville, surface, points_forts, annonce])
                        st.toast("Sauvegardé ✅")
                        
                except Exception as e:
                    st.error(f"Erreur : {e}")
