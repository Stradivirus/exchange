import pandas as pd
from pymongo import MongoClient
import os
from sqlalchemy import create_engine

# MongoDB 연결
client = MongoClient("mongodb+srv://stradivirus:1q2w3e4r6218@cluster0.e7rvfpz.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client['exchange_all']

# 원자재(현물) 및 인덱스 컬렉션명
spot_cols = ["gold", "silver", "copper", "crude_oil", "brent_oil"]
index_cols = ["dxy", "vix"]
collection_map = {
    "gold": "GOLD",
    "silver": "SILVER",
    "copper": "COPPER",
    "crude_oil": "CRUDE_OIL",
    "brent_oil": "BRENT_OIL",
    "dxy": "DXY",
    # "usd_index": "USD_INDEX",  # 중복 제거
    "vix": "VIX"
}

def make_and_save_commodities():
    """MongoDB에서 원자재/지수 데이터를 읽어와 피벗, 반올림, CSV/DB 저장"""
    all_data = []
    for col in spot_cols + index_cols:
        collection = db[collection_map[col]]
        for doc in collection.find({}, {"date": 1, "close": 1, "_id": 0}):
            all_data.append({
                "date": doc["date"].date() if hasattr(doc["date"], 'date') else doc["date"],
                "item": col,
                "close": doc.get("close")
            })
    df = pd.DataFrame(all_data)
    if df.empty:
        print("MongoDB에서 불러온 데이터가 없습니다.")
        return

    # 현물(commodities) 피벗
    spot_pivot = df[df["item"].isin(spot_cols)].pivot_table(index="date", columns="item", values="close")
    spot_pivot = spot_pivot.reindex(columns=spot_cols)
    spot_pivot = spot_pivot.sort_index().round(4)
    print("\n=== 현물(commodities) 피벗 샘플 ===")
    print(spot_pivot.tail())
    spot_csv = "commodities.csv"
    spot_pivot.to_csv(spot_csv, encoding="utf-8-sig")
    print(f"CSV로 저장 완료: {spot_csv}")

    # 인덱스(commodities_index) 피벗
    index_pivot = df[df["item"].isin(index_cols)].pivot_table(index="date", columns="item", values="close")
    index_pivot = index_pivot.reindex(columns=index_cols)
    index_pivot = index_pivot.sort_index().round(4)
    print("\n=== 인덱스(commodities_index) 피벗 샘플 ===")
    print(index_pivot.tail())
    index_csv = "commodities_index.csv"
    index_pivot.to_csv(index_csv, encoding="utf-8-sig")
    print(f"CSV로 저장 완료: {index_csv}")

    # PostgreSQL 저장
    PG_HOST = os.getenv("PG_HOST", "64.110.115.12")
    PG_DB = os.getenv("PG_DB", "exchange")
    PG_USER = os.getenv("PG_USER", "exchange_admin")
    PG_PASSWORD = os.getenv("PG_PASSWORD", "exchange_password")
    engine = create_engine(f"postgresql+psycopg2://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:5432/{PG_DB}")

    # 현물 테이블 저장
    spot_pivot_reset = spot_pivot.reset_index()
    spot_pivot_reset.to_sql("commodities", engine, if_exists="append", index=False)
    print("\nPostgreSQL(commodities) 테이블에 저장 완료!")

    # 인덱스 테이블 저장
    index_pivot_reset = index_pivot.reset_index()
    index_pivot_reset.to_sql("commodities_index", engine, if_exists="append", index=False)
    print("PostgreSQL(commodities_index) 테이블에 저장 완료!")

if __name__ == "__main__":
    make_and_save_commodities()
    client.close()
