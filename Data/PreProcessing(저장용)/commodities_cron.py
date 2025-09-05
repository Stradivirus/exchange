from pymongo import MongoClient
from sqlalchemy import create_engine

# 하드코딩 환경설정
MONGO_URI = "mongodb+srv://stradivirus:1q2w3e4r6218@cluster0.e7rvfpz.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
MONGO_DB = "exchange_all"
PG_HOST = "64.110.115.12"
PG_DB = "exchange"
PG_USER = "exchange_admin"
PG_PASSWORD = "exchange_password"

# MongoDB 연결
def get_mongo():
    client = MongoClient(MONGO_URI)
    db = client[MONGO_DB]
    return client, db

# PostgreSQL 연결
def get_pg_engine():
    return create_engine(f"postgresql+psycopg2://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:5432/{PG_DB}")

spot_cols = ["gold", "silver", "copper", "crude_oil", "brent_oil"]
grains_cols = ["corn", "wheat", "rice", "coffee", "sugar"]
index_cols = ["dxy", "vix"]
collection_map = {
    "gold": "GOLD",
    "silver": "SILVER",
    "copper": "COPPER",
    "crude_oil": "CRUDE_OIL",
    "brent_oil": "BRENT_OIL",
    "corn": "CORN",
    "wheat": "WHEAT",
    "rice": "RICE",
    "coffee": "COFFEE",
    "sugar": "SUGAR",
    "dxy": "DXY",
    "vix": "VIX"
}

def upsert_commodities():
    """MongoDB에서 최근 5일치 원자재 데이터를 읽어와 평균가/거래량을 PostgreSQL에 upsert"""
    from datetime import datetime, timedelta
    from sqlalchemy import text as sa_text
    client, db = get_mongo()
    engine = get_pg_engine()

    today = datetime.now().date()
    start_date = today - timedelta(days=4)
    date_set = set()
    spot_dict = {col: {} for col in spot_cols}
    spot_volume_dict = {f"{col}_volume": {} for col in spot_cols}
    grains_dict = {col: {} for col in grains_cols}
    grains_volume_dict = {f"{col}_volume": {} for col in grains_cols}

    # MongoDB에서 최근 5일치 데이터 수집 및 평균가/거래량 계산 (현물)
    for col in spot_cols:
        for doc in db[collection_map[col]].find({"date": {"$gte": pd.Timestamp(start_date)}}, {"date": 1, "open": 1, "high": 1, "low": 1, "close": 1, "volume": 1}):
            d = doc["date"].date() if hasattr(doc["date"], 'date') else doc["date"]
            if d >= start_date:
                avg_price = None
                if all(x in doc for x in ["open", "high", "low", "close"]):
                    prices = [doc.get("open"), doc.get("high"), doc.get("low"), doc.get("close")]
                    if all(p is not None for p in prices):
                        avg_price = round(sum(prices) / 4, 4)
                spot_dict[col][d] = avg_price
                spot_volume_dict[f"{col}_volume"][d] = doc.get("volume")
                date_set.add(d)

    # MongoDB에서 최근 5일치 데이터 수집 및 평균가/거래량 계산 (곡물)
    for col in grains_cols:
        for doc in db[collection_map[col]].find({"date": {"$gte": pd.Timestamp(start_date)}}, {"date": 1, "open": 1, "high": 1, "low": 1, "close": 1, "volume": 1}):
            d = doc["date"].date() if hasattr(doc["date"], 'date') else doc["date"]
            if d >= start_date:
                avg_price = None
                if all(x in doc for x in ["open", "high", "low", "close"]):
                    prices = [doc.get("open"), doc.get("high"), doc.get("low"), doc.get("close")]
                    if all(p is not None for p in prices):
                        avg_price = round(sum(prices) / 4, 4)
                grains_dict[col][d] = avg_price
                grains_volume_dict[f"{col}_volume"][d] = doc.get("volume")
                date_set.add(d)

    expected_cols = [
        'date',
        'gold', 'gold_volume',
        'silver', 'silver_volume',
        'copper', 'copper_volume',
        'crude_oil', 'crude_oil_volume',
        'brent_oil', 'brent_oil_volume'
    ]

    # PostgreSQL에 upsert (존재하지 않을 때만 insert)
    for date in sorted(date_set):
        # 현물
        row = {col: spot_dict[col].get(date) for col in spot_cols}
        for col in spot_cols:
            row[f"{col}_volume"] = spot_volume_dict[f"{col}_volume"].get(date)
        row_db = {"date": date}
        row_db.update(row)
        with engine.begin() as conn:
            result = conn.execute(sa_text("SELECT 1 FROM public.commodities WHERE date = :date"), {"date": date}).fetchone()
            if not result:
                placeholders = ', '.join([f':{col}' for col in expected_cols])
                columns = ', '.join(expected_cols)
                sql = f'INSERT INTO public.commodities ({columns}) VALUES ({placeholders})'
                conn.execute(sa_text(sql), {col: row_db.get(col) for col in expected_cols})
                print(f"Inserted commodities for {date}")
            else:
                print(f"commodities already exists for {date}")

        # 곡물
        grains_expected_cols = [
            'date',
            'corn', 'corn_volume',
            'wheat', 'wheat_volume',
            'rice', 'rice_volume',
            'coffee', 'coffee_volume',
            'sugar', 'sugar_volume'
        ]
        grains_row = {col: grains_dict[col].get(date) for col in grains_cols}
        for col in grains_cols:
            grains_row[f"{col}_volume"] = grains_volume_dict[f"{col}_volume"].get(date)
        grains_row_db = {"date": date}
        grains_row_db.update(grains_row)
        with engine.begin() as conn:
            result = conn.execute(sa_text("SELECT 1 FROM public.grains WHERE date = :date"), {"date": date}).fetchone()
            if not result:
                placeholders = ', '.join([f':{col}' for col in grains_expected_cols])
                columns = ', '.join(grains_expected_cols)
                sql = f'INSERT INTO public.grains ({columns}) VALUES ({placeholders})'
                conn.execute(sa_text(sql), {col: grains_row_db.get(col) for col in grains_expected_cols})
                print(f"Inserted grains for {date}")
            else:
                print(f"grains already exists for {date}")
    # 인덱스(commodities_index)도 spot과 동일하게 모든 날짜의 합집합 기준으로 저장
    index_date_set = set()
    index_dict = {col: {} for col in index_cols}
    for col in index_cols:
        for doc in db[collection_map[col]].find({"date": {"$gte": pd.Timestamp(start_date)}}, {"date": 1, "close": 1}):
            d = doc["date"].date() if hasattr(doc["date"], 'date') else doc["date"]
            if d >= start_date:
                index_dict[col][d] = doc.get("close")
                index_date_set.add(d)
    for date in sorted(index_date_set):
        row = {col: index_dict[col].get(date) for col in index_cols}
        row_db = {"date": date}
        row_db.update(row)
        # to_sql은 파티션 테이블이 아니므로, 인덱스 테이블은 그대로 사용
        import pandas as pd
        pd.DataFrame([row_db]).to_sql("commodities_index", engine, if_exists="append", index=False)
        print(f"Inserted commodities_index for {date}")
    client.close()

if __name__ == "__main__":
    upsert_commodities()
