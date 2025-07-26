import streamlit as st
import pandas as pd
from supabase import create_client, Client

# ===================== SUPABASE CONFIG =====================
url = "https://bpagbbmedpgbbfxphpkx.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJwYWdiYm1lZHBnYmJmeHBocGt4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM1NDYxOTUsImV4cCI6MjA2OTEyMjE5NX0.9najNtOfvPHtpA9aKqy56F15dqIZAcX-sA1GfNBzN68"
supabase: Client = create_client(url, key)

# ===================== LECTURE DES DONNÉES =====================
@st.cache_data
def load_data():
    response = supabase.table("donnees_mna").select("*").execute()
    df = pd.DataFrame(response.data)
    return df

df = load_data()

# DEBUG: Affiche les colonnes et un aperçu pour diagnostiquer l'erreur
st.write("🧪 Colonnes détectées :", df.columns.tolist())
st.write("📊 Aperçu des données :", df.head())

# ===================== INTERFACE =====================
st.title("🕵️‍♂️ Screening M&A interactif")

# Choix Région
region = st.selectbox("🌍 Région", [""] + sorted(df["Région"].dropna().unique().tolist()))

# Choix Pays
pays = st.selectbox("🏳️ Pays", [""] + sorted(df["Pays"].dropna().unique().tolist()))

# Choix filtre poste + année + minimum
poste_filtre = st.selectbox("📌 Filtre basé sur le poste", [""] + sorted(df["Poste"].dropna().unique().tolist()))
annee = st.selectbox("📅 Année", [""] + [str(col) for col in df.columns if col.isdigit()])
min_val = st.number_input("📉 Valeur minimale pour le poste sélectionné", min_value=0.0, value=0.0)

# ===================== FILTRAGE =====================
if poste_filtre and annee:
    # Étape 1 : identifier les entreprises qui passent les filtres
    df_filtre_base = df[
        (df["Poste"] == poste_filtre) &
        (df[annee].astype(float) >= min_val)
    ]
    entreprises_filtrées = df_filtre_base["Entreprise"].unique().tolist()

    # Étape 2 : récupérer toutes les lignes de ces entreprises
    df_filtre = df[df["Entreprise"].isin(entreprises_filtrées)]

    # Filtrage optionnel Région/Pays
    if region:
        df_filtre = df_filtre[df_filtre["Région"] == region]
    if pays:
        df_filtre = df_filtre[df_filtre["Pays"] == pays]

    st.success(f"{len(df_filtre)} lignes affichées pour {len(entreprises_filtrées)} entreprises filtrées.")
    st.dataframe(df_filtre)

    # Export XLSX
    @st.cache_data
    def to_excel(df):
        from io import BytesIO
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='MNA_Filtered')
        return output.getvalue()

    xlsx = to_excel(df_filtre)
    st.download_button("⬇️ Télécharger en XLSX", xlsx, "filtered_data.xlsx")

else:
    st.info("📌 Choisis au minimum un poste, une année et une valeur pour filtrer.")

