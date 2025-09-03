import pandas as pd
from pymongo import MongoClient
import os
from sqlalchemy import create_engine, text

# MongoDB 연결
def get_mongo():
    client = MongoClient("mongodb+srv://stradivirus:1q2w3e4r6218@cluster0.e7rvfpz.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
    db = client['exchange_all']
    return client, db

# PostgreSQL 연결
def get_pg_engine():
    PG_HOST = os.getenv("PG_HOST", "64.110.115.12")
    PG_DB = os.getenv("PG_DB", "exchange")
    PG_USER = os.getenv("PG_USER", "exchange_admin")
    PG_PASSWORD = os.getenv("PG_PASSWORD", "exchange_password")
    return create_engine(f"postgresql+psycopg2://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:5432/{PG_DB}")

spot_cols = ["gold", "silver", "copper", "crude_oil", "brent_oil"]
index_cols = ["dxy", "usd_index", "vix"]
collection_map = {
    "gold": "GOLD",
    "silver": "SILVER",
    "copper": "COPPER",
    "crude_oil": "CRUDE_OIL",
    "brent_oil": "BRENT_OIL",
    "dxy": "DXY",
    "usd_index": "USD_INDEX",
    "vix": "VIX"
}

def upsert_commodities():
    client, db = get_mongo()
    engine = get_pg_engine()
    # 현물(commodities)
    spot_data = {}
    for col in spot_cols:
        doc = db[collection_map[col]].find_one(sort=[("date", -1)])
        if doc:
            date = doc["date"].date() if hasattr(doc["date"], 'date') else doc["date"]
            spot_data[col] = doc.get("close")
    if spot_data:
        date = doc["date"].date() if hasattr(doc["date"], 'date') else doc["date"]
        # 이미 해당 날짜 데이터가 있는지 확인
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1 FROM commodities WHERE date = :date"), {"date": date}).fetchone()
            if not result:
                row = {"date": date}
                row.update(spot_data)
                pd.DataFrame([row]).to_sql("commodities", engine, if_exists="append", index=False)
                print(f"Inserted commodities for {date}")
            else:
                print(f"commodities already exists for {date}")
    # 인덱스(commodities_index)
    index_data = {}
    for col in index_cols:
        doc = db[collection_map[col]].find_one(sort=[("date", -1)])
        if doc:
            date = doc["date"].date() if hasattr(doc["date"], 'date') else doc["date"]
            index_data[col] = doc.get("close")
    if index_data:
        date = doc["date"].date() if hasattr(doc["date"], 'date') else doc["date"]
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1 FROM commodities_index WHERE date = :date"), {"date": date}).fetchone()
            if not result:
                row = {"date": date}
                row.update(index_data)
                pd.DataFrame([row]).to_sql("commodities_index", engine, if_exists="append", index=False)
                print(f"Inserted commodities_index for {date}")
            else:
                print(f"commodities_index already exists for {date}")
    client.close()

if __name__ == "__main__":
    upsert_commodities()
