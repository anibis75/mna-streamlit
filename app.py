import streamlit as st
import duckdb
import pandas as pd
from io import BytesIO

# ───── Paramètres fixes ─────
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6ImF6YWQuaG9zc2VpbmlAc2tlbWEuZWR1Iiwic2Vzc2lvbiI6ImF6YWQuaG9zc2Vpbmkuc2tlbWEuZWR1IiwicGF0IjoiYkZMVHkydUUyMHFmNVhnMkE1TXh4M1FBZkhwclh0cTBRbnl2cHc4TjhLNCIsInVzZXJJZCI6IjllYTRjNDUzLTIyNWEtNGE5NS04Y2NmLWVhMjk1NTUyNmFjZCIsImlzcyI6Im1kX3BhdCIsInJlYWRPbmx5IjpmYWxzZSwidG9rZW5UeXBlIjoicmVhZF93cml0ZSIsImlhdCI6MTc1MzYwNjUyMn0.b8KgBs8dKKymTLu4hdQ-6ZHiwjJrec9JA7_9q764EzE"
DB    = "my_db"
TABLE = "main.zonebourse_chunk_compte_renamed"

con = duckdb.connect(f"md:{DB}?motherduck_token={TOKEN}")

# ───── Utilitaires ─────
def sql_list(values): return ",".join("'" + v.replace("'", "''") + "'" for v in values)

@st.cache_data
def get_distinct(col): 
    try:
        return [r[0] for r in con.execute(f'SELECT DISTINCT "{col}" FROM {TABLE} WHERE "{col}" IS NOT NULL').fetchall()]
    except Exception as e:
        st.warning(f"Erreur chargement {col} : {e}")
        return []

@st.cache_data
def get_years():
    return [
        col[1] for col in con.execute(f"PRAGMA table_info('{TABLE.split('.')[-1]}')").fetchall()
        if col[1].isdigit()
    ]

@st.cache_data(show_spinner="📥 Chargement données…")
def run_query(sql): return con.execute(sql).df()

@st.cache_data
def to_excel(df):
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as w:
        df.to_excel(w, index=False, sheet_name="Filtrage M&A")
    return buf.getvalue()

# ───── UI Streamlit ─────
st.title("🧪 Screening M&A (MotherDuck)")

with st.expander("🔍 Colonnes disponibles"):
    colonnes = con.execute(f"PRAGMA table_info('{TABLE.split('.')[-1]}')").df()["name"].tolist()
    st.write(colonnes)

poste = st.selectbox("📌 Choix du poste financier", get_distinct("Poste"))

if poste:
    annee = st.selectbox("📅 Choix de l’année", sorted(get_years()))
    
    if annee:
        try:
            min_val, max_val = con.execute(
                f'''SELECT min(CAST("{annee}" AS DOUBLE)), max(CAST("{annee}" AS DOUBLE)) 
                    FROM {TABLE} WHERE "Poste" = '{poste.replace("'", "''")}' '''
            ).fetchone()

            if min_val is not None and max_val is not None and min_val != max_val:
                borne_min, borne_max = st.slider(
                    "🎯 Filtrer la valeur",
                    min_value=float(min_val),
                    max_value=float(max_val),
                    value=(float(min_val), float(max_val)),
                    step=max((float(max_val)-float(min_val))/100, 1.0)
                )
            else:
                borne_min = borne_max = None

        except Exception as e:
            st.error(f"Erreur min/max : {e}")
            borne_min = borne_max = None

    if annee and borne_min is not None:
        region  = st.multiselect("🌍 Région(s)", get_distinct("Région"))
        pays    = st.multiselect("🏳️ Pays", get_distinct("Pays"))
        secteur = st.multiselect("🏭 Secteur(s)", get_distinct("Secteur"))

        # ───── Construction requête ─────
        clauses = [f'"Poste" = \'{poste.replace("'", "''")}\'',
                   f'CAST("{annee}" AS DOUBLE) BETWEEN {borne_min} AND {borne_max}']
        if region:  clauses.append(f'"Région" IN ({sql_list(region)})')
        if pays:    clauses.append(f'"Pays"   IN ({sql_list(pays)})')
        if secteur: clauses.append(f'"Secteur" IN ({sql_list(secteur)})')

        sql = f"SELECT * FROM {TABLE} WHERE " + " AND ".join(clauses)
        df = run_query(sql)

        st.success(f"✅ {len(df):,} lignes trouvées")
        st.dataframe(df.head(10_000), use_container_width=True)

        if len(df) > 10_000:
            st.caption("⚠️ Limité à 10 000 lignes visibles. Export complet dispo ci-dessous.")

        st.download_button(
            "⬇️ Export XLSX",
            data=to_excel(df),
            file_name="filtrage_mna.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
