import streamlit as st
import pandas as pd
from io import BytesIO
from supabase import create_client, Client

# ------------------------ CONFIG SUPABASE ------------------------
url = "https://bpagbbmedpgbbfxphpkx.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJwYWdiYm1lZHBnYmJmeHBocGt4Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MzU0NjE5NSwiZXhwIjoyMDY5MTIyMTk1fQ.pud2b5eGOxIam03D_iJUjE1Jz55G3jlZorUvvx8E0uk"
supabase: Client = create_client(url, key)

# ------------------------ CHARGEMENT DES DONNÉES ------------------------
@st.cache_data(ttl=3600)
def load_data():
    response = supabase.table("donnees_mna").select("*").limit(100000).execute()
    return pd.DataFrame(response.data)

df = load_data()

# ------------------------ UI ------------------------
st.title("📊 Screening M&A – comparables boursiers")

# Multiselects
selected_regions = st.multiselect("🌍 Région(s)", sorted(df["Région"].dropna().unique().tolist()))
selected_pays = st.multiselect("🏳️ Pays", sorted(df["Pays"].dropna().unique().tolist()))
selected_secteurs = st.multiselect("🏭 Secteur(s)", sorted(df["Secteur"].dropna().unique().tolist()))

# Sélection du critère (poste) pour filtrer
postes_dispo = sorted(df["Poste"].dropna().unique().tolist())
critere = st.selectbox("📈 Critère de filtrage (ex: EBITDA, CA…)", postes_dispo)

# Conversion en numérique + gestion NaN
col_numerique = pd.to_numeric(df[df["Poste"] == critere]["2024"], errors="coerce")

# Slider Min/Max
min_val = st.number_input("🔽 Valeur min (2024)", value=float(col_numerique.min(skipna=True)), step=1.0)
max_val = st.number_input("🔼 Valeur max (2024)", value=float(col_numerique.max(skipna=True)), step=1.0)

# ------------------------ FILTRAGE ------------------------
# Étape 1 : filtrer sur la ligne du critère uniquement
df_critere = df[df["Poste"] == critere].copy()
df_critere["Valeur2024"] = pd.to_numeric(df_critere["2024"], errors="coerce")

filtre = (
    df_critere["Valeur2024"] >= min_val
) & (
    df_critere["Valeur2024"] <= max_val
)

if selected_regions:
    filtre &= df_critere["Région"].isin(selected_regions)
if selected_pays:
    filtre &= df_critere["Pays"].isin(selected_pays)
if selected_secteurs:
    filtre &= df_critere["Secteur"].isin(selected_secteurs)

entreprises_filtrees = df_critere[filtre]["Entreprise"].unique()

# Étape 2 : on récupère toutes les lignes pour ces entreprises
df_filtre = df[df["Entreprise"].isin(entreprises_filtrees)].copy()

st.success(f"{len(entreprises_filtrees)} entreprise(s) trouvée(s), {len(df_filtre)} ligne(s) affichée(s)")
st.dataframe(df_filtre)

# ------------------------ EXPORT EXCEL ------------------------
@st.cache_data
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Résultats")
    return output.getvalue()

if not df_filtre.empty:
    xlsx = to_excel(df_filtre)
    st.download_button(
        label="📥 Télécharger Excel",
        data=xlsx,
        file_name="resultats_mna.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
