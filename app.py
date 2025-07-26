import streamlit as st
import pandas as pd
from supabase import create_client
from io import BytesIO

# ------------------ CONFIG SUPABASE ------------------

url = "https://bpagbbmedpgbbfxphpkx.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJwYWdiYm1lZHBnYmJmeHBocGt4Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MzU0NjE5NSwiZXhwIjoyMDY5MTIyMTk1fQ.pud2b5eGOxIam03D_iJUjE1Jz55G3jlZorUvvx8E0uk"
supabase = create_client(url, key)

# ------------------ EXPORT EXCEL ------------------

@st.cache_data
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Résultats')
    return output.getvalue()

# ------------------ CHARGEMENT ------------------

st.title("🕵️ Screening M&A interactif")

with st.spinner("Chargement des données..."):
    data = supabase.table("donnees_mna").select("*").limit(100000).execute()
    df = pd.DataFrame(data.data or [])

if df.empty:
    st.error("❌ Erreur : aucune donnée chargée depuis Supabase.")
    st.stop()

# ------------------ FILTRES ------------------

col1, col2 = st.columns(2)

with col1:
    region = st.selectbox("🌍 Région", [""] + sorted(df["Région"].dropna().unique().tolist()))
with col2:
    pays = st.selectbox("🏳️ Pays", [""] + sorted(df["Pays"].dropna().unique().tolist()))

annees_disponibles = [col for col in df.columns if col.isnumeric()]
annee_ref = st.selectbox("📅 Année de filtrage sur le CA", sorted(annees_disponibles, reverse=True))
min_val = st.number_input("💰 Valeur minimale (CA)", value=0.0)

# ------------------ LOGIQUE DE FILTRAGE ------------------

df_ca = df[df["Poste"] == "Chiffre d'affaires"]
if region:
    df_ca = df_ca[df_ca["Région"] == region]
if pays:
    df_ca = df_ca[df_ca["Pays"] == pays]
df_ca = df_ca[pd.to_numeric(df_ca[annee_ref], errors="coerce") >= min_val]

entreprises_retenues = df_ca["Entreprise"].unique()
df_filtre = df[df["Entreprise"].isin(entreprises_retenues)]

# ------------------ AFFICHAGE ------------------

st.success(f"✅ {len(entreprises_retenues)} entreprise(s) retenue(s)")
st.dataframe(df_filtre)

# ------------------ EXPORT ------------------

if not df_filtre.empty:
    xlsx = to_excel(df_filtre)
    st.download_button(
        label="📥 Télécharger en .xlsx",
        data=xlsx,
        file_name="resultats_mna.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
