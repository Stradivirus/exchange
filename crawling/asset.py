import requests
import datetime
from pymongo import MongoClient

mongo_uri = "mongodb+srv://stradivirus:1q2w3e4r6218@cluster0.e7rvfpz.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(mongo_uri)
db = client["exchange"]

def fetch_latest_price(symbol):
    today = datetime.datetime.now()
    start_dt = today.replace(hour=0, minute=0, second=0, microsecond=0)
    end_dt = today
    start = int(start_dt.timestamp())
    end = int(end_dt.timestamp())
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?period1={start}&period2={end}&interval=1d"
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers)
    data = res.json()
    result_data = data.get("chart", {}).get("result")
    if not result_data:
        print(f"{symbol}: API에서 데이터를 받지 못했습니다.")
        return None
    timestamps = result_data[0]["timestamp"]
    prices = result_data[0]["indicators"]["quote"][0]["close"]
    if timestamps and prices:
        dt = datetime.datetime.fromtimestamp(timestamps[-1])
        price = prices[-1]
        if price is not None:
            return {"datetime": dt, "price": price}
    return None

def save_to_db(collection_name, record):
    if record:
        collection = db[collection_name]
        collection.update_one(
            {"datetime": record["datetime"]},
            {"$set": record},
            upsert=True
        )
        print(f"{collection_name}: {record['datetime']} {record['price']} 저장 완료")
    else:
        print(f"{collection_name}: 저장할 데이터가 없습니다.")

if __name__ == "__main__":
    assets = [
        ("gold", "GC=F"),
        ("oil", "CL=F"),
        ("dxy", "DX-Y.NYB"),
    ]
    for collection_name, symbol in assets:
        record = fetch_latest_price(symbol)
        save_to_db(collection_name, record)