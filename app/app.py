import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from streamlit_autorefresh import st_autorefresh

st.set_page_config(
    page_title="Crypto Market Dashboard",
    layout="wide"
)

st_autorefresh(interval=60 * 1000, key="refresh")

engine = create_engine(
    "postgresql://admin:admin@localhost:5432/fintech_data"
)

query = """
WITH ranked AS (
    SELECT
        id,
        symbol,
        name,
        current_price,
        market_cap,
        total_volume,
        timestamp,

        LAG(current_price) OVER (
            PARTITION BY id
            ORDER BY timestamp
        ) as prev_price

    FROM staging_crypto_prices
),
latest AS (
    SELECT DISTINCT ON (id)
        *
    FROM ranked
    ORDER BY id, timestamp DESC
)
SELECT
    *,
    timestamp as updated_at,

    RANK() OVER (ORDER BY market_cap DESC) as rank,

    current_price - prev_price AS price_change,

    ((current_price - prev_price) / prev_price) * 100 AS price_change_pct

FROM latest
ORDER BY rank
"""

history_query = """
SELECT
    id,
    name,
    current_price,
    market_cap,
    timestamp
FROM staging_crypto_prices
WHERE name = %(coin)s
ORDER BY timestamp
"""

df = pd.read_sql(query, engine)

st.title("📊 Crypto Market Dashboard")

if df.empty:
    st.warning("No data available. Run pipeline first.")
    st.stop()

df["price_change_pct"] = df["price_change_pct"].fillna(0)

df["change_fmt"] = df["price_change_pct"].apply(
    lambda x: f"{x:.2f}%"
)

df["change_color"] = df["price_change_pct"].apply(
    lambda x: "🟢" if x >= 0 else "🔴"
)

# -------------------------
# last update
# -------------------------

last_update = df["updated_at"].max()

col1, col2 = st.columns([3,1])

col1.markdown(f"Last update: **{last_update}**")

if col2.button("Refresh"):
    st.rerun()

st.divider()

# -------------------------
# Sidebar
# -------------------------

st.sidebar.header("Filters")

coin = st.sidebar.selectbox(
    "Coin",
    ["All"] + list(df["name"].unique())
)

if coin != "All":

    history_df = pd.read_sql(
        history_query,
        engine,
        params={"coin": coin}
    )
    history_df["timestamp"] = pd.to_datetime(history_df["timestamp"])
    history_df = history_df.sort_values("timestamp")

# -------------------------
# format values
# -------------------------

df["market_cap_fmt"] = df["market_cap"].apply(lambda x: f"${x:,.0f}")
df["price_fmt"] = df["current_price"].apply(lambda x: f"${x:,.2f}")
df["volume_fmt"] = df["total_volume"].apply(lambda x: f"${x:,.0f}")
df["display_change"] = df["price_change_pct"].apply(lambda x: f"🟢 {x:.2f}%" if x >= 0 else f"🔴 {x:.2f}%")

# -------------------------
# Top Gainers
# -------------------------

st.subheader("🚀 Top Gainers")

gainers = df.sort_values("price_change_pct", ascending=False).head(3)

c1, c2, c3 = st.columns(3)

for i, (_, row) in enumerate(gainers.iterrows()):
    [c1, c2, c3][i].metric(
        row["name"],
        f"${row['current_price']:,.2f}",
        f"{row['price_change_pct']:.2f}%"
    )

# -------------------------
# Top Losers
# -------------------------
st.subheader("📉 Top Losers")

losers = df.sort_values("price_change_pct").head(3)

c1, c2, c3 = st.columns(3)

for i, (_, row) in enumerate(losers.iterrows()):
    [c1, c2, c3][i].metric(
        row["name"],
        f"${row['current_price']:,.2f}",
        f"{row['price_change_pct']:.2f}%"
    )

# -------------------------
# Top 3 highlight
# -------------------------

st.subheader("🏆 Top 3 Cryptocurrencies")

top3 = df.sort_values("rank").head(3)

c1, c2, c3 = st.columns(3)

cards = [c1, c2, c3]

for i, (_, row) in enumerate(top3.iterrows()):
    cards[i].metric(
        f"#{int(row['rank'])} {row['name']}",
        row["price_fmt"],
        f"Market Cap {row['market_cap_fmt']}"
    )

st.divider()

# -------------------------
# Price History per coin
# -------------------------

if coin != "All":

    st.divider()
    st.subheader(f"📈 {coin} Price History")

    history_df = history_df.sort_values("timestamp")

    st.line_chart(
        history_df.set_index("timestamp")["current_price"]
    )

# -------------------------
# Market Cap per coin
# -------------------------

if coin != "All":

    st.subheader(f"🏦 {coin} Market Cap History")

    st.line_chart(
        history_df.set_index("timestamp")["market_cap"]
    )

# -------------------------
# global metrics
# -------------------------

st.subheader("Market Overview")

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Total Market Cap",
    f"${df['market_cap'].sum():,.0f}"
)

col2.metric(
    "Average Price",
    f"${df['current_price'].mean():,.2f}"
)

col3.metric(
    "Highest Volume",
    df.sort_values("total_volume", ascending=False).iloc[0]["name"]
)

col4.metric(
    "Tracked Coins",
    len(df)
)

st.divider()

# -------------------------
# ranking table
# -------------------------

st.subheader("Full Ranking")

display_df = df[[
    "rank",
    "name",
    "price_fmt",
    "display_change",
    "market_cap_fmt",
    "volume_fmt"
]].rename(columns={
    "rank": "Rank",
    "name": "Coin",
    "price_fmt": "Price",
    "display_change": "Change %",
    "market_cap_fmt": "Market Cap",
    "volume_fmt": "Volume"
})

st.dataframe(display_df, use_container_width=True)

# -------------------------
# charts
# -------------------------

col1, col2 = st.columns(2)

with col1:
    st.subheader("Market Cap")

    chart_df = df.sort_values("market_cap", ascending=False)

    st.bar_chart(
        chart_df.set_index("name")["market_cap"]
    )

with col2:
    st.subheader("Volume")

    st.bar_chart(
        chart_df.set_index("name")["total_volume"]
    )