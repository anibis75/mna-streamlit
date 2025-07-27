# app.py  – version corrigée (plus de IndexingError)

import os
from io import BytesIO

import duckdb
import pandas as pd
import streamlit as st

# ────────────────────── MotherDuck ──────────────────────
DB     = os.getenv("MD_DB", "my_db")
TOKEN  = os.getenv("MOTHERDUCK_TOKEN")
TABLE  = "main.zonebourse_chunk_compte"

con = duckdb.connect(f"md:{DB}?motherduck_token={TOKEN}")

# ─────────────────── Fonctions utilitaires ──────────────
def sql_list(seq):
    return ",".join("'" + str(s).replace("'", "''") + "'" for s in seq)

@st.cache_data
def distinct(col: str):
    return [
        r[0]
        for r in con.execute(
            f'SELECT DISTINCT "{col}" FROM {TABLE} '
            f'WHERE "{col}" IS NOT NULL ORDER BY 1'
        ).fetchall()
    ]

@st.cache_data
def year_columns():
    return [
        col[0]
        for col in con.execute(
            f"PRAGMA table_info('{TABLE.split('.')[-1]}')"
        ).fetchall()
        if col[1].isdigit()
    ]

@st.cache_data(show_spinner="⏳ Exécution SQL …")
def run_query(sql: str) -> pd.DataFrame:
    return con.execute(sql).df()

@st.cache_data
def to_excel(df: pd.DataFrame) -> bytes:
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as w:
        df.to_excel(w, index=False, sheet_name="Données filtrées")
    buf.seek(0)
    return buf.getvalue()

# ───────────────────── Interface ────────────────────────
st.title("📊 Screening M&A (MotherDuck)")

regions  = st.multiselect("🌍 Région(s)",  distinct("Région"))
pays     = st.multiselect("🏳️ Pays",       distinct("Pays"))
secteurs = st.multiselect("🏭 Secteur(s)", distinct("Secteur"))
poste    = st.selectbox("📌 Poste financier", distinct("Poste"))

annee = borne_min = borne_max = None
if poste:
    annee = st.selectbox("📅 Année", sorted(year_columns()))
    if annee:
        min_val, max_val = con.execute(
            f'''SELECT min(CAST("{annee}" AS DOUBLE)),
                       max(CAST("{annee}" AS DOUBLE))
                FROM {TABLE}
                WHERE "Poste" = '{poste.replace("'", "''")}' '''
        ).fetchone()
        if min_val is not None and max_val is not None and min_val != max_val:
            min_val, max_val = float(min_val), float(max_val)
            borne_min, borne_max = st.slider(
                "Plage de valeurs",
                min_value=min_val,
                max_value=max_val,
                value=(min_val, max_val),
                step=max((max_val - min_val) / 200, 1.0),
            )

# ─────────────────── Construction requête ───────────────
clauses = []
if regions:  clauses.append(f'"Région"  IN ({sql_list(regions)})')
if pays:     clauses.append(f'"Pays"    IN ({sql_list(pays)})')
if secteurs: clauses.append(f'"Secteur" IN ({sql_list(secteurs)})')
if poste:    clauses.append(f'"Poste" = \'{poste.replace("\'","\'\'")}\'')

if poste and annee and borne_min is not None:
    clauses.append(f'CAST("{annee}" AS DOUBLE) BETWEEN {borne_min} AND {borne_max}')

where_sql = " AND ".join(clauses) or "TRUE"
query_sql = f"SELECT * FROM {TABLE} WHERE {where_sql}"

df = run_query(query_sql)

# ───────────────────── Affichage ────────────────────────
st.markdown(f"### Résultats : {len(df):,} lignes")
st.dataframe(df.head(10_000), use_container_width=True)
if len(df) > 10_000:
    st.caption("Affichage limité aux 10 000 premières lignes ; l’export contient tout.")

st.download_button(
    "📥 Exporter en XLSX",
    data=to_excel(df),
    file_name="filtrage_mna.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)
