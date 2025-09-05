from pymongo import MongoClient
from sqlalchemy import create_engine

# 하드코딩 환경설정
MONGO_URI = "mongodb+srv://stradivirus:1q2w3e4r6218@cluster0.e7rvfpz.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
MONGO_DB = "exchange_all"
PG_HOST = "64.110.115.12"
PG_DB = "exchange"
PG_USER = "exchange_admin"
PG_PASSWORD = "exchange_password"

def get_mongo():
    client = MongoClient(MONGO_URI)
    db = client[MONGO_DB]
    return client, db

def get_pg_engine():
    return create_engine(f"postgresql+psycopg2://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:5432/{PG_DB}")

currencies = ["USD", "JPY", "EUR", "CNY"]

def upsert_exchange():
    client, db = get_mongo()
    engine = get_pg_engine()
    # 각 통화별 최신 데이터 수집
    data = {}
    date = None
    for currency in currencies:
        doc = db[currency].find_one(sort=[("date", -1)])
        if doc:
            d = doc["date"].date() if hasattr(doc["date"], 'date') else doc["date"]
            rate = doc.get("rate")
            if rate is not None:
                rate = round(rate, 4)
            data[currency.lower()] = rate
            if date is None or d > date:
                date = d
    if data and date:
        from sqlalchemy import text as sa_text
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

if __name__ == "__main__":
    upsert_exchange()
