from pathlib import Path
import pandas as pd
import streamlit as st
from io import BytesIO

# ========== CONFIGURATION ==========
CSV_PATH = Path("Zonebourse_chunk_1_compte.csv")

# ========== CHARGEMENT DU CSV ==========
@st.cache_data
def load_data():
    df = pd.read_csv(CSV_PATH, sep=";", dtype=str)
    df.iloc[:, 8:] = df.iloc[:, 8:].apply(pd.to_numeric, errors="coerce")
    return df

df = load_data()

# ========== INTERFACE ==========
st.title("🧠 Screening M&A – Comparables boursiers")

# === MENUS DEROULANTS ===
regions = sorted(df["Région"].dropna().unique())
pays = sorted(df["Pays"].dropna().unique())
postes = sorted(df["Poste"].dropna().unique())
annees = [col for col in df.columns if col.isnumeric()]

col1, col2 = st.columns(2)
with col1:
    region_choisie = st.multiselect("🌍 Région(s)", regions, default=regions)
with col2:
    pays_choisis = st.multiselect("🏳️ Pays", pays, default=pays)

postes_choisis = st.multiselect("📊 Postes à filtrer (pour le screening)", postes)
filtre_poste = {}

# === FILTRES MULTIPLES PAR POSTE ===
if postes_choisis:
    for poste in postes_choisis:
        st.markdown(f"### 🎯 Critères pour : {poste}")
        col3, col4, col5 = st.columns(3)
        with col3:
            annee = st.selectbox(f"Année pour {poste}", annees, key=poste)
        with col4:
            min_val = st.number_input(f"Min ({annee})", value=0.0, key=f"{poste}_min")
        with col5:
            max_val = st.number_input(f"Max ({annee})", value=1e12, key=f"{poste}_max")
        filtre_poste[poste] = (annee, min_val, max_val)

# ========== FILTRAGE ==========
df_filtre = df[
    (df["Région"].isin(region_choisie)) &
    (df["Pays"].isin(pays_choisis))
]

if filtre_poste:
    entreprises_valides = set(df_filtre["Entreprise"].unique())
    for poste, (annee, min_val, max_val) in filtre_poste.items():
        entreprises_filtrees = df_filtre[
            (df_filtre["Poste"] == poste) &
            (df_filtre[annee] >= min_val) &
            (df_filtre[annee] <= max_val)
        ]["Entreprise"].unique()
        entreprises_valides = entreprises_valides.intersection(entreprises_filtrees)
    df_filtre = df_filtre[df_filtre["Entreprise"].isin(entreprises_valides)]

# ========== AFFICHAGE ==========
st.success(f"{len(df_filtre)} lignes affichées")
st.dataframe(df_filtre)

# ========== EXPORT XLSX ==========
@st.cache_data
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name="Filtrage M&A")
    processed_data = output.getvalue()
    return processed_data

xlsx = to_excel(df_filtre)

st.download_button(
    label="📥 Télécharger Excel propre (.xlsx)",
    data=xlsx,
    file_name="comparables_filtrés.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
