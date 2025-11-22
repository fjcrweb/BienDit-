import streamlit as st
import google.generativeai as genai
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="BienDit - Assistant IA", page_icon="🏠", layout="centered")

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
    if "gcp_service_account" not in st.secrets:
        st.error("⚠️ Secrets Google Sheets manquants.")
        return None
    try:
        secrets = st.secrets["gcp_service_account"]
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(secrets, scopes=scope)
        client = gspread.authorize(creds)
        return client.open("DB_BienDit_MVP").sheet1 
    except Exception as e:
        st.error(f"Erreur Sheets : {e}")
        return None

# --- LE PROMPT ---
SYSTEM_INSTRUCTION = """
Tu es "BienDit", un assistant expert en copywriting immobilier.
RÈGLES :
1. Titre en MAJUSCULES (Type + Atout + Ville).
2. Style storytelling chaleureux et vendeur.
3. Pas de clichés ("coup de coeur assuré" interdit).
4. Structure aérée avec des paragraphes clairs.
5. Réponds uniquement avec l'annonce (pas de phrase d'intro).
"""

# --- INTERFACE ---
st.title("BienDit 🏠")
st.markdown("L'assistant de rédaction propulsé par Gemini.")

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

# --- LOGIQUE GEMINI ---
if submitted:
    if not type_bien or not ville or not points_forts:
        st.warning("Merci de remplir le Type, la Ville et les Points Forts.")
    else:
        # Vérification de la clé API
        if "GOOGLE_API_KEY" not in st.secrets:
            st.error("⚠️ Clé API Gemini manquante dans les secrets.")
        else:
            with st.spinner("Rédaction en cours avec Gemini..."):
                try:
                    # 1. Configuration de Gemini
                    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
                    model = genai.GenerativeModel('gemini-1.5-flash') # Modèle rapide et gratuit
                    
                    # 2. Construction du prompt
                    full_prompt = f"""
                    {SYSTEM_INSTRUCTION}
                    ---
                    INFORMATIONS DU BIEN :
                    Type: {type_bien}
                    Ville: {ville}
                    Surface: {surface} m²
                    Prix: {prix}
                    Points Forts: {points_forts}
                    Points Faibles: {points_faibles}
                    """
                    
                    # 3. Génération
                    response = model.generate_content(full_prompt)
                    annonce = response.text
                    
                    # 4. Affichage
                    st.success("Annonce générée !")
                    st.text_area("Résultat", value=annonce, height=300)
                    
                    # 5. Sauvegarde Sheets
                    sheet = get_google_sheet()
                    if sheet:
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        sheet.append_row([timestamp, type_bien, ville, surface, points_forts, annonce])
                        st.toast("Sauvegardé ✅")
                        
                except Exception as e:
                    st.error(f"Erreur : {e}")
