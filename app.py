import duckdb
import streamlit as st

st.title("Test MotherDuck")

# Remplace ici par ton token
TOKEN = "TON_TOKEN"
DB = "my_db"
TABLE = "main.zonebourse_chunk_compte_renamed"

try:
    con = duckdb.connect(f"md:{DB}?motherduck_token={TOKEN}")
    st.success("✅ Connexion OK")

    # Requête test
    df = con.execute(f"SELECT * FROM {TABLE} LIMIT 5").df()
    st.write("✅ Données :", df)

except Exception as e:
    st.error(f"❌ Erreur : {e}")
