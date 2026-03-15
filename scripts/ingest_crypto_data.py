import requests
import pandas as pd
from datetime import datetime, UTC
from sqlalchemy import create_engine

url = "https://api.coingecko.com/api/v3/coins/markets"

params = {
    "vs_currency": "usd",
    "order": "market_cap_desc",
    "per_page": 10,
    "page": 1,
}

response = requests.get(url, params=params)

data = response.json()

df = pd.DataFrame(data)[[
    "id",
    "symbol",
    "name",
    "current_price",
    "market_cap",
    "total_volume"
]]

df["timestamp"] = datetime.now(UTC)

engine = create_engine(
    "postgresql://admin:admin@localhost:5432/fintech_data"
)

df.to_sql(
    "crypto_prices",
    engine,
    if_exists="append",
    index=False
)

print("Data inserted into database")