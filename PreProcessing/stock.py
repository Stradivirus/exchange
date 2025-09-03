import pandas as pd
from pymongo import MongoClient
import os
from sqlalchemy import create_engine

# MongoDB 연결
client = MongoClient("mongodb+srv://stradivirus:1q2w3e4r6218@cluster0.e7rvfpz.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client['exchange_all']

# 주가지수 컬렉션명과 컬럼명 매핑 (순서: sp500, dow_jones, nasdaq, kospi, kosdaq)
stock_indices = {
    "SP500": "SP500",
    "DOW_JONES": "DOW_JONES",
    "NASDAQ": "NASDAQ",
    "KOSPI": "KOSPI",
    "KOSDAQ": "KOSDAQ"
}

def make_stock_pivot_and_save():
    """MongoDB에서 주가지수 데이터를 읽어와 피벗, 반올림, 샘플 출력, CSV/DB 저장"""
    all_data = []
    for idx_name, collection_name in stock_indices.items():
        collection = db[collection_name]
        for doc in collection.find({}, {"date": 1, "close": 1, "_id": 0}):
            all_data.append({
                "date": doc["date"].date() if hasattr(doc["date"], 'date') else doc["date"],
                "index": idx_name.lower(),
                "close": doc.get("close")
            })
    df = pd.DataFrame(all_data)
    if df.empty:
        print("MongoDB에서 불러온 데이터가 없습니다.")
        return
    # 피벗 및 컬럼 순서 지정
    ordered_cols = ["sp500", "dow_jones", "nasdaq", "kospi", "kosdaq"]
    pivot_df = df.pivot_table(index="date", columns="index", values="close")
    pivot_df = pivot_df.reindex(columns=ordered_cols)
    pivot_df = pivot_df.sort_index()
    pivot_df = pivot_df.round(4)

    print("\n=== 주가지수 피벗 데이터프레임 샘플 ===")
    print(pivot_df.head())

    # CSV 저장
    csv_path = "stock_pivot.csv"
    pivot_df.to_csv(csv_path, encoding="utf-8-sig")
    print(f"\nCSV로 저장 완료: {csv_path}")

    # PostgreSQL 저장
    PG_HOST = os.getenv("PG_HOST", "64.110.115.12")
    PG_DB = os.getenv("PG_DB", "exchange")
    PG_USER = os.getenv("PG_USER", "exchange_admin")
    PG_PASSWORD = os.getenv("PG_PASSWORD", "exchange_password")
    PG_TABLE = os.getenv("PG_TABLE", "stock")
    engine = create_engine(f"postgresql+psycopg2://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:5432/{PG_DB}")
    pivot_df_reset = pivot_df.reset_index()
    # append로 저장 (파티션 테이블 구조 유지)
    pivot_df_reset.to_sql(PG_TABLE, engine, if_exists="append", index=False)
    print(f"\nPostgreSQL({PG_DB}) {PG_TABLE} 테이블에 저장 완료!")
    print(pivot_df_reset.head())

if __name__ == "__main__":
    make_stock_pivot_and_save()
    client.close()
