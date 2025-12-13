import pandas as pd
from pymongo import MongoClient
from sqlalchemy import create_engine

# 하드코딩 환경설정
mongo_uri = "mongodb+srv://stradivirus:1q2w3e4r6218@cluster0.e7rvfpz.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
mongo_db = "exchange_all"
client = MongoClient(mongo_uri)
db = client[mongo_db]

PG_HOST = "64.110.115.12"
PG_DB = "exchange"
PG_USER = "exchange_admin"
PG_PASSWORD = "exchange_password"

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
        for doc in collection.find({}, {"date": 1, "close": 1, "volume": 1, "_id": 0}):
            all_data.append({
                "date": doc["date"].date() if hasattr(doc["date"], 'date') else doc["date"],
                f"{idx_name.lower()}": doc.get("close"),
                f"{idx_name.lower()}_volume": doc.get("volume")
            })
    df = pd.DataFrame(all_data)
    if df.empty:
        print("MongoDB에서 불러온 데이터가 없습니다.")
        return
    # 날짜별로 집계(merge)
    df_grouped = df.groupby("date").first().reset_index()
    ordered_cols = [
        "date",
        "sp500", "sp500_volume",
        "dow_jones", "dow_jones_volume",
        "nasdaq", "nasdaq_volume",
        "kospi", "kospi_volume",
        "kosdaq", "kosdaq_volume"
    ]
    df_grouped = df_grouped.reindex(columns=ordered_cols)
    df_grouped = df_grouped.sort_values("date").round(4)
    print("\n=== 주가지수 DB 저장용 데이터프레임 샘플 ===")
    print(df_grouped.head())

    # PostgreSQL 직접 insert
    PG_TABLE = "stock"
    engine = create_engine(f"postgresql+psycopg2://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:5432/{PG_DB}")
    from sqlalchemy import text as sa_text
    with engine.begin() as conn:
        for _, row in df_grouped.iterrows():
            placeholders = ', '.join([f':{col}' for col in ordered_cols])
            columns = ', '.join(ordered_cols)
            sql = f'INSERT INTO public.{PG_TABLE} ({columns}) VALUES ({placeholders})'
            conn.execute(sa_text(sql), {col: row[col] for col in ordered_cols})
    print(f"\nPostgreSQL({PG_DB}) {PG_TABLE} 테이블에 직접 insert 완료!")
    print(df_grouped.head())

if __name__ == "__main__":
    make_stock_pivot_and_save()
    client.close()
