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

currencies = ["USD", "JPY", "EUR", "CNY"]

def upsert_exchange():
    client, db = get_mongo()
    engine = get_pg_engine()
    # 각 통화별 최신 데이터 수집
    data = {}
    date = None
    for currency in currencies:
        doc = db[currency].find_one(sort=[("date", -1)])
        if doc:
            d = doc["date"].date() if hasattr(doc["date"], 'date') else doc["date"]
            data[currency.lower()] = doc.get("rate")
            if date is None or d > date:
                date = d
    if data and date:
        from sqlalchemy import text as sa_text
        expected_cols = ["date", "usd", "jpy", "eur", "cny"]
        row = {"date": date}
        for c in currencies:
            row[c.lower()] = data.get(c.lower())
        with engine.begin() as conn:
            result = conn.execute(sa_text("SELECT 1 FROM public.exchange WHERE date = :date"), {"date": date}).fetchone()
            if not result:
                placeholders = ', '.join([f':{col}' for col in expected_cols])
                columns = ', '.join(expected_cols)
                sql = f'INSERT INTO public.exchange ({columns}) VALUES ({placeholders})'
                conn.execute(sa_text(sql), {col: row.get(col) for col in expected_cols})
                print(f"Inserted exchange for {date}")
            else:
                print(f"exchange already exists for {date}")
    client.close()

if __name__ == "__main__":
    upsert_exchange()
