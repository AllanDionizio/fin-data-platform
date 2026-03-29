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
"""

with engine.connect() as conn:
    conn.execute(text(transform_query))
    conn.commit()

print("Data transformed to staging")