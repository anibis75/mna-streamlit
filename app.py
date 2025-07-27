import os
import streamlit as st
import duckdb
import pandas as pd
from io import BytesIO

# ── MotherDuck connexion ──────────────────────────────────────────────────────
DB     = os.getenv("MD_DB", "my_db")
TOKEN  = os.getenv("MOTHERDUCK_TOKEN")  # export MOTHERDUCK_TOKEN="…"
TABLE  = 'main.zonebourse_chunk_compte'  # schéma.table

con = duckdb.connect(f"md:{DB}?motherduck_token={TOKEN}")

# ── Helpers SQL ───────────────────────────────────────────────────────────────
def sql_list(vals):
    return ",".join([f"'{v.replace('\'','\'\'')}'" for v in vals])

@st.cache_data(show_spinner="📥 Récupération des choix…")
def get_distinct(col):
    q = f'SELECT DISTINCT "{col}" FROM {TABLE} WHERE "{col}" IS NOT NULL ORDER BY 1'
    return [r[0] for r in con.execute(q).fetchall()]

def build_query(regions, pays, secteurs, poste, annee, borne_min, borne_max):
    where = ["1=1"]
    if regions:  where.append(f'"Région"  IN ({sql_list(regions)})')
    if pays:     where.append(f'"Pays"    IN ({sql_list(pays)})')
    if secteurs: where.append(f'"Secteur" IN ({sql_list(secteurs)})')
    if poste:
        where.append(f'"Poste" = \'{poste.replace("\'","\'\'")}\'')

        if annee and borne_min is not None and borne_max is not None:
            where.append(f'CAST("{annee}" AS DOUBLE) BETWEEN {borne_min} AND {borne_max}')
    clause = " AND ".join(where)
    return f'SELECT * FROM {TABLE} WHERE {clause}'

# ── UI Streamlit ──────────────────────────────────────────────────────────────
st.title("📊 Screening M&A interactif (MotherDuck)")

regions  = st.multiselect("🌍 Région(s)",  get_distinct("Région"))
pays     = st.multiselect("🏳️ Pays",       get_distinct("Pays"))
secteurs = st.multiselect("🏭 Secteur(s)", get_distinct("Secteur"))

liste_postes = get_distinct("Poste")
critere = st.selectbox("📌 Poste financier", liste_postes)

annee = None
borne_min = borne_max = None

if critere:
    year_cols = [c[0] for c in con.execute(
        f"PRAGMA table_info('{TABLE.split('.')[-1]}')").fetchall() if c[1].isdigit()]
    annee = st.selectbox("📅 Année", sorted(year_cols))

    if annee:
        vals = con.execute(
            f'SELECT MIN(CAST("{annee}" AS DOUBLE)), MAX(CAST("{annee}" AS DOUBLE)) '
            f'FROM {TABLE} WHERE "Poste" = \'{critere.replace("\'","\'\'")}\'' 
        ).fetchone()
        min_val, max_val = [float(x) if x is not None else 0.0 for x in vals]
        if min_val == max_val:
            st.info("Aucune plage pour cette année.")
        else:
            borne_min, borne_max = st.slider(
                "Plage de valeurs",
                min_value=min_val,
                max_value=max_val,
                value=(min_val, max_val),
                step=max((max_val - min_val) / 100, 1.0),
            )

# ── Exécution requête & affichage ────────────────────────────────────────────
query = build_query(regions, pays, secteurs, critere, annee, borne_min, borne_max)

@st.cache_data(show_spinner="⏳ Exécution de la requête…")
def run_query(sql):
    return con.execute(sql).df()

df = run_query(query)

st.markdown(f"### Résultats : {len(df):,} lignes")
st.dataframe(df.head(10000), use_container_width=True)
if len(df) > 10000:
    st.caption("⚠️ Affichage limité aux 10 000 premières lignes. Le téléchargement contient tout.")

# ── Export Excel ─────────────────────────────────────────────────────────────
@st.cache_data
def to_excel(dframe: pd.DataFrame) -> bytes:
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
        dframe.to_excel(writer, index=False, sheet_name="Données filtrées")
    buf.seek(0)
    return buf.getvalue()

xlsx = to_excel(df)
st.download_button(
    "📥 Exporter en XLSX",
    data=xlsx,
    file_name="filtrage_mna.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)
