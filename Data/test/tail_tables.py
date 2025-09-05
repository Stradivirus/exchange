import pandas as pd
from sqlalchemy import create_engine
import os

PG_HOST = os.getenv("PG_HOST", "64.110.115.12")
PG_DB = os.getenv("PG_DB", "exchange")
PG_USER = os.getenv("PG_USER", "exchange_admin")
PG_PASSWORD = os.getenv("PG_PASSWORD", "exchange_password")
engine = create_engine(f"postgresql+psycopg2://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:5432/{PG_DB}")

# 파티션 테이블 제외, 일반 테이블만 tail
main_tables = [
    'commodities',
    'commodities_index',
    'grains',
    'exchange',
    'interest_rate',
    'stock'
]
for table in main_tables:
    try:
        df = pd.read_sql(f"SELECT * FROM {table} ORDER BY date DESC LIMIT 5", engine)
        print(f"\n[{table}] tail:")
        print(df[::-1].to_string(index=False))
    except Exception as e:
        print(f"{table} 에러: {e}")
