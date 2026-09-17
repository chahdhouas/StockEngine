import streamlit as st, pandas as pd, plotly.express as px, os
from datetime import datetime

# ==========================================
# ICÔNES VECTORIELLES (remplacent les emojis pour un rendu
# identique sur tous les systèmes d'exploitation/navigateurs)
# ==========================================
_ICONS = {
    "bar-chart": '<path d="M3 3v18h18"/><path d="M18 17V9"/><path d="M13 17V5"/><path d="M8 17v-3"/>',
    "refresh": '<path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/><path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16"/><path d="M16 16h5v5"/>',
    "trending-up": '<polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/>',
    "trending-down": '<polyline points="22 17 13.5 8.5 8.5 13.5 2 7"/><polyline points="16 17 22 17 22 11"/>',
    "package": '<path d="m7.5 4.27 9 5.15"/><path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z"/><path d="m3.3 7 8.7 5 8.7-5"/><path d="M12 22V12"/>',
    "tag": '<path d="M12.586 2.586A2 2 0 0 0 11.172 2H4a2 2 0 0 0-2 2v7.172a2 2 0 0 0 .586 1.414l8.704 8.704a2.426 2.426 0 0 0 3.42 0l6.58-6.58a2.426 2.426 0 0 0 0-3.42Z"/><circle cx="7.5" cy="7.5" r=".5" fill="currentColor"/>',
    "inbox": '<polyline points="22 12 16 12 14 15 10 15 8 12 2 12"/><path d="M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11Z"/>',
    "user": '<path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>',
    "database": '<ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5V19A9 3 0 0 0 21 19V5"/><path d="M3 12A9 3 0 0 0 21 12"/>',
    "arrow-lr": '<path d="M8 3 4 7l4 4"/><path d="M4 7h16"/><path d="m16 21 4-4-4-4"/><path d="M20 17H4"/>',
}


def icon(name, size=20, color="currentColor", stroke_width=2):
    """Retourne une icône SVG (style Lucide) en HTML, pour remplacer les emojis."""
    paths = _ICONS.get(name, "")
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="{stroke_width}" '
        f'stroke-linecap="round" stroke-linejoin="round" '
        f'style="vertical-align:-4px; display:inline-block;">{paths}</svg>'
    )


def empty_state(message, icon_name="inbox"):
    """Bloc d'état vide soigné, à la place de st.info('Aucune donnée...')."""
    st.markdown(
        f'<div class="empty-state">{icon(icon_name, 32)}<span>{message}</span></div>',
        unsafe_allow_html=True,
    )


# ==========================================
# CONFIGURATION DE LA PAGE & STYLE DE SIGN
# ==========================================
st.set_page_config(
    page_title="StockEngine - Gestion de Stock",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Injection CSS pour un design professionnel (Bleu, Rose, Blanc)
st.markdown("""
    <style>
    /* Masquer les éléments d'interface Streamlit (menu, bouton Deploy, barre d'outils, footer)
       pour une présentation "application pure" sans artefacts de preview */
    /* MainMenu (☰) réaffiché : c'est lui qui contient le sélecteur de thème
       Light/Dark/System (Settings). Le bouton "Deploy" reste masqué séparément
       via .stAppDeployButton ci-dessous.
       NB : dans les versions récentes de Streamlit, le ☰ fait partie du même
       conteneur que la barre d'outils (stToolbar) — on ne masque donc plus
       tout le toolbar (sinon le ☰ disparaît avec), on force juste sa visibilité. */
    footer { visibility: hidden; }
    [data-testid="stToolbar"] { visibility: visible !important; }
    [data-testid="stMainMenu"] { visibility: visible !important; display: block !important; }
    [data-testid="stDecoration"] { display: none; }
    [data-testid="stStatusWidget"] { visibility: hidden; display: none; }
    .stAppDeployButton { display: none !important; }
    a[href*="streamlit.io"] { display: none !important; }

    /* Le bandeau supérieur reste nécessaire au fonctionnement de Streamlit,
       mais on le rend transparent et fin pour qu'il ne se voie plus comme
       une barre blanche vide au-dessus de l'application */
    [data-testid="stHeader"] {
        background: transparent !important;
        height: 2.2rem;
        overflow: visible !important;
    }
    [data-testid="stAppViewContainer"] .block-container {
        padding-top: 1.5rem;
    }

    /* Flèche de réouverture de la sidebar (mobile) : le bandeau stHeader
       étant réduit à 2.2rem, ce bouton se retrouvait coupé/masqué sur
       téléphone. On force sa visibilité, sa taille tactile et son
       empilement au-dessus des autres éléments. */
    [data-testid="collapsedControl"] {
        display: flex !important;
        visibility: visible !important;
        opacity: 1 !important;
        z-index: 999999 !important;
        position: fixed !important;
        top: 0.6rem !important;
        left: 0.6rem !important;
    }
    [data-testid="collapsedControl"] svg {
        width: 1.5rem !important;
        height: 1.5rem !important;
    }

    /* Masquer les icônes de lien d'ancrage que Streamlit ajoute
       automatiquement à côté de chaque titre/sous-titre (uniquement
       à l'intérieur des titres, pour ne pas masquer le menu ☰ du header) */
    h1 a, h2 a, h3 a, h4 a,
    h1 [data-testid="stHeaderActionElements"],
    h2 [data-testid="stHeaderActionElements"],
    h3 [data-testid="stHeaderActionElements"],
    h4 [data-testid="stHeaderActionElements"] { display: none !important; }

    /* Fond de l'application avec un léger dégradé */
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #e4e8f0 100%);
    }

    /* Personnalisation de la barre latérale */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e3c72 0%, #2a5298 100%);
        color: white;
    }
    [data-testid="stSidebar"] .stMarkdown, [data-testid="stSidebar"] p {
        color: #ffffff;
    }
    /* Bon contraste pour les titres et libellés de la sidebar */
    [data-testid="stSidebar"] h3 {
        color: #ffffff !important;
        opacity: 1 !important;
    }
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {
        color: rgba(255,255,255,0.85) !important;
    }

    /* Titres professionnels */
    h1, h2, h3 {
        color: #1e3c72 !important;
        font-family: 'Segoe UI', Roboto, Helvetica, sans-serif;
    }

    /* Boutons personnalisés avec dégradé Rose/Bleu */
    div.stButton > button:first-child {
        background: linear-gradient(45deg, #ff416c 0%, #ff4b2b 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 24px;
        font-weight: bold;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(255, 65, 108, 0.2);
    }
    div.stButton > button:first-child:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(255, 65, 108, 0.4);
        color: white;
    }

    /* Cartes blanches pour le Dashboard (KPIs) — hauteur uniforme,
       même si le texte du chiffre passe sur deux lignes */
    .metric-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border-left: 5px solid #ff416c; /* Touche de rose */
        margin-bottom: 15px;
        min-height: 118px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .metric-card.blue {
        border-left: 5px solid #2a5298; /* Touche de bleu */
    }
    .metric-card h2 {
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    /* État vide soigné (remplace les blocs st.info génériques) */
    .empty-state {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 10px;
        padding: 40px 20px;
        background-color: #f3f6fc;
        border: 1px dashed #c6d3e8;
        border-radius: 12px;
        color: #5b6b8c;
        text-align: center;
    }
    .empty-state svg { opacity: 0.55; }
    .empty-state span { font-size: 14px; }

    /* Bulles d'alerte de stock (badges) */
    .badge {
        display: inline-block;
        padding: 4px 14px;
        border-radius: 999px;
        font-size: 13px;
        font-weight: 600;
        white-space: nowrap;
    }
    .badge-red {
        background-color: #ffe0e6;
        color: #d6003c;
    }
    .badge-green {
        background-color: #dcf7e3;
        color: #1a8a3d;
    }

    /* Tableau HTML personnalisé (inventaire) */
    .custom-table {
        width: 100%;
        border-collapse: collapse;
        background: #ffffff;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        font-size: 14px;
    }
    .custom-table th {
        background: #1e3c72;
        color: white;
        text-align: left;
        padding: 10px 14px;
        font-weight: 600;
    }
    .custom-table td {
        padding: 10px 14px;
        border-bottom: 1px solid #eef1f6;
        color: #333;
    }
    .custom-table tr:last-child td { border-bottom: none; }
    .custom-table tr:hover td { background: #f7f9fc; }

    </style>
""", unsafe_allow_html=True)

# ==========================================
# GESTION DES DONNÉES (CSV)
# ==========================================
CSV_FILE = "stock_data.csv"
INVENTAIRE_FILE = "stock.csv"
USERS_FILE = "users.csv"

BASE_COLS = ["Date", "Type", "Produit", "Quantite", "Categorie", "Motif", "Utilisateur"]

def load_data():
    if os.path.exists(CSV_FILE):
        df = pd.read_csv(CSV_FILE)
        df['Date'] = pd.to_datetime(df['Date']).dt.date
        # Colonnes optionnelles (rétro-compatibilité avec un fichier plus ancien)
        for col in ["Motif", "Utilisateur"]:
            if col not in df.columns:
                df[col] = ""
        return df[BASE_COLS]
    else:
        return pd.DataFrame(columns=BASE_COLS)

def save_data(df):
    df.to_csv(CSV_FILE, index=False)

def load_inventaire():
    """Charge le référentiel produits (stock.csv) : quantité en stock, seuil d'alerte, prix, fournisseur."""
    if os.path.exists(INVENTAIRE_FILE):
        return pd.read_csv(INVENTAIRE_FILE)
    else:
        return pd.DataFrame(columns=["id", "produit", "categorie", "quantite", "seuil_alerte", "prix_unitaire", "fournisseur"])

def load_users():
    """Charge les comptes utilisateurs (users.csv) : username, password, nom, role."""
    if os.path.exists(USERS_FILE):
        return pd.read_csv(USERS_FILE, dtype=str)
    else:
        # Compte de secours si le fichier est absent
        return pd.DataFrame([{"username": "admin", "password": "admin123", "nom": "Administrateur", "role": "Admin"}])

# Initialisation des données dans la session
if 'df_stock' not in st.session_state:
    st.session_state.df_stock = load_data()

if 'df_inventaire' not in st.session_state:
    st.session_state.df_inventaire = load_inventaire()

# ==========================================
# ÉCRAN DE CONNEXION (LOGIN)
# ==========================================
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:

    # --------------------------------------
    # CSS dédié à l'écran de connexion
    # Version sobre "outil professionnel" : carte simple,
    # palette identique au dashboard, sans décor superflu.
    # --------------------------------------
    st.markdown("""
        <style>
        .stApp {
            background: linear-gradient(135deg, #f5f7fa 0%, #e4e8f0 100%) !important;
        }
        [data-testid="stHeader"] { background: transparent; }

        /* Carte de connexion */
        [data-testid="stForm"] {
            max-width: 480px;
            margin: 70px auto 0 auto;
            background: #ffffff !important;
            border-radius: 16px;
            border: 1px solid rgba(30,60,114,0.08) !important;
            box-shadow: 0 10px 30px rgba(30,60,114,0.12) !important;
            padding: 48px 44px !important;
        }

        .login-logo {
            text-align: center;
            margin-bottom: 10px;
            font-size: 52px;
        }
        .login-brand {
            text-align: center;
            color: #1e3c72;
            font-size: 30px;
            font-weight: 700;
            margin-bottom: 6px;
        }
        .login-subtitle {
            text-align: center;
            color: #7d8aa3;
            font-size: 15px;
            margin-bottom: 34px;
        }

        /* Libellés des champs */
        [data-testid="stForm"] label p {
            color: #2a3a5c !important;
            font-size: 14px;
            font-weight: 600;
        }

        /* Champs de saisie */
        [data-testid="stTextInputRootElement"] {
            background: #f5f7fa !important;
            border: 1px solid #dde3ec !important;
            border-radius: 9px !important;
            height: 50px !important;
            transition: .2s;
        }
        [data-testid="stTextInputRootElement"]:focus-within {
            border: 1px solid #2a5298 !important;
            box-shadow: 0 0 0 3px rgba(42,82,152,0.12) !important;
        }
        [data-testid="stTextInputRootElement"] input {
            color: #1e293b !important;
            border: none !important;
            box-shadow: none !important;
            background: transparent !important;
            font-size: 15px !important;
        }

        /* Bouton de connexion (même dégradé que le reste de l'app) */
        [data-testid="stFormSubmitButton"] { width: 100% !important; }
        [data-testid="stFormSubmitButton"] button {
            width: 100% !important;
            min-height: 52px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            background: linear-gradient(45deg, #1e3c72 0%, #2a5298 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: 9px !important;
            padding: 14px 24px !important;
            margin: 12px 0 0 0 !important;
            font-weight: 700 !important;
            font-size: 17px !important;
            line-height: 1.4 !important;
            white-space: nowrap;
            transition: .25s;
            box-shadow: 0 4px 14px rgba(30,60,114,0.25) !important;
        }
        [data-testid="stFormSubmitButton"] button p {
            margin: 0 !important;
        }
        [data-testid="stFormSubmitButton"] button:hover {
            transform: translateY(-1px);
            box-shadow: 0 6px 18px rgba(30,60,114,0.35) !important;
        }

        /* Adaptation mobile : carte pleine largeur, espacements resserrés */
        @media (max-width: 640px) {
            [data-testid="stForm"] {
                margin: 30px auto 0 auto !important;
                padding: 28px 22px !important;
                max-width: 94vw;
            }
            .login-brand { font-size: 20px; }
            .login-logo { font-size: 34px; }
        }
        </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.4, 1])

    with col2:
        with st.form("login_form"):
            st.markdown('<div class="login-logo">📦</div>', unsafe_allow_html=True)
            st.markdown('<div class="login-brand">StockEngine</div>', unsafe_allow_html=True)
            st.markdown('<div class="login-subtitle">Application de Gestion de Stock</div>', unsafe_allow_html=True)

            username = st.text_input("Identifiant", placeholder="Nom d'utilisateur")
            password = st.text_input("Mot de passe", type="password", placeholder="••••••••")
            submit_login = st.form_submit_button("Se connecter")

            if submit_login:
                users_df = load_users()
                match = users_df[
                    (users_df['username'].str.strip() == username.strip()) &
                    (users_df['password'].astype(str) == password)
                ]
                if not match.empty:
                    st.session_state.logged_in = True
                    st.session_state.current_user = match.iloc[0]['username']
                    st.session_state.current_nom = match.iloc[0]['nom']
                    st.session_state.current_role = match.iloc[0]['role']
                    st.success("Connexion réussie !")
                    st.rerun()
                else:
                    st.error("Identifiant ou mot de passe incorrect.")

    st.stop()


# ==========================================
# APPLICATION PRINCIPALE (APPRÈS CONNEXION)
# ==========================================

# Déconnexion dans la barre latérale
with st.sidebar:
    st.markdown(f'### {icon("user", 20, "#ffffff")} Session Active', unsafe_allow_html=True)
    nom_affiche = st.session_state.get("current_nom", "Admin")
    st.caption(f"Connecté en tant que: **{nom_affiche}**")
    if st.button("Se déconnecter", key="logout"):
        st.session_state.logged_in = False
        st.rerun()
    st.markdown("---")
    menu = st.radio("Navigation", ["Tableaux de bord", "Entrées / Sorties", "Inventaire", "Base de données"])

df = st.session_state.df_stock
inv = st.session_state.df_inventaire

# ------------------------------------------
# ONGLET 1 : TABLEAUX DE BORD (DASHBOARD)
# ------------------------------------------
if menu == "Tableaux de bord":
    st.markdown(f'<h1>{icon("bar-chart", 30, "#1e3c72")} Tableau de Bord des Stocks</h1>', unsafe_allow_html=True)
    st.markdown("Visualisez en temps réel l'état et les mouvements de votre stock.")
    
    # Calcul des indicateurs clés (KPIs)
    total_mouvements = len(df)
    total_entrees = df[df['Type'] == 'Entrée']['Quantite'].sum()
    total_sorties = df[df['Type'] == 'Sortie']['Quantite'].sum()
    
    # Affichage des KPIs stylisés
    kpi1, kpi2, kpi3 = st.columns(3)
    with kpi1:
        st.markdown(f"""
            <div class='metric-card blue'>
                <p style='color:#555; font-size:14px; margin:0;'>TOTAL ENTRÉES</p>
                <h2 style='margin:5px 0 0 0; color:#2a5298; font-size:22px; white-space:nowrap;'>{icon("trending-up", 24, "#2a5298")} {total_entrees} unités</h2>
            </div>
        """, unsafe_allow_html=True)
    with kpi2:
        st.markdown(f"""
            <div class='metric-card'>
                <p style='color:#555; font-size:14px; margin:0;'>TOTAL SORTIES</p>
                <h2 style='margin:5px 0 0 0; color:#ff416c; font-size:22px; white-space:nowrap;'>{icon("trending-down", 24, "#ff416c")} {total_sorties} unités</h2>
            </div>
        """, unsafe_allow_html=True)
    with kpi3:
        st.markdown(f"""
            <div class='metric-card blue'>
                <p style='color:#555; font-size:14px; margin:0;'>TOTAL TRANSACTIONS</p>
                <h2 style='margin:5px 0 0 0; color:#1e3c72; font-size:22px; white-space:nowrap;'>{icon("refresh", 24, "#1e3c72")} {total_mouvements} opérations</h2>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    # Graphiques avec Plotly (Couleurs adaptées)
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        st.markdown(f'<h3>{icon("package", 22, "#1e3c72")} Volume des Flux par Produit</h3>', unsafe_allow_html=True)
        if not df.empty:
            fig_bar = px.bar(
                df, x="Produit", y="Quantite", color="Type",
                barmode="group",
                color_discrete_map={'Entrée': '#2a5298', 'Sortie': '#ff416c'},
                template="plotly_white"
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            empty_state("Aucune donnée disponible.", "package")
            
    with chart_col2:
        st.markdown(f'<h3>{icon("tag", 22, "#1e3c72")} Répartition par Catégorie</h3>', unsafe_allow_html=True)
        if not df.empty:
            fig_pie = px.pie(
                df, names="Categorie", values="Quantite",
                color_discrete_sequence=['#2a5298', '#ff416c', '#00c9ff', '#92fe9d'],
                hole=0.4,
                template="plotly_white"
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            empty_state("Aucune donnée disponible.", "tag")

# ------------------------------------------
# ONGLET 2 : ENTRÉES / SORTIES (FORMULAIRE)
# ------------------------------------------
elif menu == "Entrées / Sorties":
    st.markdown(f'<h1>{icon("arrow-lr", 30, "#1e3c72")} Enregistrer un Flux de Stock</h1>', unsafe_allow_html=True)
    st.markdown("Utilisez ce formulaire pour ajouter une entrée ou une sortie de marchandise.")
    
    produits_connus = sorted(inv['produit'].dropna().unique().tolist()) if not inv.empty else []
    categories_connues = sorted(inv['categorie'].dropna().unique().tolist()) if not inv.empty else ["Électronique", "Accessoires", "Mobilier", "Autre"]

    with st.form("stock_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            type_mvt = st.selectbox("Type de mouvement", ["Entrée", "Sortie"])
            if produits_connus:
                choix_produit = st.selectbox("Produit", produits_connus + ["➕ Nouveau produit..."])
                if choix_produit == "➕ Nouveau produit...":
                    produit = st.text_input("Nom du nouveau produit", placeholder="Ex: Écran Asus 27\"")
                else:
                    produit = choix_produit
            else:
                produit = st.text_input("Nom du produit", placeholder="Ex: Écran Asus 27\"")
            # Pré-sélectionne la catégorie connue du produit si elle existe
            cat_defaut = None
            if not inv.empty and produit in inv['produit'].values:
                cat_defaut = inv.loc[inv['produit'] == produit, 'categorie'].iloc[0]
            categorie = st.selectbox(
                "Catégorie", categories_connues,
                index=categories_connues.index(cat_defaut) if cat_defaut in categories_connues else 0
            )
        with col2:
            quantite = st.number_input("Quantité", min_value=1, step=1, value=1)
            date_mvt = st.date_input("Date de l'opération", datetime.now().date())
            motif = st.selectbox("Motif", ["Vente", "Livraison client", "Utilisation interne", "Retour fournisseur", "Transfert agence", "Casse/Perte", "Autre"])

        submit_btn = st.form_submit_button("Valider l'opération")

        if submit_btn:
            if produit.strip() == "":
                st.error("Veuillez entrer le nom du produit.")
            else:
                utilisateur_courant = st.session_state.get("current_user", "inconnu")
                # Ajout de la nouvelle ligne dans l'historique des mouvements
                new_row = pd.DataFrame([{
                    "Date": date_mvt,
                    "Type": type_mvt,
                    "Produit": produit,
                    "Quantite": quantite,
                    "Categorie": categorie,
                    "Motif": motif,
                    "Utilisateur": utilisateur_courant
                }])

                st.session_state.df_stock = pd.concat([df, new_row], ignore_index=True)
                save_data(st.session_state.df_stock)

                # Mise à jour du niveau de stock dans l'inventaire (stock.csv)
                inv_updated = st.session_state.df_inventaire.copy()
                if produit in inv_updated['produit'].values:
                    delta = quantite if type_mvt == "Entrée" else -quantite
                    inv_updated.loc[inv_updated['produit'] == produit, 'quantite'] += delta
                else:
                    nouvel_id = int(inv_updated['id'].max()) + 1 if not inv_updated.empty else 1
                    nouvelle_ligne = pd.DataFrame([{
                        "id": nouvel_id, "produit": produit, "categorie": categorie,
                        "quantite": quantite if type_mvt == "Entrée" else 0,
                        "seuil_alerte": 5, "prix_unitaire": 0, "fournisseur": "À définir"
                    }])
                    inv_updated = pd.concat([inv_updated, nouvelle_ligne], ignore_index=True)
                inv_updated['quantite'] = inv_updated['quantite'].clip(lower=0)
                st.session_state.df_inventaire = inv_updated
                inv_updated.to_csv(INVENTAIRE_FILE, index=False)

                st.success(f"Opération enregistrée avec succès : {type_mvt} de {quantite} {produit}")
                st.rerun()

# ------------------------------------------
# ONGLET 3 : INVENTAIRE (NIVEAUX DE STOCK ACTUELS)
# ------------------------------------------
elif menu == "Inventaire":
    st.markdown(f'<h1>{icon("package", 30, "#1e3c72")} Inventaire des Produits</h1>', unsafe_allow_html=True)
    st.markdown("Niveaux de stock actuels, seuils d'alerte et valorisation de l'inventaire.")

    if not inv.empty:
        inv_display = inv.copy()
        inv_display["Valeur totale"] = inv_display["quantite"] * inv_display["prix_unitaire"]
        inv_display["stock_bas"] = inv_display["quantite"] <= inv_display["seuil_alerte"]

        kpi1, kpi2, kpi3 = st.columns(3)
        with kpi1:
            st.markdown(f"""
                <div class='metric-card blue'>
                    <p style='color:#555; font-size:14px; margin:0;'>PRODUITS RÉFÉRENCÉS</p>
                    <h2 style='margin:5px 0 0 0; color:#2a5298; font-size:22px;'>{icon("package", 24, "#2a5298")} {len(inv_display)}</h2>
                </div>
            """, unsafe_allow_html=True)
        with kpi2:
            nb_alertes = (inv_display["quantite"] <= inv_display["seuil_alerte"]).sum()
            st.markdown(f"""
                <div class='metric-card'>
                    <p style='color:#555; font-size:14px; margin:0;'>PRODUITS EN ALERTE</p>
                    <h2 style='margin:5px 0 0 0; color:#ff416c; font-size:22px;'>{icon("trending-down", 24, "#ff416c")} {nb_alertes}</h2>
                </div>
            """, unsafe_allow_html=True)
        with kpi3:
            valeur_totale = inv_display["Valeur totale"].sum()
            st.markdown(f"""
                <div class='metric-card blue'>
                    <p style='color:#555; font-size:14px; margin:0;'>VALEUR TOTALE DU STOCK</p>
                    <h2 style='margin:5px 0 0 0; color:#1e3c72; font-size:22px;'>{icon("database", 24, "#1e3c72")} {valeur_totale:,.0f} DH</h2>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        recherche_inv = st.text_input("🔍 Rechercher un produit dans l'inventaire...", "")
        if recherche_inv:
            inv_display = inv_display[inv_display["produit"].str.contains(recherche_inv, case=False, na=False)]

        # Construction du tableau HTML (permet d'afficher une vraie bulle
        # colorée pour l'alerte, ce que st.dataframe ne peut pas faire).
        # IMPORTANT : pas d'indentation sur les lignes de la chaîne HTML,
        # sinon st.markdown interprète ces lignes comme un bloc de code
        # (règle Markdown : ligne indentée de 4+ espaces = code brut)
        # et affiche les balises telles quelles au lieu de les rendre.
        lignes_html = ""
        for _, r in inv_display.iterrows():
            if r["stock_bas"]:
                badge = '<span class="badge badge-red">🔴 Stock bas</span>'
            else:
                badge = '<span class="badge badge-green">🟢 OK</span>'
            lignes_html += (
                "<tr>"
                f"<td>{r['produit']}</td>"
                f"<td>{r['categorie']}</td>"
                f"<td>{r['quantite']}</td>"
                f"<td>{r['seuil_alerte']}</td>"
                f"<td>{r['prix_unitaire']:,.0f} DH</td>"
                f"<td>{r['fournisseur']}</td>"
                f"<td>{r['Valeur totale']:,.0f} DH</td>"
                f"<td>{badge}</td>"
                "</tr>"
            )

        table_html = (
            '<table class="custom-table"><thead><tr>'
            "<th>Produit</th><th>Catégorie</th><th>Quantité</th>"
            "<th>Seuil d'alerte</th><th>Prix unitaire</th>"
            "<th>Fournisseur</th><th>Valeur totale</th><th>Alerte</th>"
            f"</tr></thead><tbody>{lignes_html}</tbody></table>"
        )
        st.markdown(table_html, unsafe_allow_html=True)
    else:
        empty_state("Aucun produit dans l'inventaire.", "package")

# ------------------------------------------
# ONGLET 4 : BASE DE DONNÉES (HISTORIQUE)
# ------------------------------------------
elif menu == "Base de données":
    st.markdown(f'<h1>{icon("database", 30, "#1e3c72")} Historique des Mouvements</h1>', unsafe_allow_html=True)
    st.markdown("Consultez et gérez l'ensemble des données enregistrées dans le fichier CSV.")
    
    if not df.empty:
        # Filtre rapide
        search = st.text_input("🔍 Rechercher un produit...", "")
        if search:
            filtered_df = df[df['Produit'].str.contains(search, case=False, na=False)]
        else:
            filtered_df = df
            
        # Affichage du tableau interactif (Motif/Utilisateur masqués, conservés dans le CSV)
        st.dataframe(filtered_df.drop(columns=["Motif", "Utilisateur"]), use_container_width=True)
        
        # Option de réinitialisation complète
        st.markdown("<br><br>", unsafe_allow_html=True)
        if st.button("⚠️ Réinitialiser toutes les données"):
            empty_df = pd.DataFrame(columns=BASE_COLS)
            st.session_state.df_stock = empty_df
            save_data(empty_df)
            st.warning("Toutes les données ont été effacées.")
            st.rerun()
    else:
        empty_state("La base de données est actuellement vide.", "database")