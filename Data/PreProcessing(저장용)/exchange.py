import os
from pymongo import MongoClient
from datetime import datetime

# 환경변수 로드
mongo_uri = "mongodb+srv://stradivirus:1q2w3e4r6218@cluster0.e7rvfpz.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
mongo_db = "exchange_all"
client = MongoClient(mongo_uri)
db = client[mongo_db]

# 통화 코드와 이름 매핑
currencies = {
    "0000001": "USD",  # 달러
    "0000002": "JPY",  # 엔 (100엔당)
    "0000053": "CNY",  # 위안
    "0000003": "EUR"    # 유로
}

import pandas as pd
import os
from sqlalchemy import create_engine

def print_exchange_samples():
    print("\n=== MongoDB 환율 데이터 샘플 출력 (각 통화별 5개) ===")
    for currency_name in currencies.values():
        collection = db[currency_name]
        docs = collection.find().sort("date", 1).limit(5)
        print(f"\n[{currency_name}] 예시 데이터:")
        for doc in docs:
            date_str = doc["date"].strftime('%Y-%m-%d') if hasattr(doc["date"], 'strftime') else str(doc["date"])
            print(f"  날짜: {date_str}, 코드: {doc['currency_code']}, 환율: {doc['rate']}, 단위: {doc.get('unit_name', '')}")

def make_pivot_and_save_csv_and_postgres():
    """모든 환율 데이터를 피벗 형태로 변환 후 CSV 저장 및 PostgreSQL 저장"""
    all_data = []
    # CNY를 마지막에 넣기 위해 순서 지정
    ordered_currencies = ["USD", "JPY", "EUR", "CNY"]
    for currency_name in ordered_currencies:
        collection = db[currency_name]
        for doc in collection.find({}, {"date": 1, "rate": 1, "currency_code": 1, "_id": 0}):
            all_data.append({
                "date": doc["date"].date() if hasattr(doc["date"], 'date') else doc["date"],
                "currency": currency_name.lower(),
                "rate": doc["rate"]
            })
    df = pd.DataFrame(all_data)
    if df.empty:
        print("MongoDB에서 불러온 데이터가 없습니다.")
        return
    # 피벗: 날짜별, usd/jpy/eur/cny 순서로
    pivot_df = df.pivot_table(index="date", columns="currency", values="rate")
    pivot_df = pivot_df.reindex(columns=["usd", "jpy", "eur", "cny"])
    pivot_df = pivot_df.sort_index()
    print("\n=== 피벗 데이터프레임 샘플 ===")
    print(pivot_df.head())

    # PostgreSQL 직접 insert
    PG_HOST = "64.110.115.12"
    PG_DB = "exchange"
    PG_USER = "exchange_admin"
    PG_PASSWORD = "exchange_password"
    PG_TABLE = os.getenv("PG_TABLE", "exchange")
    engine = create_engine(f"postgresql+psycopg2://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:5432/{PG_DB}")
    pivot_df_reset = pivot_df.reset_index()
    expected_cols = ["date", "usd", "jpy", "eur", "cny"]
    pivot_df_reset = pivot_df_reset[expected_cols]
    from sqlalchemy import text as sa_text
    with engine.begin() as conn:
        for _, row in pivot_df_reset.iterrows():
            placeholders = ', '.join([f':{col}' for col in expected_cols])
            columns = ', '.join(expected_cols)
            sql = f'INSERT INTO public.{PG_TABLE} ({columns}) VALUES ({placeholders})'
            conn.execute(sa_text(sql), {col: row[col] for col in expected_cols})
    print(f"\nPostgreSQL({PG_DB}) {PG_TABLE} 테이블에 직접 insert 완료!")
    print(pivot_df_reset.head())

if __name__ == "__main__":
    print_exchange_samples()
    make_pivot_and_save_csv_and_postgres()
    client.close()
