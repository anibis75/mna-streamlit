import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="M&A Screening", layout="wide")

# === Charger les données
@st.cache_data
def load_data():
    df = pd.read_csv("Zonebourse_chunk_1_compte.csv", sep=";")
    df = df.astype(object).where(pd.notnull(df), None)
    return df

df = load_data()

st.title("💼 Screening M&A – Comparables Boursiers")

# === Colonnes utiles
liste_annees = [col for col in df.columns if col.isdigit()]
liste_postes = sorted(df["Poste"].dropna().unique())
liste_regions = sorted(df["Région"].dropna().unique())
liste_pays = sorted(df["Pays"].dropna().unique())

# === FILTRES
st.sidebar.header("🔍 Filtres comparables")

poste_pivot = st.sidebar.selectbox("Poste pivot (filtrage)", liste_postes)
annee = st.sidebar.selectbox("Année de référence", liste_annees)
val_min = st.sidebar.number_input(f"Valeur min ({annee})", value=0.0)
val_max = st.sidebar.number_input(f"Valeur max ({annee})", value=1e9)

regions = st.sidebar.multiselect("🌍 Région(s)", options=liste_regions, default=liste_regions)
pays = st.sidebar.multiselect("🇺🇳 Pays", options=liste_pays, default=liste_pays)

# === Étape 1 : Filtrer les entreprises matching
df_filtered = df[
    (df["Poste"] == poste_pivot) &
    (df["Région"].isin(regions)) &
    (df["Pays"].isin(pays))
].copy()

df_filtered[annee] = pd.to_numeric(df_filtered[annee], errors="coerce")
df_filtered = df_filtered[
    (df_filtered[annee] >= val_min) &
    (df_filtered[annee] <= val_max)
]

entreprises_match = df_filtered["Entreprise"].dropna().unique()

# === Étape 2 : Extraire toutes les lignes des entreprises retenues
df_final = df[df["Entreprise"].isin(entreprises_match)]

st.markdown(f"✅ **{len(entreprises_match)} entreprises sélectionnées** – {len(df_final)} lignes affichées")
st.dataframe(df_final, use_container_width=True)

# === EXPORT
if not df_final.empty:
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df_final.to_excel(writer, index=False, sheet_name="Résultats")

    buffer.seek(0)
    st.download_button(
        label="📥 Télécharger Excel",
        data=buffer,
        file_name="comparables_mna.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
