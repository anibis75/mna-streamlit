import streamlit as st
import pandas as pd
from supabase import create_client, Client
from io import BytesIO
import xlsxwriter

# --- CONFIGURATION SUPABASE ---
url = "https://bpagbbmedpgbbfxphpkx.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJwYWdiYm1lZHBnYmJmeHBocGt4Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MzU0NjE5NSwiZXhwIjoyMDY5MTIyMTk1fQ.pud2b5eGOxIam03D_iJUjE1Jz55G3jlZorUvvx8E0uk"
supabase: Client = create_client(url, key)

st.set_page_config(page_title="M&A Screener", layout="wide")
st.title("🔍 Outil de screening M&A")

# --- CHARGEMENT DES DONNÉES ---
@st.cache_data(show_spinner=True)
def load_data():
    data = supabase.table("donnees_mna").select("*").limit(100000).execute()
    df = pd.DataFrame(data.data)
    return df

if st.button("🔄 Actualiser les données"):
    st.cache_data.clear()

df = load_data()

# --- INTERFACES DE FILTRAGE ---
with st.sidebar:
    st.header("🎯 Filtres")

    # Région
    regions = sorted(df["Région"].dropna().unique())
    selected_regions = st.multiselect("Régions", regions, default=regions)

    # Pays
    pays = sorted(df["Pays"].dropna().unique())
    selected_pays = st.multiselect("Pays", pays, default=pays)

    # Secteurs
    secteurs = sorted(df["Secteur"].dropna().unique())
    selected_secteurs = st.multiselect("Secteurs", secteurs, default=secteurs)

    # Choix du critère numérique
    colonnes_numeriques = [col for col in df.columns if col.isnumeric()]
    critere = st.selectbox("Critère de filtrage principal", colonnes_numeriques)
    min_val = st.number_input("Valeur min", value=float(df[critere].min()), step=1.0)
    max_val = st.number_input("Valeur max", value=float(df[critere].max()), step=1.0)

# --- FILTRAGE DES DONNÉES ---
entreprises_filtrees = df[
    (df["Région"].isin(selected_regions)) &
    (df["Pays"].isin(selected_pays)) &
    (df["Secteur"].isin(selected_secteurs)) &
    (df[critere] >= min_val) &
    (df[critere] <= max_val)
]["Entreprise"].unique()

df_filtre = df[df["Entreprise"].isin(entreprises_filtrees)]

# --- AFFICHAGE ---
st.markdown(f"### Résultat : {len(df_filtre)} lignes")
st.dataframe(df_filtre, use_container_width=True)

# --- EXPORT EXCEL ---
@st.cache_data
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Filtré')
        writer.save()
    return output.getvalue()

xlsx = to_excel(df_filtre)
st.download_button("📥 Télécharger Excel", xlsx, "resultat_filtré.xlsx")
