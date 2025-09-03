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
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1 FROM exchange WHERE date = :date"), {"date": date}).fetchone()
            if not result:
                row = {"date": date}
                for c in currencies:
                    row[c.lower()] = data.get(c.lower())
                pd.DataFrame([row]).to_sql("exchange", engine, if_exists="append", index=False)
                print(f"Inserted exchange for {date}")
            else:
                print(f"exchange already exists for {date}")
    client.close()

if __name__ == "__main__":
    upsert_exchange()
