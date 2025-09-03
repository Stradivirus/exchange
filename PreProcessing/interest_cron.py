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

def upsert_interest():
    import datetime
    client, db = get_mongo()
    engine = get_pg_engine()
    today = datetime.date.today()
    start_date = today - datetime.timedelta(days=180)
    # 최근 6개월치 데이터 모두 조회
    kor_cursor = db["KOR_BASE_RATE"].find({"date": {"$gte": start_date}}, {"date": 1, "rate": 1, "_id": 0})
    us_cursor = db["US_FED_RATE"].find({"date": {"$gte": start_date}}, {"date": 1, "rate": 1, "_id": 0})
    kor_dict = {doc["date"].date() if hasattr(doc["date"], 'date') else doc["date"]: doc.get("rate") for doc in kor_cursor}
    us_dict = {doc["date"].date() if hasattr(doc["date"], 'date') else doc["date"]: doc.get("rate") for doc in us_cursor}
    # 날짜 합집합
    all_dates = set(kor_dict.keys()) | set(us_dict.keys())
    if not all_dates:
        print("최근 6개월 내 금리 데이터가 없습니다.")
        client.close()
        return
    rows = []
    for date in sorted(all_dates):
        row = {"date": date, "kor_base_rate": kor_dict.get(date), "us_fed_rate": us_dict.get(date)}
        rows.append(row)
    with engine.connect() as conn:
        for row in rows:
            result = conn.execute(text("SELECT 1 FROM interest_rate WHERE date = :date"), {"date": row["date"]}).fetchone()
            if not result:
                pd.DataFrame([row]).to_sql("interest_rate", engine, if_exists="append", index=False)
                print(f"Inserted interest_rate for {row['date']}")
            else:
                print(f"interest_rate already exists for {row['date']}")
    client.close()

if __name__ == "__main__":
    upsert_interest()
