# app.py
import streamlit as st
import os
import io
import html     # For html.escape
import markdown # For Markdown conversion
from datetime import datetime # For HTML filename/info
from dotenv import load_dotenv # Optional: for local .env loading

# Importer les classes logiques et le gestionnaire de conversation
# Assurez-vous que ces fichiers sont présents et corrects
try:
    from expert_logic import ExpertAdvisor, ExpertProfileManager
    from conversation_manager import ConversationManager
except ImportError as e:
    st.error(f"Erreur d'importation des modules locaux: {e}")
    st.error("Assurez-vous que les fichiers 'expert_logic.py' et 'conversation_manager.py' existent dans le même dossier.")
    st.stop()


# --- Fonction pour charger le CSS local (utilisée avant et après login) ---
def local_css(file_name):
    """Charge les styles CSS depuis un fichier local."""
    try:
        css_path = os.path.join(os.path.dirname(__file__), file_name)
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning(f"Fichier CSS '{file_name}' non trouvé dans {os.path.dirname(__file__)}.")
    except Exception as e:
        st.error(f"Erreur lors du chargement du CSS '{file_name}': {e}")

# --- Helper Function pour lire le CSS pour l'intégration HTML (utilisée plus tard) ---
@st.cache_data # Mise en cache pour ne pas lire le fichier à chaque interaction
def load_css_content(file_name):
    """Charge le contenu brut d'un fichier CSS."""
    try:
        css_path = os.path.join(os.path.dirname(__file__), file_name)
        with open(css_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        st.warning(f"Fichier CSS '{file_name}' non trouvé pour l'intégration HTML.")
        return "/* CSS non trouvé */"
    except Exception as e:
        st.error(f"Erreur lors de la lecture du CSS '{file_name}' pour l'intégration : {e}")
        return f"/* Erreur lecture CSS: {e} */"

# --- Fonction helper pour convertir image en base64 ---
def get_image_base64(image_path):
    """Convertit une image en base64 pour l'incorporation HTML."""
    import base64
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except Exception as e:
        st.error(f"Erreur lors de la lecture de l'image: {e}")
        return ""

# --- Fonction de vérification du mot de passe ET affichage page d'accueil/login ---
def display_login_or_app():
    """
    Affiche la page d'accueil statique et le formulaire de connexion si non connecté.
    Retourne True si l'utilisateur EST connecté (et l'application principale doit s'afficher),
    Retourne False si l'utilisateur N'EST PAS connecté (et le script doit s'arrêter).
    """

    # Initialiser l'état de connexion s'il n'existe pas
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    # Si déjà connecté, retourner True pour afficher l'app principale
    if st.session_state.logged_in:
        return True

    # --- Si non connecté : Afficher la page d'accueil STATIQUE et le LOGIN ---

    # Configuration de la page
    st.set_page_config(
        page_title="Connexion - Constructo AI",
        page_icon="🏗️",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    local_css("style.css") # Charger CSS

    # --- Créer les colonnes pour centrer le contenu statique ---
    _ , center_col, _ = st.columns([0.5, 3, 0.5], gap="large") # Ajustez les poids si nécessaire

    with center_col: # Tout le contenu statique va dans cette colonne centrale
        # >>>>> CONTENU STATIQUE DE LA PAGE D'ACCUEIL (AVANT LOGIN) 

        # --- AJOUT DU LOGO CENTRÉ ---
        try:
            logo_path = os.path.join(os.path.dirname(__file__), "assets", "logo.png")
            if os.path.exists(logo_path):
                # Forcer le centrage avec CSS inline et base64
                st.markdown(
                    """
                    <div style='display: flex; justify-content: center; align-items: center; width: 100%;'>
                        <img src='data:image/png;base64,{}' style='width: 200px; height: auto;'>
                    </div>
                    """.format(get_image_base64(logo_path)),
                    unsafe_allow_html=True
                )
            else:
                st.warning("Logo 'assets/logo.png' non trouvé.")
        except Exception as e:
            st.error(f"Erreur logo: {e}")
        
        # Espace après le logo
        st.markdown("<br>", unsafe_allow_html=True)
        # --- FIN AJOUT DU LOGO ---

        # --- Texte principal centré ---
        st.markdown("""
            <div style='text-align: center;'>
                <h3>Constructo AI - La plateforme intelligente Open Source qui révolutionne vos projets de construction au Québec.</h3>
                <p>Bénéficiez d'estimations précises, d'un suivi intelligent et d'une conformité réglementaire garantie grâce à notre technologie d'IA avancée.</p>
            </div>
        """, unsafe_allow_html=True)
        # --- FIN MODIFICATION ---

        st.divider()
        st.markdown("<h2 style='text-align: center;'>Notre mission</h2>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center; font-weight: normal;'>Révolutionner l'industrie de la construction</h3>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: var(--text-color-light);'>Notre objectif est de fournir des outils intelligents et précis pour optimiser vos projets de construction</p>", unsafe_allow_html=True)
        st.markdown(" ")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("#### ⚡ Innovation IA")
            st.markdown("Utilisation de l'Intelligence Artificielle pour fournir des estimations et des recommandations pertinentes.")
        with col2:
            st.markdown("#### 📄 Expertise Construction")
            st.markdown("Une équipe passionnée avec plus de 20 ans d'expérience dans le secteur de la construction au Québec.")
        with col3:
            st.markdown("#### 🛡️ Conformité Réglementaire")
            st.markdown("Conformité stricte aux normes et règles de la construction au Québec.")
        st.markdown(" ")

        # --- Section Solutions IA Clés ---
        st.divider()
        st.markdown("<h2 style='text-align: center;'>Nos Solutions IA Clés</h2>", unsafe_allow_html=True)
        st.markdown(" ") # Espace

        feat_col1, feat_col2, feat_col3, feat_col4 = st.columns(4, gap="medium")
        with feat_col1:
            st.markdown("### 🚀 TakeOff AI")
            st.markdown("Automatisation du calcul des quantités et de l'estimation à l'aide d'une IA avancée pour analyser les plans et les documents de construction.")
        with feat_col2:
            st.markdown("### 📊 Project Manager AI")
            st.markdown("Système de gestion de projet alimenté par l'IA qui prédit les retards, optimise les calendriers et gère les ressources de manière efficace.")
        with feat_col3:
            st.markdown("### 📦 Inventory AI")
            st.markdown("Système intelligent de gestion des stocks avec commandes prédictives et capacités de suivi en temps réel.")
        with feat_col4:
            st.markdown("### 📝 Notes AI")
            st.markdown("Système intelligent de prise de notes qui organise les observations sur le site, les rapports de sécurité et la documentation du projet.")
        st.markdown(" ") # Espace
        # --- FIN Section Solutions IA ---


        # --- Section Fonctionnalités Détaillées ---
        st.divider()
        st.markdown("<p style='text-align: center; text-transform: uppercase; color: var(--text-color-light);'>Fonctionnalités Détaillées</p>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center;'>La plateforme intelligente pour la construction au Québec</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: var(--text-color-light);'>Gagnez du temps et réduisez vos coûts grâce à notre IA conçue pour la construction au Québec. Une plateforme complète pour estimer et optimiser vos projets.</p>", unsafe_allow_html=True)
        st.markdown(" ")
        fcol1, fcol2, fcol3 = st.columns(3)
        with fcol1:
            st.markdown("#### 🧑‍🤝‍🧑 Espaces de travail collaboratif")
            st.markdown("Collaborez efficacement avec vos équipes, partagez et gérez vos devis en un seul endroit.")
        with fcol2:
            st.markdown("#### 💡 AI Estimations")
            st.markdown("Obtenez des estimations de coûts en quelques secondes sur la base des données actuelles du marché.")
        with fcol3:
            st.markdown("#### 💬 Assistant de construction")
            st.markdown("Un assistant IA spécialisé dans la réponse à vos questions techniques et réglementaires en temps réel.")
        st.markdown(" ")
        fcol4, fcol5, fcol6 = st.columns(3)
        with fcol4:
            st.markdown("#### ✅ Conformité RBQ")
            st.markdown("Assurez la conformité de vos projets aux normes québécoises grâce à notre vérification automatique.")
        with fcol5:
            st.markdown("#### 📖 Documentation technique")
            st.markdown("Base de connaissances complète sur les normes et règlements de construction du Québec.")
        with fcol6:
            st.markdown("#### 💰 Analyse financière")
            st.markdown("Outils d'analyse et d'optimisation des coûts basés sur les données actuelles du marché québécois.")
        st.markdown(" ")
        fcol7, fcol8, fcol9 = st.columns(3)
        with fcol7:
            st.markdown("#### ⏱️ Mises à jour quotidiennes")
            st.markdown("Mises à jour quotidiennes pour mieux estimer vos projets, vos équipes et les changements réglementaires.")
        with fcol8:
            st.markdown("#### 📄 Exportation facile")
            st.markdown("Exportez vos devis au format PDF en un seul clic.")
        with fcol9:
            st.markdown("#### 📈 Analyse")
            st.markdown("Analysez vos devis et plans tout au long du processus de construction (fichiers Excel et PDF).")

        # --- SECTION Conformité et réglementation ---
        st.divider()
        st.markdown("<h2 style='text-align: center;'>Conformité et réglementation</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: var(--text-color-light);'>Constructo AI se conforme aux principales organisations du secteur de la construction au Québec</p>", unsafe_allow_html=True)
        st.markdown(" ")

        # Créer 3 lignes de 2 colonnes pour les 6 logos/textes
        reg_col1, reg_col2 = st.columns(2, gap="medium")
        with reg_col1:
            with st.container(): # Utiliser st.container pour potentiellement styler comme une carte
                 st.markdown("<p style='text-align: center; font-weight: 500;'>🏢 Régie du bâtiment du Québec (RBQ)</p>", unsafe_allow_html=True)
        with reg_col2:
            with st.container():
                 st.markdown("<p style='text-align: center; font-weight: 500;'>🏢 APCHQ</p>", unsafe_allow_html=True)

        st.markdown(" ") # Espace vertical

        reg_col3, reg_col4 = st.columns(2, gap="medium")
        with reg_col3:
            with st.container():
                 st.markdown("<p style='text-align: center; font-weight: 500;'>🏢 ACQ</p>", unsafe_allow_html=True)
        with reg_col4:
            with st.container():
                 st.markdown("<p style='text-align: center; font-weight: 500;'>📄 Commission de la construction du Québec</p>", unsafe_allow_html=True)

        st.markdown(" ") # Espace vertical

        reg_col5, reg_col6 = st.columns(2, gap="medium")
        with reg_col5:
            with st.container():
                 st.markdown("<p style='text-align: center; font-weight: 500;'>🎖️ Corporation des maîtres électriciens du Québec</p>", unsafe_allow_html=True)
        with reg_col6:
            with st.container():
                 st.markdown("<p style='text-align: center; font-weight: 500;'>🎖️ Corporation des maîtres mécaniciens en tuyauterie du Québec</p>", unsafe_allow_html=True)
        # --- FIN SECTION Conformité ---

        # --- NOUVELLE SECTION PAIEMENT ---
        st.divider()
        st.markdown("<h2 style='text-align: center;'>Constructo AI évolue : Fini les abonnements mensuels !</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center;'>Nous sommes heureux de vous annoncer que Constructo AI passe à un système de paiement à l'utilisation (pay as you go).</p>", unsafe_allow_html=True)
        st.markdown(" ") # Espace
        st.markdown("**Ce que cela signifie pour vous :**")
        st.markdown("""
        - Plus de flexibilité : payez uniquement ce que vous utilisez
        - Meilleure maîtrise de vos coûts
        - Économisez jusqu'à 50% sur vos factures en ne payant que pour vos besoins réels
        - Fini les frais fixes mensuels pour des fonctionnalités inutilisées
        """)
        st.markdown("Avec notre nouveau modèle, vous ne payez que pour les services réellement consommés, vous permettant ainsi d'optimiser votre budget selon vos besoins.")
        st.markdown(" ") # Espace
        st.markdown("<p style='text-align: center; color: var(--text-color-light);'>Pour plus d'informations sur cette transition ou pour toute question, n'hésitez pas à nous contacter</p>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-weight: 500;'>📧 <a href='mailto:info@constructoai.ca'>info@constructoai.ca</a></p>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-weight: 500;'>🌐 <a href='https://constructoai.ca' target='_blank'>https://constructoai.ca</a></p>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-weight: 500;'>📞 Sylvain Leduc / (514) 820-1972</p>", unsafe_allow_html=True)
        # --- FIN NOUVELLE SECTION PAIEMENT ---

        # >>>>> FIN DU CONTENU STATIQUE CENTRÉ 

    # --- Formulaire de Connexion (reste centré comme avant, sous le contenu statique) ---
    st.divider()
    st.markdown("<h2 style='text-align: center;'>Connexion</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Veuillez entrer le mot de passe pour accéder à l'application.</p>", unsafe_allow_html=True)

    correct_password = st.secrets.get("APP_PASSWORD")
    if not correct_password:
         st.error("Erreur de configuration: Secret 'APP_PASSWORD' non défini.")
         st.info("Veuillez configurer ce secret.")
         return False

    _, login_col, _ = st.columns([1, 1.5, 1])
    with login_col:
        password_attempt = st.text_input(
            "Mot de passe", type="password", key="password_input_login",
            label_visibility="collapsed", placeholder="Entrez votre mot de passe"
            )
        login_button = st.button("Se connecter", key="login_button", use_container_width=True)

    if login_button:
        if password_attempt == correct_password:
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("Mot de passe incorrect.")

    return False # Non connecté


# --- Exécution Principale ---

# >>>>> AFFICHAGE CONDITIONNEL : LOGIN ou APP 
if not display_login_or_app():
    st.stop() # Arrête l'exécution si display_login_or_app retourne False (non connecté)

# --- SI CONNECTÉ, LE SCRIPT CONTINUE ICI ---

# --- Configuration de la Page Principale ---
st.set_page_config(
    page_title="Constructo AI",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Charger Police Google Font & CSS pour l'App ---
st.markdown("""
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700&display=swap" rel="stylesheet">
    <style>
        /* Styles inline spécifiques à l'UI Streamlit (peuvent être dans style.css) */
        .sidebar-subheader {
            margin-top: 1.5rem; margin-bottom: 0.5rem; font-size: 0.875rem;
            font-weight: 500; color: var(--text-color-light);
            text-transform: uppercase; letter-spacing: 0.05em;
        }
        /* Styles pour l'historique dans la sidebar */
        div[data-testid="stHorizontalBlock"] > div:nth-child(1) button[kind="secondary"] {
             text-align: left; justify-content: flex-start !important;
             overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
             font-size: 0.9rem; padding: 0.4rem 0.6rem;
             border: 1px solid transparent; background-color: transparent;
             color: var(--text-color); transition: background-color 0.2s ease, border-color 0.2s ease;
        }
         div[data-testid="stHorizontalBlock"] > div:nth-child(1) button[kind="secondary"]:hover {
              background-color: var(--border-color-light); border-color: var(--border-color);
         }
         div[data-testid="stHorizontalBlock"] > div:nth-child(2) button[kind="secondary"] {
             background: none; border: none; color: var(--text-color-light); cursor: pointer;
             padding: 0.4rem 0.3rem; font-size: 0.9rem; line-height: 1;
         }
         div[data-testid="stHorizontalBlock"] > div:nth-child(2) button[kind="secondary"]:hover {
             color: #EF4444; background-color: rgba(239, 68, 68, 0.1);
         }
    </style>
""", unsafe_allow_html=True)
local_css("style.css") # Recharger pour s'assurer que les styles de l'app sont appliqués

# --- Load API Keys ---
load_dotenv() # Pour le dev local si .env existe
ANTHROPIC_API_KEY = st.secrets.get("ANTHROPIC_API_KEY")
# Load APP_PASSWORD (if needed elsewhere, otherwise it's loaded in display_login_or_app)
APP_PASSWORD = st.secrets.get("APP_PASSWORD")


# --- Initialize Logic Classes & Conversation Manager ---
if 'profile_manager' not in st.session_state:
    try:
        profile_dir_path = "profiles"
        if not os.path.exists(profile_dir_path):
            os.makedirs(profile_dir_path, exist_ok=True); print(f"Dossier '{profile_dir_path}' créé.")
            default_profile_path = os.path.join(profile_dir_path, "default_expert.txt")
            if not os.path.exists(default_profile_path):
                 with open(default_profile_path, "w", encoding="utf-8") as f: f.write("Expert par Défaut\nJe suis un expert IA généraliste."); print("Profil par défaut créé.")
        st.session_state.profile_manager = ExpertProfileManager(profile_dir=profile_dir_path)
        print("ProfileManager initialisé.")
    except Exception as e: st.error(f"Erreur critique: Init ProfileManager: {e}"); st.stop()

if 'expert_advisor' not in st.session_state:
    if not ANTHROPIC_API_KEY: st.error("Erreur critique: ANTHROPIC_API_KEY non configurée."); st.stop()
    try:
        st.session_state.expert_advisor = ExpertAdvisor(api_key=ANTHROPIC_API_KEY)
        st.session_state.expert_advisor.profile_manager = st.session_state.profile_manager
        print("ExpertAdvisor initialisé.")
        available_profiles = st.session_state.profile_manager.get_profile_names()
        if available_profiles:
            initial_profile_name = available_profiles[0]
            st.session_state.selected_profile_name = initial_profile_name
            st.session_state.expert_advisor.set_current_profile_by_name(initial_profile_name)
            print(f"Profil initial chargé: {initial_profile_name}")
        else:
            st.warning("Aucun profil expert trouvé. Utilisation profil par défaut.")
            default_profile = st.session_state.expert_advisor.get_current_profile()
            st.session_state.selected_profile_name = default_profile.get("name", "Expert (Défaut)")
    except Exception as e: st.error(f"Erreur critique: Init ExpertAdvisor: {e}"); st.exception(e); st.stop()

if 'conversation_manager' not in st.session_state:
    try:
        db_file_path = "conversations.db"
        st.session_state.conversation_manager = ConversationManager(db_path=db_file_path)
        print(f"ConversationManager initialisé avec DB: {os.path.abspath(db_file_path)}")
    except Exception as e: st.error(f"Erreur: Init ConversationManager: {e}"); st.exception(e); st.session_state.conversation_manager = None; st.warning("Historique désactivé.")

# Initialisation variables état session (après login check)
if "messages" not in st.session_state: st.session_state.messages = []
if "current_conversation_id" not in st.session_state: st.session_state.current_conversation_id = None
if "processed_messages" not in st.session_state: st.session_state.processed_messages = set()


# --- Fonction de Génération HTML ---
def generate_html_report(messages, profile_name, conversation_id=None, client_name=""):
    """Génère un rapport HTML autonome à partir de l'historique."""
    custom_css = load_css_content("style.css")
    now = datetime.now().strftime("%d/%m/%Y à %H:%M:%S")
    conv_id_display = f" (ID: {conversation_id})" if conversation_id else ""
    client_display = f"<p><strong>Client :</strong> {html.escape(client_name)}</p>" if client_name else ""
    messages_html = ""
    md_converter = markdown.Markdown(extensions=['tables', 'fenced_code'])

    for msg in messages:
        role = msg.get("role", "unknown")
        content = msg.get("content", "*Message vide*")

        if role == "system": continue

        try:
            md_converter.reset()
            content_str = str(content) if not isinstance(content, str) else content
            content_html = md_converter.convert(content_str)
        except Exception as e:
            print(f"Erreur conversion Markdown: {e}")
            content_html = f"<p>{html.escape(str(content)).replace(chr(10), '<br/>')}</p>"

        if role == "user":
            messages_html += f'<div class="stChatMessage user-bubble"><strong>Utilisateur :</strong><div class="msg-content">{content_html}</div></div>\n'
        elif role == "assistant":
            messages_html += f'<div class="stChatMessage assistant-bubble"><strong>Expert ({html.escape(profile_name)}) :</strong><div class="msg-content">{content_html}</div></div>\n'
        elif role == "search_result":
             messages_html += f'<div class="stChatMessage search-bubble"><strong>Résultat Recherche Web :</strong><div class="msg-content">{content_html}</div></div>\n'
        else:
             messages_html += f'<div class="stChatMessage other-bubble"><strong>{html.escape(role.capitalize())} :</strong><div class="msg-content">{content_html}</div></div>\n'

    html_output = f"""<!DOCTYPE html><html lang="fr"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Rapport Constructo AI - {html.escape(profile_name)}{conv_id_display}</title><link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700&display=swap" rel="stylesheet"><style>{custom_css} body{{padding:20px;background-color:var(--background-color,#F9FAFB);max-width:1200px;margin:20px auto;box-shadow:0 2px 10px rgba(0,0,0,.1);border-radius:8px}}.search-bubble{{background-color:#F0FDF4;border:1px solid #BBF7D0;color:#14532D;padding:.8rem 1.2rem;margin-bottom:1rem;border-radius:var(--border-radius-md);box-shadow:var(--box-shadow-sm);line-height:1.6}}.search-bubble .msg-content p,.search-bubble .msg-content ul,.search-bubble .msg-content ol{{color:#14532D}}.other-bubble{{background-color:#FEFCE8;border:1px solid #FEF08A}}.report-header h1{{text-align:center;color:var(--primary-color,#3B82F6);font-size:1.8rem;margin-bottom:15px;padding-bottom:10px;border-bottom:2px solid var(--primary-color,#3B82F6)}}.report-info{{margin-bottom:25px;padding:10px;background-color:var(--border-color-light,#F3F4F6);border-radius:var(--border-radius-sm);font-size:.9rem;color:var(--text-color-light,#6B7280)}}.report-info p{{margin:3px 0}}section[data-testid=stSidebar],div[data-testid=stChatInput],.stButton{{display:none!important}}.msg-content table{{font-size:.9em}}.msg-content th,.msg-content td{{padding:6px 9px}}.msg-content pre{{font-size:.85rem}}</style></head><body><div class="report-header"><h1>Rapport Constructo AI</h1></div><div class="report-info"><p><strong>Expert :</strong> {html.escape(profile_name)}</p>{client_display}<p><strong>Date :</strong> {now}</p><p><strong>ID Conversation :</strong> {html.escape(str(conversation_id)) if conversation_id else 'N/A'}</p></div><div class="conversation-history">{messages_html}</div></body></html>"""
    return html_output

# --- Helper Functions (Application Logic) ---
def start_new_consultation():
    """Réinitialise l'état pour une nouvelle conversation."""
    st.session_state.messages = []
    st.session_state.current_conversation_id = None
    st.session_state.processed_messages = set()
    profile_name = "par défaut"
    if 'expert_advisor' in st.session_state:
        profile = st.session_state.expert_advisor.get_current_profile()
        profile_name = profile.get('name', 'par défaut') if profile else "par défaut"
    # Ajouter le message d'accueil
    st.session_state.messages.append({
        "role": "assistant",
        "content": f"Bonjour! Je suis votre expert {profile_name}. Comment puis-je vous aider aujourd'hui?\n\n"
                  f"Pour effectuer une recherche web, tapez simplement `/search votre question`\n"
                  f"Exemple: `/search normes construction Quebec 2025`"
    })
    if 'html_download_data' in st.session_state: del st.session_state.html_download_data
    if "files_to_analyze" in st.session_state: del st.session_state.files_to_analyze
    st.rerun()

def load_selected_conversation(conv_id):
    """Charge une conversation depuis la base de données."""
    if st.session_state.conversation_manager:
        messages = st.session_state.conversation_manager.load_conversation(conv_id)
        if messages is not None:
            st.session_state.messages = messages
            st.session_state.current_conversation_id = conv_id
            st.session_state.processed_messages = set()
            if 'html_download_data' in st.session_state: del st.session_state.html_download_data
            if "files_to_analyze" in st.session_state: del st.session_state.files_to_analyze
            st.success(f"Consultation {conv_id} chargée.")
            st.rerun()
        else:
            st.error(f"Erreur lors du chargement de la conversation {conv_id}.")
    else:
        st.error("Gestionnaire de conversations indisponible.")

def delete_selected_conversation(conv_id):
    """Supprime une conversation de la base de données."""
    if st.session_state.conversation_manager:
        print(f"Tentative suppression conv {conv_id}")
        success = st.session_state.conversation_manager.delete_conversation(conv_id)
        if success:
            st.success(f"Consultation {conv_id} supprimée.")
            if st.session_state.current_conversation_id == conv_id:
                start_new_consultation() # Rerun inclus
            else:
                if 'html_download_data' in st.session_state: del st.session_state.html_download_data
                st.rerun() # Juste pour rafraîchir la liste
        else:
            st.error(f"Impossible de supprimer conv {conv_id}.")
    else:
        st.error("Gestionnaire de conversations indisponible.")

def save_current_conversation():
    """Sauvegarde la conversation actuelle (messages) dans la DB."""
    should_save = True
    if st.session_state.conversation_manager and st.session_state.messages:
        is_initial_greeting_only = (
            len(st.session_state.messages) == 1 and
            st.session_state.messages[0].get("role") == "assistant" and
            st.session_state.messages[0].get("content", "").startswith("Bonjour!") and
            st.session_state.current_conversation_id is None
        )
        if is_initial_greeting_only: should_save = False

        if should_save:
            try:
                new_id = st.session_state.conversation_manager.save_conversation(
                    st.session_state.current_conversation_id,
                    st.session_state.messages
                )
                if new_id is not None and st.session_state.current_conversation_id is None:
                    st.session_state.current_conversation_id = new_id
            except Exception as e:
                st.warning(f"Erreur sauvegarde auto: {e}")
                st.exception(e)

# --- Sidebar UI (App Principale) ---
with st.sidebar:
    try:
        logo_path = os.path.join(os.path.dirname(__file__), "assets", "logo.png")
        if os.path.exists(logo_path):
            st.image(logo_path, width=150)
        else:
             st.warning("Logo 'assets/logo.png' non trouvé.")
    except Exception as e:
        st.error(f"Erreur logo: {e}")

    st.title("Constructo AI")
    if st.button("➕ Nouvelle Consultation", key="new_consult_button_top", use_container_width=True):
        save_current_conversation()
        start_new_consultation()
    st.markdown('<hr style="margin: 1rem 0; border-top: 1px solid var(--border-color);">', unsafe_allow_html=True)

    # --- Profil Expert ---
    st.markdown('<div class="sidebar-subheader">👤 Profil Expert</div>', unsafe_allow_html=True)
    if 'expert_advisor' in st.session_state and st.session_state.expert_advisor.profile_manager:
        profile_names = st.session_state.expert_advisor.profile_manager.get_profile_names()
        if profile_names:
            try:
                selected_profile_name_ref = st.session_state.get("selected_profile_name", profile_names[0])
                current_index = profile_names.index(selected_profile_name_ref) if selected_profile_name_ref in profile_names else 0
            except ValueError:
                 current_index = 0
            selected_profile = st.selectbox("Profil:", profile_names, index=current_index, key="profile_select", label_visibility="collapsed")
            if selected_profile != st.session_state.get("selected_profile_name"):
                print(f"Changement profil: '{st.session_state.get('selected_profile_name')}' -> '{selected_profile}'")
                save_current_conversation()
                with st.spinner(f"Changement vers {selected_profile}..."):
                    success = st.session_state.expert_advisor.set_current_profile_by_name(selected_profile)
                    if success:
                        st.session_state.selected_profile_name = selected_profile
                        st.success(f"Profil changé. Nouvelle consultation.")
                        start_new_consultation() # Rerun inclus
                    else:
                        st.error(f"Impossible de charger profil '{selected_profile}'.")
        else:
            st.warning("Aucun profil expert trouvé.")
    else:
        st.error("Module Expert non initialisé.")

    # --- Analyse Fichiers ---
    st.markdown('<div class="sidebar-subheader">📄 Analyse Fichiers</div>', unsafe_allow_html=True)
    uploaded_files_sidebar = []
    if 'expert_advisor' in st.session_state:
        supported_types = st.session_state.expert_advisor.get_supported_filetypes_flat()
        uploaded_files_sidebar = st.file_uploader("Téléverser fichiers:", type=supported_types if supported_types else None, accept_multiple_files=True, key="file_uploader_sidebar", label_visibility="collapsed")
        if uploaded_files_sidebar:
            if st.button("🔍 Analyser Fichiers", key="analyze_button", use_container_width=True):
                num_files = len(uploaded_files_sidebar)
                file_names_str = ', '.join([f.name for f in uploaded_files_sidebar])
                user_analysis_prompt = f"J'ai téléversé {num_files} fichier(s) ({file_names_str}) pour analyse. Peux-tu les examiner ?"
                action_id = f"analyze_{datetime.now().isoformat()}"
                st.session_state.files_to_analyze = uploaded_files_sidebar
                st.session_state.messages.append({"role": "user", "content": user_analysis_prompt, "id": action_id})
                save_current_conversation()
                st.rerun()
    else:
         st.error("Module Expert non initialisé.")

    # --- Aide Recherche Web (Nouvelle section) ---
    st.markdown('<hr style="margin: 1rem 0; border-top: 1px solid var(--border-color);">', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-subheader">🔎 Recherche Web</div>', unsafe_allow_html=True)
    with st.expander("Comment utiliser la recherche web"):
        st.markdown("""
        Pour effectuer une recherche web via Claude:
        
        1. Tapez `/search` suivi de votre question ou requête
        2. Exemple: `/search normes électriques Québec`
        3. Pour rechercher des informations sur un site spécifique:
           `/search règlement construction site:rbq.gouv.qc.ca`
        4. Attendez quelques secondes pour les résultats
        
        **Remarque:** Pour obtenir les meilleurs résultats, formulez des questions précises et utilisez des mots-clés pertinents.
        """)

    # --- Historique ---
    if st.session_state.get('conversation_manager'):
        st.markdown('<hr style="margin: 1rem 0; border-top: 1px solid var(--border-color);">', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-subheader">🕒 Historique</div>', unsafe_allow_html=True)
        try:
            conversations = st.session_state.conversation_manager.list_conversations(limit=100)
            if not conversations: st.caption("Aucune consultation sauvegardée.")
            else:
                with st.container(height=300):
                    for conv in conversations:
                        col1, col2 = st.columns([0.85, 0.15])
                        with col1:
                            if st.button(conv['name'], key=f"load_conv_{conv['id']}", use_container_width=True, type="secondary", help=f"Charger '{conv['name']}' (màj: {conv['last_updated_at']})"):
                                save_current_conversation(); load_selected_conversation(conv['id'])
                        with col2:
                            if st.button("🗑️", key=f"delete_conv_{conv['id']}", help=f"Supprimer '{conv['name']}'", use_container_width=True, type="secondary"):
                                delete_selected_conversation(conv['id'])
        except Exception as e: st.error(f"Erreur historique: {e}"); st.exception(e)
    else: st.caption("Module historique inactif.")

    # --- Export ---
    st.markdown('<hr style="margin: 1rem 0; border-top: 1px solid var(--border-color);">', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-subheader">📥 Export</div>', unsafe_allow_html=True)
    client_name_export = st.text_input("Nom client (optionnel)", key="client_name_export", placeholder="Pour rapport HTML")
    if 'html_download_data' not in st.session_state: st.session_state.html_download_data = None
    if st.button("Rapport HTML", key="gen_html_btn", use_container_width=True, help="Générer rapport HTML"):
            st.session_state.html_download_data = None
            can_generate = True
            if not st.session_state.messages or (len(st.session_state.messages) == 1 and st.session_state.messages[0].get("role") == "assistant" and st.session_state.messages[0].get("content", "").startswith("Bonjour!")): can_generate = False
            if not can_generate: st.warning("Conversation vide ou initiale.")
            else:
                with st.spinner("Génération HTML..."):
                    try:
                        profile_name = "Expert"; current_profile = st.session_state.expert_advisor.get_current_profile() if 'expert_advisor' in st.session_state else None
                        if current_profile: profile_name = current_profile.get('name', 'Expert')
                        conv_id = st.session_state.current_conversation_id
                        html_string = generate_html_report(st.session_state.messages, profile_name, conv_id, client_name_export)
                        if html_string: id_part = f"Conv{conv_id}" if conv_id else datetime.now().strftime('%Y%m%d_%H%M'); filename = f"Rapport_ProjetsKDI_{id_part}.html"; st.session_state.html_download_data = {"data": html_string, "filename": filename}; st.success("Rapport prêt.")
                        else: st.error("Échec génération HTML.")
                    except Exception as e: st.error(f"Erreur génération HTML: {e}"); st.exception(e)
            st.rerun()
    if st.session_state.get('html_download_data'):
        download_info = st.session_state.html_download_data
        st.download_button(label="⬇️ Télécharger HTML", data=download_info["data"].encode("utf-8"), file_name=download_info["filename"], mime="text/html", key="dl_html", use_container_width=True, on_click=lambda: st.session_state.update(html_download_data=None))

    # --- Liens Programmes ---
    st.markdown('<hr style="margin: 1rem 0; border-top: 1px solid var(--border-color);">', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-subheader">🔗 Logiciels Windows et Documents</div>', unsafe_allow_html=True)
    wetransfer_links = {"TAKEOFF": "https://we.tl/t-2m6p765rVv", "CRM": "https://we.tl/t-vsGuk2AQZO", "REGISTRE DES PROJETS": "https://we.tl/t-VKj2HseTAN", "GESTIONNAIRE D'INVENTAIRE": "https://we.tl/t-K2j2zQYBLx", "FORMULAIRES": "https://we.tl/t-tcXwFRQ6t2", "SMART NOTE": "https://we.tl/t-jYkQMXteMx", "GUIDE DES PROMPTS": "https://we.tl/t-efBWRHP6yG"}
    for program_name, link_url in wetransfer_links.items():
        if link_url and link_url != "#" and link_url.strip(): st.markdown(f"*   [{program_name}]({link_url})")
        else: st.markdown(f"*   {program_name} *(Lien non disponible)*")
    st.caption("Propriété intellectuelle de Sylvain Leduc. info@constructoai.ca")

    # --- Bouton Déconnexion ---
    st.markdown('<hr style="margin: 1rem 0; border-top: 1px solid var(--border-color);">', unsafe_allow_html=True)
    if st.button("🚪 Déconnexion", key="logout_button", use_container_width=True):
        st.session_state.logged_in = False
        keys_to_clear = ["messages", "current_conversation_id", "processed_messages", "html_download_data", "selected_profile_name", "files_to_analyze"]
        for key in keys_to_clear:
             if key in st.session_state: del st.session_state[key]
        # Aussi nettoyer les objets potentiellement lourds ou liés aux clés API
        if 'expert_advisor' in st.session_state: del st.session_state['expert_advisor']
        if 'profile_manager' in st.session_state: del st.session_state['profile_manager']
        if 'conversation_manager' in st.session_state: del st.session_state['conversation_manager']
        st.rerun()


# --- Main Chat Area (App Principale) ---
main_container = st.container()
with main_container:
    # Titre dynamique
    if 'expert_advisor' in st.session_state:
        current_profile = st.session_state.expert_advisor.get_current_profile()
        profile_name = "Assistant Constructo AI"; profile_name = current_profile.get('name', profile_name) if current_profile else profile_name
        st.title(f"Assistant: {profile_name}")
        if not current_profile or current_profile.get('id') == 'default_expert': st.markdown("*Profil expert par défaut actif.*")
    else: st.title("Assistant Constructo AI"); st.markdown("*Erreur: Module expert non initialisé.*")
    st.divider()

    # Affichage du chat (le contenu statique est géré dans la page de login)
    if not st.session_state.messages and 'expert_advisor' in st.session_state:
         profile = st.session_state.expert_advisor.get_current_profile()
         prof_name = profile.get('name', 'par défaut') if profile else "par défaut"
         st.session_state.messages.append({
             "role": "assistant", 
             "content": f"Bonjour! Je suis votre expert {prof_name}. Comment puis-je vous aider aujourd'hui?\n\n"
                        f"Pour effectuer une recherche web, tapez simplement `/search votre question`\n"
                        f"Exemple: `/search normes construction Quebec 2025`"
         })

    # Boucle d'affichage des messages
    for message in st.session_state.messages:
        role = message.get("role", "unknown"); content = message.get("content", "*Message vide*")
        if role == "system": continue
        avatar = "👤" if role == "user" else "🏗️" if role == "assistant" else "🔎" if role == "search_result" else "🤖"
        with st.chat_message(role, avatar=avatar):
            display_content = str(content) if not isinstance(content, str) else content
            # Utiliser unsafe_allow_html=True peut être risqué si le contenu vient d'une source non sûre
            # Mais nécessaire si Claude ou les snippets Google retournent du Markdown/HTML simple formaté
            # Pour plus de sécurité, on pourrait utiliser une librairie de sanitization HTML ici.
            # Pour l'instant, on garde False pour plus de sécurité par défaut, mais on sait que ça limite le rendu.
            st.markdown(display_content, unsafe_allow_html=False)

# --- Chat Input ---
prompt = st.chat_input("Posez votre question ou tapez /search [recherche web]...")

# --- Traitement du nouveau prompt ---
if prompt:
    user_msg = {"role": "user", "content": prompt, "id": datetime.now().isoformat()}
    st.session_state.messages.append(user_msg)
    save_current_conversation()
    if 'html_download_data' in st.session_state: del st.session_state.html_download_data
    st.rerun()

# --- LOGIQUE DE RÉPONSE / RECHERCHE / ANALYSE ---
action_to_process = None
if st.session_state.messages and 'expert_advisor' in st.session_state:
    last_message = st.session_state.messages[-1]
    msg_id = last_message.get("id", last_message.get("content")) # Use ID if available, else content hash (less reliable)
    if msg_id not in st.session_state.processed_messages: action_to_process = last_message

if action_to_process and action_to_process.get("role") == "user":
    msg_id = action_to_process.get("id", action_to_process.get("content"))
    st.session_state.processed_messages.add(msg_id)
    user_content = action_to_process.get("content", "")
    
    # Amélioration de la détection de commande search
    is_search_command = False
    search_query = ""
    
    if user_content.strip().lower().startswith("/search "):
        is_search_command = True
        search_query = user_content[len("/search "):].strip()
    elif user_content.strip().lower() == "/search":
        is_search_command = True
        search_query = ""  # Requête vide, à gérer
    
    files_for_analysis = st.session_state.get("files_to_analyze", [])
    is_analysis_request = action_to_process.get("id", "").startswith("analyze_") and files_for_analysis

    if is_analysis_request:
        # --- Logique Analyse Fichiers ---
        with st.chat_message("assistant", avatar="🏗️"):
            with st.spinner("Analyse des fichiers..."):
                try:
                    history_context = [m for m in st.session_state.messages[:-1] if m.get("role") != "system"]
                    analysis_response, analysis_details = st.session_state.expert_advisor.analyze_documents(files_for_analysis, history_context)
                    st.markdown(analysis_response, unsafe_allow_html=False)
                    st.session_state.messages.append({"role": "assistant", "content": analysis_response})
                    st.success("Analyse terminée.")
                    if "files_to_analyze" in st.session_state: del st.session_state.files_to_analyze
                except Exception as e:
                    error_msg = f"Erreur analyse: {e}"; st.error(error_msg); st.exception(e)
                    st.session_state.messages.append({"role": "assistant", "content": f"Erreur analyse: {e}"})
                    if "files_to_analyze" in st.session_state: del st.session_state.files_to_analyze
                except Exception as e:
                    error_msg = f"Erreur analyse: {e}"; st.error(error_msg); st.exception(e)
                    st.session_state.messages.append({"role": "assistant", "content": f"Erreur analyse: {e}"})
                    if "files_to_analyze" in st.session_state: del st.session_state.files_to_analyze
        save_current_conversation(); st.rerun()

    elif is_search_command:
        # --- Logique Recherche Web Simplifiée ---
        query = search_query.strip()
        if not query:
            error_msg = "Commande `/search` vide. Veuillez fournir un terme de recherche."
            with st.chat_message("assistant", avatar="⚠️"):
                st.warning(error_msg)
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
            save_current_conversation()
            st.rerun()
        else:
            # Ajouter un message d'attente
            with st.chat_message("assistant", avatar="🔎"):
                with st.spinner(f"Recherche web pour: '{query}'"):
                    try:
                        # Appel direct à la fonction de recherche
                        search_result = st.session_state.expert_advisor.perform_web_search(query)
                        st.markdown(search_result)
                        
                        # Ajouter le résultat aux messages
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": search_result,
                            "id": f"search_result_{datetime.now().isoformat()}"
                        })
                        save_current_conversation()
                    except Exception as e:
                        error_msg = f"Erreur lors de la recherche web: {str(e)}"
                        st.error(error_msg)
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": f"Désolé, une erreur s'est produite lors de la recherche web: {type(e).__name__}",
                            "id": f"search_error_{datetime.now().isoformat()}"
                        })
                        save_current_conversation()

    else: # Traiter comme chat normal
        # --- Logique Réponse Claude ---
        with st.chat_message("assistant", avatar="🏗️"):
            placeholder = st.empty()
            with st.spinner("L'expert réfléchit..."):
                try:
                    # Préparer l'historique pour l'API
                    history_for_claude = []
                    for msg in st.session_state.messages[:-1]: # Exclure le dernier message utilisateur
                        role, content = msg.get("role"), msg.get("content");
                        # Ignorer les placeholders ou messages système non pertinents
                        if role == "system" or msg.get("id", "").startswith("search_placeholder_"): continue # Ignorer placeholders de recherche
                        # Simplifier le contenu (pas d'images ici, juste du texte)
                        content_str = str(content)
                        # Mapper les rôles correctement pour l'API Claude
                        api_role = "assistant" if role in ["assistant", "search_result"] else "user"
                        if role == "search_result":
                             content_str = f"[Info Web]: {content_str}" # Préfixer le contenu de la recherche
                        history_for_claude.append({"role": api_role, "content": content_str})

                    response_content = st.session_state.expert_advisor.obtenir_reponse(user_content, history_for_claude)
                    placeholder.markdown(response_content, unsafe_allow_html=False)
                    st.session_state.messages.append({"role": "assistant", "content": response_content})
                except Exception as e:
                    error_msg = f"Erreur réponse Claude: {e}"; print(error_msg); st.exception(e)
                    placeholder.error(f"Erreur technique Claude ({type(e).__name__}).")
                    st.session_state.messages.append({"role": "assistant", "content": f"Erreur technique Claude ({type(e).__name__})."})
        save_current_conversation()
        st.rerun()

# --- FIN DU FICHIER app.py ---