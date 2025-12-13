from pymongo import MongoClient
from sqlalchemy import create_engine
import pandas as pd

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
    start_date = today - timedelta(days=365*3)
    
    date_set = set()
    spot_dict = {col: {} for col in spot_cols}
    spot_volume_dict = {f"{col}_volume": {} for col in spot_cols}
    grains_dict = {col: {} for col in grains_cols}
    grains_volume_dict = {f"{col}_volume": {} for col in grains_cols}

    # MongoDB에서 최근 5일치 데이터 수집 및 평균가/거래량 계산 (현물)
    for col in spot_cols:
        print(f"Processing spot commodity: {col}")
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
        print(f"Processing grain: {col}")
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
        'date', 'gold', 'gold_volume', 'silver', 'silver_volume', 'copper', 'copper_volume',
        'crude_oil', 'crude_oil_volume', 'brent_oil', 'brent_oil_volume'
    ]

    # PostgreSQL에 upsert (존재하지 않을 때만 insert) - 현물
    for date in sorted(date_set):
        row = {col: spot_dict[col].get(date) for col in spot_cols}
        for col in spot_cols:
            row[f"{col}_volume"] = spot_volume_dict[f"{col}_volume"].get(date)
        row_db = {"date": date}
        row_db.update(row)

        # DB 저장 대신 터미널 출력
        print(f"[commodities] {row_db}")

        # 곡물
        grains_expected_cols = [
            'date', 'corn', 'corn_volume', 'wheat', 'wheat_volume', 'rice', 'rice_volume',
            'coffee', 'coffee_volume', 'sugar', 'sugar_volume'
        ]
        grains_row = {col: grains_dict[col].get(date) for col in grains_cols}
        for col in grains_cols:
            grains_row[f"{col}_volume"] = grains_volume_dict[f"{col}_volume"].get(date)
        grains_row_db = {"date": date}
        grains_row_db.update(grains_row)

        print(f"[grains] {grains_row_db}")

    # 인덱스 처리 (중복 방지 및 VIX 문제 해결)
    index_date_set = set()
    index_dict = {col: {} for col in index_cols}
    
    for col in index_cols:
        collection_name = collection_map[col]
        print(f"Processing index: {col} from collection {collection_name}")
        
        # MongoDB에서 인덱스 데이터 조회 (close와 price 필드 모두 확인)
        for doc in db[collection_name].find(
            {"date": {"$gte": pd.Timestamp(start_date)}}, 
            {"date": 1, "close": 1, "price": 1}
        ):
            d = doc["date"].date() if hasattr(doc["date"], 'date') else doc["date"]
            if d >= start_date:
                # close 또는 price 필드 중 존재하는 것 사용 (VIX는 둘 다 있음)
                value = doc.get("close") or doc.get("price")
                if value is not None:
                    index_dict[col][d] = round(float(value), 4)  # ← 이 부분 추가
                    print(f"Found {col} data for {d}: {round(float(value), 4)}")
                index_date_set.add(d)

    # 인덱스 데이터 출력
    index_expected_cols = ['date', 'dxy', 'vix']
    for date in sorted(index_date_set):
        row = {col: index_dict[col].get(date) for col in index_cols}
        row_db = {"date": date}
        row_db.update(row)
        print(f"[commodities_index] {row_db}")

    client.close()

if __name__ == "__main__":
    upsert_commodities()
