import streamlit as st
import duckdb
import pandas as pd

# ─────────── Paramètres MotherDuck ───────────
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."  # ← garde ton vrai token ici
DB    = "my_db"
TABLE = "main.zonebourse_chunk_compte_renamed"

# ─────────── Connexion ───────────
con = duckdb.connect(f"md:{DB}?motherduck_token={TOKEN}")

# ─────────── Requête simple ───────────
try:
    df = con.execute(f"SELECT * FROM {TABLE} LIMIT 1000").df()
    st.success(f"✅ {len(df):,} lignes chargées")
    st.dataframe(df, use_container_width=True)
except Exception as e:
    st.error(f"❌ Erreur : {e}")
