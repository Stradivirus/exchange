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

stock_indices = ["SP500", "DOW_JONES", "NASDAQ", "KOSPI", "KOSDAQ"]

def upsert_stock():
    client, db = get_mongo()
    engine = get_pg_engine()
    data = {}
    volume_data = {}
    date = None
    for idx in stock_indices:
        doc = db[idx].find_one(sort=[("date", -1)])
        if doc:
            d = doc["date"].date() if hasattr(doc["date"], 'date') else doc["date"]
            close_val = doc.get("close")
            volume_val = doc.get("volume")
            data[idx.lower()] = round(close_val, 4) if close_val is not None else None
            volume_data[f"{idx.lower()}_volume"] = round(volume_val, 4) if volume_val is not None else None
            if date is None or d > date:
                date = d
    if data and date:
        from sqlalchemy import text as sa_text
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

if __name__ == "__main__":
    upsert_stock()
