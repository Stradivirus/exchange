from pymongo import MongoClient
from sqlalchemy import create_engine, text

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

def upsert_interest():
    import datetime
    client, db = get_mongo()
    engine = get_pg_engine()
    today = datetime.date.today()
    # 최근 1년(365일) 데이터만 insert
    start_date = today - datetime.timedelta(days=365)
    kor_cursor = db["KOR_BASE_RATE"].find({"date": {"$gte": start_date}}, {"date": 1, "rate": 1, "_id": 0})
    us_cursor = db["US_FED_RATE"].find({"date": {"$gte": start_date}}, {"date": 1, "rate": 1, "_id": 0})
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
    with engine.connect() as conn:
        for row in rows:
            date = row['date']
            kor_base_rate = row['kor_base_rate'] if row['kor_base_rate'] is not None else None
            us_fed_rate = row['us_fed_rate'] if row['us_fed_rate'] is not None else None
            exists = conn.execute(text("SELECT 1 FROM interest_rate WHERE date = :date"), {"date": date}).fetchone()
            if not exists:
                conn.execute(
                    text("INSERT INTO interest_rate (date, kor_base_rate, us_fed_rate) VALUES (:date, :kor, :us)"),
                    {"date": date, "kor": kor_base_rate, "us": us_fed_rate}
                )
                print(f"Inserted interest_rate for {date}")
            else:
                print(f"interest_rate already exists for {date}")
    client.close()

if __name__ == "__main__":
    upsert_interest()
