from sqlalchemy import create_engine, text

engine = create_engine(
    "postgresql://admin:admin@localhost:5432/fintech_data"
)

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
FROM staging_crypto_prices
"""

with engine.connect() as conn:
    conn.execute(text(mart_query))
    conn.commit()

print("MART table updated")