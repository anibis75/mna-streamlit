import streamlit as st
import pandas as pd

# Chargement
st.title("🧠 Screening M&A – Comparables boursiers")

# Chargement du CSV
df = pd.read_csv("Zonebourse_chunk_1_compte.csv", sep=";")

# Nettoyage des noms de colonnes
df.columns = df.columns.str.strip()

# Affichage des colonnes détectées (debug temporaire)
st.write("🧪 Colonnes détectées :", df.columns.tolist())

# Filtres
liste_regions = sorted(df["Région"].dropna().unique())
liste_pays = sorted(df["Pays"].dropna().unique())
liste_postes = sorted(df["Poste"].dropna().unique())

region = st.multiselect("🌍 Région(s)", options=liste_regions)
pays = st.multiselect("🇺🇳 Pays", options=liste_pays)
poste = st.selectbox("📌 Poste pivot (filtrage sur valeur)", options=liste_postes)
annee = st.selectbox("📆 Année", options=[str(y) for y in range(2020, 2029)])

min_val = st.number_input("📉 Valeur minimale", value=0.0)
max_val = st.number_input("📈 Valeur maximale", value=1e9)

# Application des filtres
df_filtered = df.copy()

if region:
    df_filtered = df_filtered[df_filtered["Région"].isin(region)]
if pays:
    df_filtered = df_filtered[df_filtered["Pays"].isin(pays)]
if poste:
    df_filtered = df_filtered[df_filtered["Poste"] == poste]
if annee:
    df_filtered = df_filtered[df_filtered[annee].notna()]
    df_filtered = df_filtered[df_filtered[annee].astype(float).between(min_val, max_val)]

# Affichage
st.markdown(f"### Résultats : {len(df_filtered)} lignes")
st.dataframe(df_filtered, use_container_width=True)

# Téléchargement
csv = df_filtered.to_csv(index=False).encode("utf-8-sig")
st.download_button("📥 Télécharger CSV filtré", data=csv, file_name="resultats_filtrés.csv", mime="text/csv")
