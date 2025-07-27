import streamlit as st
import duckdb

# Config MotherDuck
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6ImF6YWQuaG9zc2VpbmlAc2tlbWEuZWR1Iiwic2Vzc2lvbiI6ImF6YWQuaG9zc2Vpbmkuc2tlbWEuZWR1IiwicGF0IjoiYkZMVHkydUUyMHFmNVhnMkE1TXh4M1FBZkhwclh0cTBRbnl2cHc4TjhLNCIsInVzZXJJZCI6IjllYTRjNDUzLTIyNWEtNGE5NS04Y2NmLWVhMjk1NTUyNmFjZCIsImlzcyI6Im1kX3BhdCIsInJlYWRPbmx5IjpmYWxzZSwidG9rZW5UeXBlIjoicmVhZF93cml0ZSIsImlhdCI6MTc1MzYwNjUyMn0.b8KgBs8dKKymTLu4hdQ-6ZHiwjJrec9JA7_9q764EzE"
DB = "my_db"
TABLE = "main.zonebourse_chunk_compte_renamed"

# Connexion
con = duckdb.connect(f"md:{DB}?motherduck_token={TOKEN}")

# Requête simple
try:
    df = con.execute(f"SELECT * FROM {TABLE} LIMIT 10").fetchdf()
    st.title("✅ Test Lecture DuckDB")
    st.dataframe(df)
except Exception as e:
    st.error(f"❌ Erreur : {e}")
