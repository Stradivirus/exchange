import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
import datetime

mongo_uri = "mongodb+srv://stradivirus:1q2w3e4r6218@cluster0.e7rvfpz.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(mongo_uri)
db = client["exchange"]
collection = db["base_rate"]

def fetch_latest_base_rate():
    url = "https://www.bok.or.kr/portal/singl/baseRate/list.do?dataSeCd=01&menuNo=200643"
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")
    tbody = soup.find("tbody")
    for tr in tbody.find_all("tr"):
        tds = tr.find_all("td")
        if len(tds) == 3:
            year = tds[0].get_text(strip=True)
            date_str = tds[1].get_text(strip=True)
            rate_str = tds[2].get_text(strip=True)
            try:
                date = datetime.datetime.strptime(f"{year} {date_str}", "%Y %m월 %d일")
                rate = float(rate_str)
                return {"date": date, "rate": rate}
            except Exception as e:
                continue
    return None

def get_last_rate():
    doc = collection.find_one(sort=[("date", -1)])
    if doc:
        return doc["rate"]
    return None

def save_to_db(record):
    if record:
        collection.update_one(
            {"date": record["date"], "rate": record["rate"]},
            {"$set": record},
            upsert=True
        )
        print(f"{record['date']} 기준금리 {record['rate']} 저장 완료")
    else:
        print("저장할 데이터가 없습니다.")

if __name__ == "__main__":
    record = fetch_latest_base_rate()
    if record:
        last_rate = get_last_rate()
        if last_rate is None or record["rate"] != last_rate:
            save_to_db(record)
        else:
            print("변동 없음, 저장하지 않음")
    else:
        print("데이터 없음")