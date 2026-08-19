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
"""