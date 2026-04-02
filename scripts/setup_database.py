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
    conn.commit()