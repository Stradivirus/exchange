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
    "vix": "VIX"
}

def make_and_save_commodities():
    """MongoDB에서 원자재/지수 데이터를 읽어와 피벗, 반올림, CSV/DB 저장"""
    all_data = []
    for col in spot_cols + index_cols:
        collection = db[collection_map[col]]
        for doc in collection.find({}, {"date": 1, "open": 1, "high": 1, "low": 1, "close": 1, "volume": 1, "_id": 0}):
            avg_price = None
            if all(x in doc for x in ["open", "high", "low", "close"]):
                prices = [doc.get("open"), doc.get("high"), doc.get("low"), doc.get("close")]
                if all(p is not None for p in prices):
                    avg_price = sum(prices) / 4
            row = {
                "date": doc["date"].date() if hasattr(doc["date"], 'date') else doc["date"],
                "item": col
            }
            if col in spot_cols:
                row[col] = avg_price
                row[f"{col}_volume"] = doc.get("volume")
            else:
                row[col] = avg_price
            all_data.append(row)
    df = pd.DataFrame(all_data)
    if df.empty:
        print("MongoDB에서 불러온 데이터가 없습니다.")
        return

    # 현물(commodities) 피벗
    spot_value_cols = []
    for col in spot_cols:
        spot_value_cols.append(col)
        spot_value_cols.append(f"{col}_volume")
    spot_pivot = df[df["item"].isin(spot_cols)].pivot_table(index="date", values=spot_value_cols, aggfunc="first")
    spot_pivot = spot_pivot.reindex(columns=spot_value_cols)
    spot_pivot = spot_pivot.sort_index().round(4)
    print("\n=== 현물(commodities) 평균가+거래량 피벗 샘플 ===")
    print(spot_pivot.tail())

    # 인덱스(commodities_index) 피벗
    index_pivot = df[df["item"].isin(index_cols)].pivot_table(index="date", values=index_cols, aggfunc="first")
    index_pivot = index_pivot.reindex(columns=index_cols)
    index_pivot = index_pivot.sort_index().round(4)
    print("\n=== 인덱스(commodities_index) 평균가 피벗 샘플 ===")
    print(index_pivot.tail())

    # PostgreSQL 저장
    PG_HOST = os.getenv("PG_HOST")
    PG_DB = os.getenv("PG_DB")
    PG_USER = os.getenv("PG_USER")
    PG_PASSWORD = os.getenv("PG_PASSWORD")
    engine = create_engine(f"postgresql+psycopg2://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:5432/{PG_DB}")

    # 현물 테이블 직접 insert (to_sql 대신)
    spot_pivot_reset = spot_pivot.reset_index()
    expected_cols = [
        'date',
        'gold', 'gold_volume',
        'silver', 'silver_volume',
        'copper', 'copper_volume',
        'crude_oil', 'crude_oil_volume',
        'brent_oil', 'brent_oil_volume'
    ]
    spot_pivot_reset = spot_pivot_reset[expected_cols]
    from sqlalchemy import text
    with engine.begin() as conn:
        for _, row in spot_pivot_reset.iterrows():
            placeholders = ', '.join([f':{col}' for col in expected_cols])
            columns = ', '.join(expected_cols)
            sql = f'INSERT INTO public.commodities ({columns}) VALUES ({placeholders})'
            conn.execute(text(sql), {col: row[col] for col in expected_cols})
    print("\nPostgreSQL(commodities) 테이블에 저장 완료!")

    # 인덱스 테이블 저장
    index_pivot_reset = index_pivot.reset_index()
    index_pivot_reset.to_sql("commodities_index", engine, if_exists="append", index=False)
    print("PostgreSQL(commodities_index) 테이블에 저장 완료!")

if __name__ == "__main__":
    make_and_save_commodities()
    client.close()
