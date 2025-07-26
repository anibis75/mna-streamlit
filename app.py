import streamlit as st
import pandas as pd
from io import BytesIO
from supabase import create_client, Client

# === CONFIGURATION SUPABASE ===
url = "https://bpagbbmedpgbbfxphpkx.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJwYWdiYm1lZHBnYmJmeHBocGt4Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MzU0NjE5NSwiZXhwIjoyMDY5MTIyMTk1fQ.pud2b5eGOxIam03D_iJUjE1Jz55G3jlZorUvvx8E0uk"
supabase: Client = create_client(url, key)

# === CHARGEMENT DES DONNÉES ===
@st.cache_data
def load_data():
    response = supabase.table("donnees_mna").select("*").range(0, 25528).execute()
    return pd.DataFrame(response.data)

df = load_data()

# === UI STREAMLIT ===
st.title("📊 Screening M&A interactif")

# Filtres géographiques
regions = st.multiselect("🌍 Région(s)", sorted(df["Région"].dropna().unique()))
pays = st.multiselect("🏳️ Pays", sorted(df["Pays"].dropna().unique()))
secteurs = st.multiselect("🏭 Secteur(s)", sorted(df["Secteur"].dropna().unique()))

# Filtrage de base
df_filtré = df.copy()

if regions:
    df_filtré = df_filtré[df_filtré["Région"].isin(regions)]
if pays:
    df_filtré = df_filtré[df_filtré["Pays"].isin(pays)]
if secteurs:
    df_filtré = df_filtré[df_filtré["Secteur"].isin(secteurs)]

# Filtres par postes financiers
postes_numeriques = ["2020", "2021", "2022", "2023", "2024", "2025", "2026", "2027"]
liste_postes = sorted(df_filtré["Poste"].dropna().unique())
critere = st.selectbox("📌 Choisir un poste financier de filtrage", liste_postes)

if critere:
    annee = st.selectbox("📅 Année", postes_numeriques)
    df_tmp = df_filtré[df_filtré["Poste"] == critere]
    min_val = float(df_tmp[annee].dropna().min())
    max_val = float(df_tmp[annee].dropna().max())
    borne_min = st.number_input("Valeur minimale", value=min_val, step=1.0)
    borne_max = st.number_input("Valeur maximale", value=max_val, step=1.0)

    entreprises_filtrées = df_tmp[
        (df_tmp[annee].astype(float) >= borne_min) & (df_tmp[annee].astype(float) <= borne_max)
    ]["Entreprise"].unique()

    df_filtré = df_filtré[df_filtré["Entreprise"].isin(entreprises_filtrées)]

st.markdown(f"### Résultats : {len(df_filtré)} lignes")

st.dataframe(df_filtré, use_container_width=True)

# EXPORT XLSX
@st.cache_data
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Données filtrées')
    return output.getvalue()

xlsx = to_excel(df_filtré)
st.download_button("📥 Exporter en XLSX", xlsx, "filtrage_mna.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
