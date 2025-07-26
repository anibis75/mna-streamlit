import streamlit as st
import pandas as pd
from supabase import create_client

# === CONFIG SUPABASE ===
SUPABASE_URL = "https://bpagbbmedpgbbfxphpkx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJwYWdiYm1lZHBnYmJmeHBocGt4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM1NDYxOTUsImV4cCI6MjA2OTEyMjE5NX0.9najNtOfvPHtpA9aKqy56F15dqIZAcX-sA1GfNBzN68"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# === CHARGEMENT DES DONNÉES ===
@st.cache_data
def charger_donnees():
    response = supabase.table("donnees_mna").select("*").execute()
    return pd.DataFrame(response.data)

df = charger_donnees()

# === INTERFACE ===
st.title("Screening M&A 📊")

col1, col2 = st.columns(2)

with col1:
    region = st.selectbox("Région", [""] + sorted(df["Région"].dropna().unique().tolist()))
    pays = st.multiselect("Pays", sorted(df["Pays"].dropna().unique().tolist()))

with col2:
    poste_ref = st.selectbox("Poste de référence pour filtrage (ex: Chiffre d'affaires)", sorted(df["Poste"].unique()))
    annee = st.selectbox("Année", ["2020", "2021", "2022", "2023", "2024", "2025", "2026", "2027"])
    min_val = st.number_input(f"Valeur min. ({annee})", value=0.0)
    max_val = st.number_input(f"Valeur max. ({annee})", value=1e12)

# === FILTRAGE ===
df_filtre = df.copy()

if region:
    df_filtre = df_filtre[df_filtre["Région"] == region]

if pays:
    df_filtre = df_filtre[df_filtre["Pays"].isin(pays)]

if poste_ref and annee:
    entreprises_filtrees = df_filtre[
        (df_filtre["Poste"] == poste_ref) &
        (df_filtre[annee].astype(float) >= min_val) &
        (df_filtre[annee].astype(float) <= max_val)
    ]["Entreprise"].unique()
    df_filtre = df_filtre[df_filtre["Entreprise"].isin(entreprises_filtrees)]

# === AFFICHAGE ===
st.write(f"Résultats filtrés : {len(df_filtre)} lignes")
st.dataframe(df_filtre)

# === EXPORT EXCEL ===
@st.cache_data
def to_excel(df):
    from io import BytesIO
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Résultats')
    return output.getvalue()

st.download_button(
    label="📥 Télécharger en Excel",
    data=to_excel(df_filtre),
    file_name="resultats_filtrés.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
