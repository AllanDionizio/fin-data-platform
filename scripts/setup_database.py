from sqlalchemy import create_engine, text

engine = create_engine(
    "postgresql://admin:admin@localhost:5432/fintech_data"
)

create_table_query = """
CREATE TABLE IF NOT EXISTS crypto_prices (
    id TEXT,
    symbol TEXT,
    name TEXT,
    current_price FLOAT,
    market_cap BIGINT,
    total_volume BIGINT,
    timestamp TIMESTAMP
)
"""

with engine.connect() as conn:
    conn.execute(text(create_table_query))
    conn.commit()

print("Table created successfully")