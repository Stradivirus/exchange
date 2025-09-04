import pandas as pd
from pymongo import MongoClient
import os
from sqlalchemy import create_engine

# 환경변수 로드
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))
mongo_uri = os.getenv('MONGODB_URI')
mongo_db = os.getenv('MONGODB_DB', 'exchange_all')
client = MongoClient(mongo_uri)
db = client[mongo_db]

def make_and_save_interest_rate():
    """MongoDB에서 금리 데이터를 읽어와 피벗, 반올림, CSV/DB 저장 (하나라도 값이 있는 날짜만)"""
    all_data = []
    # 한국 기준금리
    for doc in db["KOR_BASE_RATE"].find({}, {"date": 1, "rate": 1, "_id": 0}):
        all_data.append({
            "date": doc["date"].date() if hasattr(doc["date"], 'date') else doc["date"],
            "item": "kor_base_rate",
            "rate": doc.get("rate")
        })
    # 미국 연방기금금리
    for doc in db["US_FED_RATE"].find({}, {"date": 1, "rate": 1, "_id": 0}):
        all_data.append({
            "date": doc["date"].date() if hasattr(doc["date"], 'date') else doc["date"],
            "item": "us_fed_rate",
            "rate": doc.get("rate")
        })
    df = pd.DataFrame(all_data)
    if df.empty:
        print("MongoDB에서 불러온 데이터가 없습니다.")
        return

    ordered_cols = ["kor_base_rate", "us_fed_rate"]
    pivot_df = df.pivot_table(index="date", columns="item", values="rate")
    pivot_df = pivot_df.reindex(columns=ordered_cols)
    pivot_df = pivot_df.sort_index().round(4)
    # 하나라도 값이 있는 날짜만 남기고, 2010-01-01 이후만 남김 (파티션 범위와 일치)
    import datetime
    pivot_df = pivot_df.dropna(how="all")
    pivot_df = pivot_df[pivot_df.index >= datetime.date(2010, 1, 1)]
    print("\n=== 금리 피벗 데이터프레임 샘플 ===")
    print(pivot_df.tail())

    # PostgreSQL 저장 (insert 방식, 중복 날짜는 insert하지 않음)
    from sqlalchemy import text
    PG_HOST = os.getenv("PG_HOST")
    PG_DB = os.getenv("PG_DB")
    PG_USER = os.getenv("PG_USER")
    PG_PASSWORD = os.getenv("PG_PASSWORD")
    engine = create_engine(f"postgresql+psycopg2://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:5432/{PG_DB}")
    df_reset = pivot_df.reset_index()
    with engine.connect() as conn:
        for _, row in df_reset.iterrows():
            date = row['date']
            kor_base_rate = row['kor_base_rate'] if not pd.isna(row['kor_base_rate']) else None
            us_fed_rate = row['us_fed_rate'] if not pd.isna(row['us_fed_rate']) else None
            exists = conn.execute(text("SELECT 1 FROM interest_rate WHERE date = :date"), {"date": date}).fetchone()
            if not exists:
                conn.execute(
                    text("INSERT INTO interest_rate (date, kor_base_rate, us_fed_rate) VALUES (:date, :kor, :us)"),
                    {"date": date, "kor": kor_base_rate, "us": us_fed_rate}
                )
                print(f"Inserted interest_rate for {date}")
            else:
                print(f"interest_rate already exists for {date}")
    print("\nPostgreSQL(interest_rate) 테이블에 insert 방식으로 저장 완료!")

if __name__ == "__main__":
    make_and_save_interest_rate()
    client.close()