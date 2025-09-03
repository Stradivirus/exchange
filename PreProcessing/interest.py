import pandas as pd
from pymongo import MongoClient
import os
from sqlalchemy import create_engine

# MongoDB 연결
client = MongoClient("mongodb+srv://stradivirus:1q2w3e4r6218@cluster0.e7rvfpz.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client['exchange_all']

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
    # 하나라도 값이 있는 날짜만 남기고, 2000-01-01 이후만 남김 (파티션 범위와 일치)
    import datetime
    pivot_df = pivot_df.dropna(how="all")
    pivot_df = pivot_df[pivot_df.index >= datetime.date(2000, 1, 1)]
    print("\n=== 금리 피벗 데이터프레임 샘플 ===")
    print(pivot_df.tail())

    # CSV 저장
    csv_path = "interest_rate.csv"
    pivot_df.to_csv(csv_path, encoding="utf-8-sig")
    print(f"CSV로 저장 완료: {csv_path}")

    # PostgreSQL 저장
    PG_HOST = os.getenv("PG_HOST", "64.110.115.12")
    PG_DB = os.getenv("PG_DB", "exchange")
    PG_USER = os.getenv("PG_USER", "exchange_admin")
    PG_PASSWORD = os.getenv("PG_PASSWORD", "exchange_password")
    engine = create_engine(f"postgresql+psycopg2://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:5432/{PG_DB}")
    pivot_df_reset = pivot_df.reset_index()
    pivot_df_reset.to_sql("interest_rate", engine, if_exists="append", index=False)
    print("\nPostgreSQL(interest_rate) 테이블에 저장 완료!")

if __name__ == "__main__":
    make_and_save_interest_rate()
    client.close()