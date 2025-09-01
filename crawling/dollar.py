import requests
import datetime
from pymongo import MongoClient

mongo_uri = "mongodb+srv://stradivirus:1q2w3e4r6218@cluster0.e7rvfpz.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(mongo_uri)
db = client["exchange"]
collection = db["dollar"]

def fetch_current_usdkrw():
    url = "https://query1.finance.yahoo.com/v8/finance/chart/KRW=X?interval=1h&range=1d"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()
        data = res.json()
        result_data = data.get("chart", {}).get("result")
        if not result_data:
            print("API에서 데이터를 받지 못했습니다.")
            return None
        result = result_data[0]
        timestamps = result.get("timestamp")
        indicators = result.get("indicators", {})
        quote = indicators.get("quote", [{}])[0]
        prices = quote.get("close")
        if timestamps and prices:
            dt = datetime.datetime.fromtimestamp(timestamps[-1])
            price = prices[-1]
            if price is not None:
                return {"datetime": dt, "price": price}
    except Exception as e:
        print(f"데이터 요청 또는 파싱 중 오류 발생: {e}")
    return None

def save_to_db(record):
    if record:
        collection.update_one(
            {"datetime": record["datetime"]},
            {"$set": record},
            upsert=True
        )
        print(f"{record['datetime']} 저장 완료")
    else:
        print("저장할 데이터가 없습니다.")

if __name__ == "__main__":
    record = fetch_current_usdkrw()
    if record:
        save_to_db(record)  # 무조건 저장
    else:
        print("데이터 없음")
