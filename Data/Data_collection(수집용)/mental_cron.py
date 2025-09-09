from pymongo import MongoClient
import requests
import pandas as pd
from datetime import datetime, timedelta
import time

# 하드코딩 환경설정
mongo_uri = "mongodb+srv://stradivirus:1q2w3e4r6218@cluster0.e7rvfpz.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
mongo_db = "exchange_all"
api_key = "GYMU5SDZ3BMQ9GWY2JAF"

client = MongoClient(mongo_uri)
db = client[mongo_db]

sentiment_indicators = {
    "511Y004": {  # 소비자심리지수
        "collection_name": "consumer_sentiment",
        "indicator_name": "소비자심리지수",
        "item_codes": ["FME"],
        "period": "M"
    },
    "513Y001": {  # 경제심리지수
        "collection_name": "economic_sentiment",
        "indicator_name": "경제심리지수",
        "item_codes": ["E1000"],
        "period": "M"
    },
    "521Y001": {  # 뉴스심리지수
        "collection_name": "news_sentiment",
        "indicator_name": "뉴스심리지수",
        "item_codes": ["A001"],
        "period": "D"
    }
}

def get_sentiment_data_batch(stat_code, item_code, start_date, end_date, period="M"):
    url = f"https://ecos.bok.or.kr/api/StatisticSearch/{api_key}/json/kr/1/10000/{stat_code}/{period}/{start_date}/{end_date}/{item_code}"
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if 'StatisticSearch' in data and 'row' in data['StatisticSearch']:
                rows = data['StatisticSearch']['row']
                df = pd.DataFrame(rows)
                if period == "D":
                    df['date'] = pd.to_datetime(df['TIME'], format='%Y%m%d')
                else:
                    df['date'] = pd.to_datetime(df['TIME'], format='%Y%m')
                df['value'] = pd.to_numeric(df['DATA_VALUE'], errors='coerce')
                df['stat_code'] = stat_code
                df['item_code'] = item_code
                df['item_name'] = df['ITEM_NAME1']
                df['unit_name'] = df['UNIT_NAME']
                df['created_at'] = datetime.now()
                if stat_code == "511Y004":
                    df['region_code'] = df['ITEM_CODE2']
                    df['region_name'] = df['ITEM_NAME2']
                return df[['date', 'value', 'stat_code', 'item_code', 'item_name', 'unit_name', 'created_at'] +
                         (['region_code', 'region_name'] if stat_code == "511Y004" else [])]
            else:
                print(f"데이터가 없습니다 - 통계코드: {stat_code}, 항목코드: {item_code}")
                return pd.DataFrame()
        else:
            print(f"API 오류 {response.status_code} - 통계코드: {stat_code}")
            return pd.DataFrame()
    except Exception as e:
        print(f"오류 발생 - 통계코드 {stat_code}: {e}")
        return pd.DataFrame()

def save_sentiment_to_mongodb(collection_name, df):
    if df.empty:
        print(f"{collection_name}: 저장할 데이터가 없습니다.")
        return
    collection = db[collection_name]
    collection.create_index([("date", 1), ("item_code", 1)], unique=True)
    records = df.to_dict('records')
    inserted_count = 0
    for record in records:
        try:
            # 중복 방지: 이미 존재하면 skip
            exists = collection.find_one({"date": record['date'], "item_code": record['item_code']})
            if exists:
                continue
            result = collection.replace_one(
                {"date": record['date'], "item_code": record['item_code']},
                record,
                upsert=True
            )
            if result.upserted_id:
                inserted_count += 1
        except Exception as e:
            print(f"저장 오류 - {collection_name}: {e}")
    print(f"{collection_name}: 신규 {inserted_count}개 저장 완료")

def main():
    print("=== 심리지수 데이터 크론 수집 시작 ===")
    for stat_code, config in sentiment_indicators.items():
        print(f"\n--- {config['indicator_name']} 데이터 수집 중 ---")
        collection = db[config['collection_name']]
        # 최근 7일(오늘 포함) 기간 계산
        today_dt = datetime.now()
        if config['period'] == "D":
            start_dt = today_dt - timedelta(days=6)
            start_date = start_dt.strftime('%Y%m%d')
            today = today_dt.strftime('%Y%m%d')
        else:
            # 월별은 최근 1개월만
            start_dt = (today_dt - pd.DateOffset(months=1)).replace(day=1)
            start_date = start_dt.strftime('%Y%m')
            today = today_dt.strftime('%Y%m')
        print(f"최근 7일(또는 1개월) 수집 기간: {start_date} ~ {today}")
        time.sleep(1)
        for item_code in config['item_codes']:
            print(f"항목코드 {item_code} 수집 중...")
            df = get_sentiment_data_batch(
                stat_code,
                item_code,
                start_date,
                today,
                config['period']
            )
            if not df.empty:
                print(f"{config['indicator_name']}: {len(df)}개 데이터 조회 완료")
                save_sentiment_to_mongodb(config['collection_name'], df)
            else:
                print(f"{config['indicator_name']}: 조회된 데이터가 없습니다")
            time.sleep(0.5)
    print("\n=== 심리지수 크론 데이터 저장 완료 ===")

if __name__ == "__main__":
    main()
    client.close()
