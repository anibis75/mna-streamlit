import streamlit as st
import pandas as pd
from supabase import create_client, Client
from io import BytesIO
import xlsxwriter

# Connexion à Supabase
url = "https://bpagbbmedpgbbfxphpkx.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJwYWdiYm1lZHBnYmJmeHBocGt4Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MzU0NjE5NSwiZXhwIjoyMDY5MTIyMTk1fQ.pud2b5eGOxIam03D_iJUjE1Jz55G3jlZorUvvx8E0uk"
supabase: Client = create_client(url, key)

# Import des données Supabase
@st.cache_data
def load_data():
    res = supabase.table("donnees_mna").select("*").execute()
    return pd.DataFrame(res.data)

df = load_data()

st.title("📊 M&A Screening App - Tereos")

# Sélection multiple : régions, pays
regions = st.multiselect("🌍 Régions", options=sorted(df["Région"].dropna().unique()))
pays = st.multiselect("🏳️ Pays", options=sorted(df["Pays"].dropna().unique()))

# Critères disponibles pour filtre numérique
colonnes_annees = [col for col in df.columns if col.isdigit()]
poste_dispo = sorted(df["Poste"].dropna().unique())
criteres = st.multiselect("📈 Critères numériques (Postes)", options=poste_dispo)

# Construction filtre numérique
filtres_numeriques = {}
for crit in criteres:
    col_cible = st.selectbox(f"📅 Année pour le critère : {crit}", colonnes_annees, key=f"{crit}_annee")
    min_val = st.number_input(f"🔽 Min {crit} ({col_cible})", value=0.0, key=f"{crit}_min")
    max_val = st.number_input(f"🔼 Max {crit} ({col_cible})", value=1e12, key=f"{crit}_max")
    filtres_numeriques[(crit, col_cible)] = (min_val, max_val)

# Application des filtres
df_filtre = df.copy()

if regions:
    df_filtre = df_filtre[df_filtre["Région"].isin(regions)]

if pays:
    df_filtre = df_filtre[df_filtre["Pays"].isin(pays)]

# Filtrage sur les entreprises qui vérifient tous les critères numériques
if filtres_numeriques:
    entreprises_valides = set(df_filtre["Entreprise"].unique())
    for (poste, annee), (vmin, vmax) in filtres_numeriques.items():
        subset = df_filtre[
            (df_filtre["Poste"] == poste) &
            (df_filtre[annee].apply(pd.to_numeric, errors='coerce').between(vmin, vmax))
        ]
        entreprises_valides &= set(subset["Entreprise"].unique())
    df_filtre = df_filtre[df_filtre["Entreprise"].isin(entreprises_valides)]

st.markdown(f"### Résultat : {df_filtre.shape[0]} lignes sélectionnées")
st.dataframe(df_filtre, use_container_width=True)

# Export Excel
@st.cache_data
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Résultat')
    return output.getvalue()

xlsx = to_excel(df_filtre)
st.download_button(
    label="📥 Télécharger en .xlsx",
    data=xlsx,
    file_name="screening_mna.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
