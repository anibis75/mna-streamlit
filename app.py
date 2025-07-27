import os
import streamlit as st
import pandas as pd
from io import BytesIO
from supabase import create_client, Client

# === CONFIGURATION SUPABASE ===============================================
url = os.getenv("SUPABASE_URL") or "https://bpagbbmedpgbbfxphpkx.supabase.co"
key = os.getenv("SUPABASE_ANON_KEY") or "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJwYWdiYm1lZHBnYmJmeHBocGt4Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MzU0NjE5NSwiZXhwIjoyMDY5MTIyMTk1fQ.pud2b5eGOxIam03D_iJUjE1Jz55G3jlZorUvvx8E0uk"
supabase: Client = create_client(url, key)

# === CHARGEMENT DES DONNÉES ===============================================
@st.cache_data(show_spinner="📥 Chargement des données…")
def load_data(batch_size: int = 10_000) -> pd.DataFrame:
    rows, start = [], 0
    while True:
        end = start + batch_size - 1
        resp = (
            supabase.table("donnees_mna")
            .select("*")
            .range(start, end)
            .execute()
        )
        data = resp.data or []
        rows.extend(data)
        if len(data) < batch_size:
            break
        start += batch_size
    df = pd.DataFrame(rows)
    year_cols = [c for c in df.columns if c.isdigit() and len(c) == 4]
    df[year_cols] = df[year_cols].apply(pd.to_numeric, errors="coerce")
    return df

df = load_data()

# === UI STREAMLIT ==========================================================
st.title("📊 Screening M&A interactif")

regions = st.multiselect("🌍 Région(s)", sorted(df["Région"].dropna().unique()))
pays     = st.multiselect("🏳️ Pays",      sorted(df["Pays"].dropna().unique()))
secteurs = st.multiselect("🏭 Secteur(s)",  sorted(df["Secteur"].dropna().unique()))

df_filtré = df
if regions:
    df_filtré = df_filtré[df_filtré["Région"].isin(regions)]
if pays:
    df_filtré = df_filtré[df_filtré["Pays"].isin(pays)]
if secteurs:
    df_filtré = df_filtré[df_filtré["Secteur"].isin(secteurs)]

liste_postes = sorted(df_filtré["Poste"].dropna().unique())
critere = st.selectbox("📌 Poste financier", liste_postes)

if critere:
    postes_numeriques = [c for c in df_filtré.columns if c.isdigit() and len(c) == 4]
    annee = st.selectbox("📅 Année", postes_numeriques)

    df_tmp = df_filtré[df_filtré["Poste"] == critere]
    vals = pd.to_numeric(df_tmp[annee], errors="coerce").dropna()

    if not vals.empty:
        min_val, max_val = float(vals.min()), float(vals.max())
        borne_min, borne_max = st.slider(
            "Plage de valeurs",
            min_value=min_val,
            max_value=max_val,
            value=(min_val, max_val),
            step=max((max_val - min_val) / 100, 1.0),
        )
        entreprises_filtrées = df_tmp[
            (vals >= borne_min) & (vals <= borne_max)
        ]["Entreprise"].unique()
        df_filtré = df_filtré[df_filtré["Entreprise"].isin(entreprises_filtrées)]
    else:
        st.warning("Aucune valeur numérique pour ce poste / année.")
        st.stop()

st.markdown(f"### Résultats : {len(df_filtré):,} lignes")
st.dataframe(df_filtré, use_container_width=True)

# === EXPORT XLSX ===========================================================
@st.cache_data
def to_excel(dframe: pd.DataFrame) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        dframe.to_excel(writer, index=False, sheet_name="Données filtrées")
    output.seek(0)
    return output.getvalue()

xlsx = to_excel(df_filtré)
st.download_button(
    "📥 Exporter en XLSX",
    data=xlsx,
    file_name="filtrage_mna.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)
