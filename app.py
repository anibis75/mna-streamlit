import streamlit as st
import pandas as pd
import io

# === Charger les données
@st.cache_data
def load_data():
    df = pd.read_csv("Zonebourse_chunk_1_compte.csv", sep=";")
    df = df.astype(object).where(pd.notnull(df), None)
    return df

df = load_data()

st.title("📊 Outil M&A – Filtrage + Export Excel")

# === Filtres actifs
poste = st.selectbox("Poste", sorted(df["Poste"].dropna().unique()))
annee = st.selectbox("Année", [str(col) for col in df.columns if col.isdigit()])
min_value = st.number_input(f"Valeur min ({annee})", value=0.0)
max_value = st.number_input(f"Valeur max ({annee})", value=1e9)

# === Application du filtrage
filtered_df = df[df["Poste"] == poste]
filtered_df[annee] = pd.to_numeric(filtered_df[annee], errors="coerce")
filtered_df = filtered_df[(filtered_df[annee] >= min_value) & (filtered_df[annee] <= max_value)]

st.success(f"{len(filtered_df)} lignes affichées")
st.dataframe(filtered_df, use_container_width=True)

# === Export Excel
if not filtered_df.empty:
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        filtered_df.to_excel(writer, index=False, sheet_name="Résultats")
    buffer.seek(0)
    st.download_button(
        label="📥 Télécharger Excel",
        data=buffer,
        file_name="export_mna.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
