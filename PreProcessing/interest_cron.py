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

def upsert_interest():
    import datetime
    client, db = get_mongo()
    engine = get_pg_engine()
    today = datetime.date.today()
    # 최근 1년(365일) 데이터만 insert
    start_date = today - datetime.timedelta(days=365)
    kor_cursor = db["KOR_BASE_RATE"].find({"date": {"$gte": start_date}}, {"date": 1, "rate": 1, "_id": 0})
    us_cursor = db["US_FED_RATE"].find({"date": {"$gte": start_date}}, {"date": 1, "rate": 1, "_id": 0})
    kor_dict = {doc["date"].date() if hasattr(doc["date"], 'date') else doc["date"]: doc.get("rate") for doc in kor_cursor}
    us_dict = {doc["date"].date() if hasattr(doc["date"], 'date') else doc["date"]: doc.get("rate") for doc in us_cursor}
    all_dates = set(kor_dict.keys()) | set(us_dict.keys())
    if not all_dates:
        print("2010년 이후 금리 데이터가 없습니다.")
        client.close()
        return
    rows = []
    for date in sorted(all_dates):
        row = {"date": date, "kor_base_rate": kor_dict.get(date), "us_fed_rate": us_dict.get(date)}
        rows.append(row)
    with engine.connect() as conn:
        for row in rows:
            date = row['date']
            kor_base_rate = row['kor_base_rate'] if row['kor_base_rate'] is not None else None
            us_fed_rate = row['us_fed_rate'] if row['us_fed_rate'] is not None else None
            exists = conn.execute(text("SELECT 1 FROM interest_rate WHERE date = :date"), {"date": date}).fetchone()
            if not exists:
                conn.execute(
                    text("INSERT INTO interest_rate (date, kor_base_rate, us_fed_rate) VALUES (:date, :kor, :us)"),
                    {"date": date, "kor": kor_base_rate, "us": us_fed_rate}
                )
                print(f"Inserted interest_rate for {date}")
            else:
                print(f"interest_rate already exists for {date}")
    client.close()

if __name__ == "__main__":
    upsert_interest()
