import pandas as pd
from pymongo import MongoClient
import os
from sqlalchemy import create_engine, text

def get_mongo():
    client = MongoClient("mongodb+srv://stradivirus:1q2w3e4r6218@cluster0.e7rvfpz.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
    db = client['exchange_all']
    return client, db

def get_pg_engine():
    PG_HOST = os.getenv("PG_HOST", "64.110.115.12")
    PG_DB = os.getenv("PG_DB", "exchange")
    PG_USER = os.getenv("PG_USER", "exchange_admin")
    PG_PASSWORD = os.getenv("PG_PASSWORD", "exchange_password")
    return create_engine(f"postgresql+psycopg2://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:5432/{PG_DB}")

stock_indices = ["SP500", "DOW_JONES", "NASDAQ", "KOSPI", "KOSDAQ"]

def upsert_stock():
    client, db = get_mongo()
    engine = get_pg_engine()
    data = {}
    date = None
    for idx in stock_indices:
        doc = db[idx].find_one(sort=[("date", -1)])
        if doc:
            d = doc["date"].date() if hasattr(doc["date"], 'date') else doc["date"]
            data[idx.lower()] = doc.get("close")
            if date is None or d > date:
                date = d
    if data and date:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1 FROM stock WHERE date = :date"), {"date": date}).fetchone()
            if not result:
                row = {"date": date}
                for idx in stock_indices:
                    row[idx.lower()] = data.get(idx.lower())
                pd.DataFrame([row]).to_sql("stock", engine, if_exists="append", index=False)
                print(f"Inserted stock for {date}")
            else:
                print(f"stock already exists for {date}")
    client.close()

if __name__ == "__main__":
    upsert_stock()
