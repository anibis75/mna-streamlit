import streamlit as st
import pandas as pd
from supabase import create_client, Client
import io

# =================== CONFIG ===================
SUPABASE_URL = "https://bpagbbmedpgbbfxphpkx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJwYWdiYm1lZHBnYmJmeHBocGt4Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MzU0NjE5NSwiZXhwIjoyMDY5MTIyMTk1fQ.pud2b5eGOxIam03D_iJUjE1Jz55G3jlZorUvvx8E0uk"
TABLE_NAME = "donnees_mna"

# ================== INIT =====================
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
st.set_page_config(page_title="M&A Screener", layout="wide")

# ================== LOAD DATA =================
@st.cache_data(ttl=3600)
def load_data():
    response = supabase.table(TABLE_NAME).select("*").range(0, 22999).execute()
    return pd.DataFrame(response.data)

df = load_data()

# ================== UI ========================
st.title("📊 Screening M&A – Données Financières")
st.markdown("Filtrez les entreprises par **région, pays, secteur et critères financiers**.")

# Sélecteurs multiples
regions = st.multiselect("🌍 Régions", sorted(df["Région"].dropna().unique()))
pays = st.multiselect("🏳️ Pays", sorted(df["Pays"].dropna().unique()))
secteurs = st.multiselect("🏭 Secteurs", sorted(df["Secteur"].dropna().unique()))

# Choix du critère de filtrage numérique (facultatif)
critere = st.selectbox("📈 Critère numérique (optionnel)", [""] + [c for c in df.columns if c.isdigit()])

min_val, max_val = None, None
if critere:
    col1, col2 = st.columns(2)
    with col1:
        min_val = st.number_input("Valeur minimale", value=float(df[critere].dropna().min()), step=1.0)
    with col2:
        max_val = st.number_input("Valeur maximale", value=float(df[critere].dropna().max()), step=1.0)

# ================= FILTRAGE ====================
df_filtre = df.copy()

if regions:
    df_filtre = df_filtre[df_filtre["Région"].isin(regions)]
if pays:
    df_filtre = df_filtre[df_filtre["Pays"].isin(pays)]
if secteurs:
    df_filtre = df_filtre[df_filtre["Secteur"].isin(secteurs)]
if critere and min_val is not None and max_val is not None:
    entreprises_cible = df_filtre[
        df_filtre["Poste"].str.contains("chiffre d'affaires", case=False, na=False) &
        df_filtre[critere].between(min_val, max_val)
    ]["Entreprise"].unique()
    df_filtre = df_filtre[df_filtre["Entreprise"].isin(entreprises_cible)]

# ================ DISPLAY ======================
st.success(f"{len(df_filtre)} lignes affichées sur {len(df)}")
st.dataframe(df_filtre)

# ================ EXPORT =======================
@st.cache_data
def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Résultats')
    return output.getvalue()

st.download_button(
    label="📥 Télécharger les résultats (.xlsx)",
    data=to_excel(df_filtre),
    file_name="resultats_screening.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
