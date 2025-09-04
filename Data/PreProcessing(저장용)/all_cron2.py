"""
preprocessing_all_cron.py
- commodities, stock, exchange, interest 전처리 크론 기능을 한 파일에 직접 통합
- 각 파트별 함수로 분리, main에서 순차 실행
- 각 함수별 예외는 개별 처리 및 상세 로그
"""
import os
from dotenv import load_dotenv
import pandas as pd
from pymongo import MongoClient
from sqlalchemy import create_engine, text as sa_text
import datetime

def get_mongo():
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))
    mongo_uri = os.getenv('MONGODB_URI')
    mongo_db = os.getenv('MONGODB_DB', 'exchange_all')
    client = MongoClient(mongo_uri)
    db = client[mongo_db]
    return client, db

def get_pg_engine():
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))
    PG_HOST = os.getenv("PG_HOST")
    PG_DB = os.getenv("PG_DB")
    PG_USER = os.getenv("PG_USER")
    PG_PASSWORD = os.getenv("PG_PASSWORD")
    return create_engine(f"postgresql+psycopg2://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:5432/{PG_DB}")

# 1. Commodities
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

def upsert_commodities():
    from datetime import datetime, timedelta
    print("\n=== [PreProcessing] 원자재/지수 PostgreSQL upsert ===")
    try:
        client, db = get_mongo()
        engine = get_pg_engine()
        today = datetime.now().date()
        start_date = today - timedelta(days=4)
        date_set = set()
        spot_dict = {col: {} for col in spot_cols}
        spot_volume_dict = {f"{col}_volume": {} for col in spot_cols}
        for col in spot_cols:
            for doc in db[collection_map[col]].find({"date": {"$gte": pd.Timestamp(start_date)}}, {"date": 1, "open": 1, "high": 1, "low": 1, "close": 1, "volume": 1}):
                d = doc["date"].date() if hasattr(doc["date"], 'date') else doc["date"]
                if d >= start_date:
                    avg_price = None
                    if all(x in doc for x in ["open", "high", "low", "close"]):
                        prices = [doc.get("open"), doc.get("high"), doc.get("low"), doc.get("close")]
                        if all(p is not None for p in prices):
                            avg_price = sum(prices) / 4
                    spot_dict[col][d] = avg_price
                    spot_volume_dict[f"{col}_volume"][d] = doc.get("volume")
                    date_set.add(d)
        expected_cols = [
            'date',
            'gold', 'gold_volume',
            'silver', 'silver_volume',
            'copper', 'copper_volume',
            'crude_oil', 'crude_oil_volume',
            'brent_oil', 'brent_oil_volume'
        ]
        for date in sorted(date_set):
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
        # 인덱스(commodities_index)도 spot과 동일하게 모든 날짜의 합집합 기준으로 저장
        index_date_set = set()
        index_dict = {col: {} for col in index_cols}
        for col in index_cols:
            for doc in db[collection_map[col]].find({"date": {"$gte": pd.Timestamp(start_date)}}, {"date": 1, "close": 1}):
                d = doc["date"].date() if hasattr(doc["date"], 'date') else doc["date"]
                if d >= start_date:
                    index_dict[col][d] = doc.get("close")
                    index_date_set.add(d)
        expected_index_cols = ['date'] + index_cols
        for date in sorted(index_date_set):
            row = {col: index_dict[col].get(date) for col in index_cols}
            row_db = {"date": date}
            row_db.update(row)
            with engine.begin() as conn:
                result = conn.execute(sa_text("SELECT 1 FROM public.commodities_index WHERE date = :date"), {"date": date}).fetchone()
                if not result:
                    placeholders = ', '.join([f':{col}' for col in expected_index_cols])
                    columns = ', '.join(expected_index_cols)
                    sql = f'INSERT INTO public.commodities_index ({columns}) VALUES ({placeholders})'
                    conn.execute(sa_text(sql), {col: row_db.get(col) for col in expected_index_cols})
                    print(f"Inserted commodities_index for {date}")
                else:
                    print(f"commodities_index already exists for {date}")
        client.close()
    except Exception as e:
        print(f"[FAIL] commodities_preprocessing: {e}")

# 2. Stock
stock_indices = ["SP500", "DOW_JONES", "NASDAQ", "KOSPI", "KOSDAQ"]
def upsert_stock():
    print("\n=== [PreProcessing] 주가지수 PostgreSQL upsert ===")
    try:
        client, db = get_mongo()
        engine = get_pg_engine()
        data = {}
        volume_data = {}
        date = None
        for idx in stock_indices:
            doc = db[idx].find_one(sort=[("date", -1)])
            if doc:
                d = doc["date"].date() if hasattr(doc["date"], 'date') else doc["date"]
                data[idx.lower()] = doc.get("close")
                volume_data[f"{idx.lower()}_volume"] = doc.get("volume")
                if date is None or d > date:
                    date = d
        if data and date:
            ordered_cols = [
                "date",
                "sp500", "sp500_volume",
                "dow_jones", "dow_jones_volume",
                "nasdaq", "nasdaq_volume",
                "kospi", "kospi_volume",
                "kosdaq", "kosdaq_volume"
            ]
            row = {"date": date}
            for idx in stock_indices:
                row[idx.lower()] = data.get(idx.lower())
                row[f"{idx.lower()}_volume"] = volume_data.get(f"{idx.lower()}_volume")
            with engine.begin() as conn:
                result = conn.execute(sa_text("SELECT 1 FROM public.stock WHERE date = :date"), {"date": date}).fetchone()
                if not result:
                    placeholders = ', '.join([f':{col}' for col in ordered_cols])
                    columns = ', '.join(ordered_cols)
                    sql = f'INSERT INTO public.stock ({columns}) VALUES ({placeholders})'
                    conn.execute(sa_text(sql), {col: row.get(col) for col in ordered_cols})
                    print(f"Inserted stock for {date}")
                else:
                    print(f"stock already exists for {date}")
        client.close()
    except Exception as e:
        print(f"[FAIL] stock_preprocessing: {e}")

# 3. Exchange
def upsert_exchange():
    print("\n=== [PreProcessing] 환율 PostgreSQL upsert ===")
    try:
        client, db = get_mongo()
        engine = get_pg_engine()
        currencies = ["USD", "JPY", "EUR", "CNY"]
        data = {}
        date = None
        for currency in currencies:
            doc = db[currency].find_one(sort=[("date", -1)])
            if doc:
                d = doc["date"].date() if hasattr(doc["date"], 'date') else doc["date"]
                data[currency.lower()] = doc.get("rate")
                if date is None or d > date:
                    date = d
        if data and date:
            expected_cols = ["date", "usd", "jpy", "eur", "cny"]
            row = {"date": date}
            for c in currencies:
                row[c.lower()] = data.get(c.lower())
            with engine.begin() as conn:
                result = conn.execute(sa_text("SELECT 1 FROM public.exchange WHERE date = :date"), {"date": date}).fetchone()
                if not result:
                    placeholders = ', '.join([f':{col}' for col in expected_cols])
                    columns = ', '.join(expected_cols)
                    sql = f'INSERT INTO public.exchange ({columns}) VALUES ({placeholders})'
                    conn.execute(sa_text(sql), {col: row.get(col) for col in expected_cols})
                    print(f"Inserted exchange for {date}")
                else:
                    print(f"exchange already exists for {date}")
        client.close()
    except Exception as e:
        print(f"[FAIL] exchange_preprocessing: {e}")

# 4. Interest
def upsert_interest():
    print("\n=== [PreProcessing] 기준금리 PostgreSQL upsert ===")
    try:
        import datetime
        client, db = get_mongo()
        engine = get_pg_engine()
        today = datetime.date.today()
        start_date = today - datetime.timedelta(days=365)
        start_date_dt = datetime.datetime.combine(start_date, datetime.time.min)
        kor_cursor = db["KOR_BASE_RATE"].find({"date": {"$gte": start_date_dt}}, {"date": 1, "rate": 1, "_id": 0})
        us_cursor = db["US_FED_RATE"].find({"date": {"$gte": start_date_dt}}, {"date": 1, "rate": 1, "_id": 0})
        kor_dict = {doc["date"].date() if hasattr(doc["date"], 'date') else doc["date"]: doc.get("rate") for doc in kor_cursor}
        us_dict = {doc["date"].date() if hasattr(doc["date"], 'date') else doc["date"]: doc.get("rate") for doc in us_cursor}
        all_dates = set(kor_dict.keys()) | set(us_dict.keys())
        if not all_dates:
            print("2010년 이후 금리 데이터가 없습니다.")
            client.close()
            return
        rows = []
        for date in sorted(all_dates):
            row = {"date": date, "kor_base_rate": kor_dict.get(date), "us_fed_rate": us_dict.get(date)}
            rows.append(row)
        with engine.begin() as conn:
            for row in rows:
                date = row['date']
                kor_base_rate = row['kor_base_rate'] if row['kor_base_rate'] is not None else None
                us_fed_rate = row['us_fed_rate'] if row['us_fed_rate'] is not None else None
                exists = conn.execute(sa_text("SELECT 1 FROM interest_rate WHERE date = :date"), {"date": date}).fetchone()
                if not exists:
                    conn.execute(
                        sa_text("INSERT INTO interest_rate (date, kor_base_rate, us_fed_rate) VALUES (:date, :kor, :us)"),
                        {"date": date, "kor": kor_base_rate, "us": us_fed_rate}
                    )
                    print(f"Inserted interest_rate for {date}")
                else:
                    print(f"interest_rate already exists for {date}")
        client.close()
    except Exception as e:
        print(f"[FAIL] interest_preprocessing: {e}")

if __name__ == "__main__":
    print("=== 모든 PreProcessing 크론 작업 시작 ===")
    upsert_commodities()
    upsert_stock()
    upsert_exchange()
    upsert_interest()
    print("=== 모든 PreProcessing 크론 작업 종료 ===")
