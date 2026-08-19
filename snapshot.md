]633;E;echo "## Estrutura";e26a133e-fa55-4490-85c6-01559832701c]633;C## Estrutura
.gitignore
README.md
app/app.py
data/crypto_data_20260307_234045.csv
docker-compose.yml
requirements.txt
scripts/build_mart_top_crypto.py
scripts/ingest_crypto_data.py
scripts/setup_database.py
scripts/transform_raw_to_staging.py
snapshot.md

## Conteúdo dos arquivos

### README.md
```
```

### app/app.py
```
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
    )```

### docker-compose.yml
```
#version: "3"

services:

  postgres:
    image: postgres:15
    container_name: fintech_postgres

    environment:
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: admin
      POSTGRES_DB: fintech_data

    ports:
      - "5432:5432"

    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:```

### requirements.txt
```
altair==6.0.0
attrs==26.1.0
blinker==1.9.0
cachetools==7.0.5
certifi==2026.2.25
charset-normalizer==3.4.5
click==8.3.1
gitdb==4.0.12
GitPython==3.1.46
greenlet==3.3.2
idna==3.11
Jinja2==3.1.6
jsonschema==4.26.0
jsonschema-specifications==2025.9.1
MarkupSafe==3.0.3
narwhals==2.18.1
numpy==2.4.2
packaging==26.0
pandas==3.0.1
pillow==12.2.0
protobuf==7.34.1
psycopg2-binary==2.9.11
pyarrow==23.0.1
pydeck==0.9.1
python-dateutil==2.9.0.post0
referencing==0.37.0
requests==2.32.5
rpds-py==0.30.0
six==1.17.0
smmap==5.0.3
SQLAlchemy==2.0.48
streamlit==1.56.0
streamlit-autorefresh==1.0.1
tenacity==9.1.4
toml==0.10.2
tornado==6.5.5
typing_extensions==4.15.0
urllib3==2.6.3
watchdog==6.0.0
```

### scripts/build_mart_top_crypto.py
```
from sqlalchemy import create_engine, text

engine = create_engine(
    "postgresql://admin:admin@localhost:5432/fintech_data"
)

truncate_query = "TRUNCATE TABLE mart_top_crypto"

mart_query = """
INSERT INTO mart_top_crypto
SELECT
    id,
    symbol,
    name,
    current_price,
    market_cap,
    total_volume,
    RANK() OVER (ORDER BY market_cap DESC) as rank,
    NOW() as updated_at
FROM (
    SELECT DISTINCT ON (id)
        id,
        symbol,
        name,
        current_price,
        market_cap,
        total_volume,
        timestamp
    FROM staging_crypto_prices
    ORDER BY id, timestamp DESC
) sub
"""

with engine.begin() as conn:
    conn.execute(text(truncate_query))
    conn.execute(text(mart_query))
    #conn.commit()

print("MART table updated")```

### scripts/ingest_crypto_data.py
```
import requests
from sqlalchemy import create_engine, text
from datetime import datetime, UTC
import json

url = "https://api.coingecko.com/api/v3/coins/markets"

params = {
    "vs_currency": "usd",
    "order": "market_cap_desc",
    "per_page": 10,
    "page": 1,
}

response = requests.get(url, params=params)
data = response.json()

engine = create_engine(
    "postgresql://admin:admin@localhost:5432/fintech_data"
)

insert_query = """
INSERT INTO raw_crypto_prices (data, ingestion_timestamp)
VALUES (:data, :timestamp)
"""

with engine.connect() as conn:
    for record in data:
        conn.execute(
            text(insert_query),
            {
                "data": json.dumps(record),
                "timestamp": datetime.now(UTC)
            }
        )
    conn.commit()

print("Raw data inserted")

create_staging_table = """
CREATE TABLE IF NOT EXISTS staging_crypto_prices (
    id TEXT,
    symbol TEXT,
    name TEXT,
    current_price FLOAT,
    market_cap BIGINT,
    total_volume BIGINT,
    timestamp TIMESTAMP
)
"""```

### scripts/setup_database.py
```
from sqlalchemy import create_engine, text

engine = create_engine(
    "postgresql://admin:admin@localhost:5432/fintech_data"
)

create_raw_table = """
CREATE TABLE IF NOT EXISTS raw_crypto_prices (
    data JSONB,
    ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

create_staging_table = """
CREATE TABLE IF NOT EXISTS staging_crypto_prices (
    id TEXT,
    symbol TEXT,
    name TEXT,
    current_price FLOAT,
    market_cap BIGINT,
    total_volume BIGINT,
    timestamp TIMESTAMP,
    UNIQUE (id,timestamp)
)
"""

print("RAW table created")

create_mart_table = """
CREATE TABLE IF NOT EXISTS mart_top_crypto (
    id TEXT,
    symbol TEXT,
    name TEXT,
    current_price FLOAT,
    market_cap BIGINT,
    total_volume BIGINT,
    rank INT,
    updated_at TIMESTAMP,
    UNIQUE (id, updated_at)
)
"""

print("Top Crypto table created")

with engine.connect() as conn:
    conn.execute(text(create_raw_table))
    conn.execute(text(create_staging_table))
    conn.execute(text(create_mart_table))
    conn.commit()```

### scripts/transform_raw_to_staging.py
```
from sqlalchemy import create_engine, text

engine = create_engine(
    "postgresql://admin:admin@localhost:5432/fintech_data"
)

transform_query = """
INSERT INTO staging_crypto_prices
SELECT
    data->>'id' AS id,
    data->>'symbol' AS symbol,
    data->>'name' AS name,
    (data->>'current_price')::float,
    (data->>'market_cap')::bigint,
    (data->>'total_volume')::bigint,
    ingestion_timestamp
FROM raw_crypto_prices
ON CONFLICT (id,timestamp) DO NOTHING
"""

with engine.connect() as conn:
    conn.execute(text(transform_query))
    conn.commit()

print("Data transformed to staging")```

### snapshot.md
```
```
