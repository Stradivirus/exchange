import pandas as pd
from pymongo import MongoClient
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

def get_mongo():
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))
    mongo_uri = os.getenv('MONGODB_URI')
    mongo_db = os.getenv('MONGODB_DB', 'exchange_all')
    client = MongoClient(mongo_uri)
    db = client[mongo_db]
    return client, db

def get_pg_engine():
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))
    PG_HOST = os.getenv("PG_HOST")
    PG_DB = os.getenv("PG_DB")
    PG_USER = os.getenv("PG_USER")
    PG_PASSWORD = os.getenv("PG_PASSWORD")
    return create_engine(f"postgresql+psycopg2://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:5432/{PG_DB}")

stock_indices = ["SP500", "DOW_JONES", "NASDAQ", "KOSPI", "KOSDAQ"]

def upsert_stock():
    client, db = get_mongo()
    engine = get_pg_engine()
    data = {}
    volume_data = {}
    date = None
    for idx in stock_indices:
        doc = db[idx].find_one(sort=[("date", -1)])
        if doc:
            d = doc["date"].date() if hasattr(doc["date"], 'date') else doc["date"]
            data[idx.lower()] = doc.get("close")
            volume_data[f"{idx.lower()}_volume"] = doc.get("volume")
            if date is None or d > date:
                date = d
    if data and date:
        from sqlalchemy import text as sa_text
        ordered_cols = [
            "date",
            "sp500", "sp500_volume",
            "dow_jones", "dow_jones_volume",
            "nasdaq", "nasdaq_volume",
            "kospi", "kospi_volume",
            "kosdaq", "kosdaq_volume"
        ]
        row = {"date": date}
        for idx in stock_indices:
            row[idx.lower()] = data.get(idx.lower())
            row[f"{idx.lower()}_volume"] = volume_data.get(f"{idx.lower()}_volume")
        with engine.begin() as conn:
            result = conn.execute(sa_text("SELECT 1 FROM public.stock WHERE date = :date"), {"date": date}).fetchone()
            if not result:
                placeholders = ', '.join([f':{col}' for col in ordered_cols])
                columns = ', '.join(ordered_cols)
                sql = f'INSERT INTO public.stock ({columns}) VALUES ({placeholders})'
                conn.execute(sa_text(sql), {col: row.get(col) for col in ordered_cols})
                print(f"Inserted stock for {date}")
            else:
                print(f"stock already exists for {date}")
    client.close()

if __name__ == "__main__":
    upsert_stock()
