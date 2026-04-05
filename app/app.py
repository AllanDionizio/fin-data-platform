import streamlit as st
import pandas as pd
from sqlalchemy import create_engine

# conexão com banco
engine = create_engine(
    "postgresql://admin:admin@localhost:5432/fintech_data"
)

# título
st.title("📊 Crypto Market Dashboard")

# carregar dados
query = """
SELECT *
FROM mart_top_crypto
ORDER BY rank
LIMIT 20
"""

df = pd.read_sql(query, engine)

st.write(df)
st.write("Rows:", len(df))

if df.empty:
    st.warning("No data available. Run the pipeline first.")

# mostrar tabela
st.subheader("Top 20 Cryptocurrencies by Market Cap")
st.dataframe(df)

# gráfico simples
st.subheader("Market Cap Ranking")

st.bar_chart(
    df.set_index("name")["market_cap"]
)

# métricas rápidas
st.subheader("Key Metrics")

col1, col2, col3 = st.columns(3)

col1.metric("Top Coin", df.iloc[0]["name"])
col2.metric("Top Market Cap", f"${df.iloc[0]['market_cap']:,}")
col3.metric("Top Price", f"${df.iloc[0]['current_price']:,}")