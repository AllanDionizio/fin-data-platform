import requests
import pandas as pd
from datetime import datetime
import os

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

df["timestamp"] = datetime.utcnow()

os.makedirs("../data", exist_ok=True)

file_name = f"../data/crypto_data_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"

df.to_csv(file_name, index=False)

print("Data saved:", file_name)