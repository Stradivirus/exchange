from pymongo import MongoClient
import datetime

mongo_uri = "mongodb+srv://stradivirus:1q2w3e4r6218@cluster0.e7rvfpz.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(mongo_uri)
db = client["exchange"]
collection = db["us_base_rate"]

# 예시: 여러 건 한 번에 입력
history = [
    {"date": datetime.datetime(2024, 8, 1), "rate": 5.5},
    {"date": datetime.datetime(2024, 9, 19), "rate": 5.0},
    {"date": datetime.datetime(2024, 11, 8), "rate": 4.75},
    {"date": datetime.datetime(2024, 12, 19), "rate": 4.5},
    # ... 필요한 만큼 추가
]

for rec in history:
    collection.update_one(
        {"date": rec["date"]},
        {"$set": rec},
        upsert=True
    )
print("과거 금리 변동 이력 저장 완료")
