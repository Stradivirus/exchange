
import os
from dotenv import load_dotenv
from pymongo import MongoClient
import requests
import pandas as pd
from datetime import datetime
import time


# 환경변수 로드
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))
mongo_uri = os.getenv('MONGODB_URI')
mongo_db = os.getenv('MONGODB_DB', 'exchange_all')
api_key = os.getenv('BOK_API_KEY')
stat_code = "731Y001"
client = MongoClient(mongo_uri)
db = client[mongo_db]

# 각 통화별 컬렉션 이름 설정
currencies = {
    "0000001": "USD",  # 달러
    "0000002": "JPY",  # 엔 (100엔당)
    "0000053": "CNY",  # 위안
    "0000003": "EUR"   # 유로
}

def get_exchange_rate_batch(currency_code, start_date, end_date):
    """
    환율 데이터를 배치로 조회하는 함수
    API 제한을 고려하여 한 번에 최대 100개 데이터만 조회
    """
    url = f"https://ecos.bok.or.kr/api/StatisticSearch/{api_key}/json/kr/1/10000/{stat_code}/D/{start_date}/{end_date}/{currency_code}"
    
    try:
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'StatisticSearch' in data and 'row' in data['StatisticSearch']:
                rows = data['StatisticSearch']['row']
                df = pd.DataFrame(rows)
                
                # 데이터 정제
                df['date'] = pd.to_datetime(df['TIME'], format='%Y%m%d')
                df['rate'] = df['DATA_VALUE'].astype(float)
                df['currency_code'] = currency_code
                df['unit_name'] = df['UNIT_NAME']
                df['created_at'] = datetime.now()
                
                return df[['date', 'rate', 'currency_code', 'unit_name', 'created_at']]
            else:
                print(f"데이터가 없습니다 - 통화코드: {currency_code}")
                return pd.DataFrame()
        else:
            print(f"API 오류 {response.status_code} - 통화코드: {currency_code}")
            return pd.DataFrame()
            
    except Exception as e:
        print(f"오류 발생 - 통화코드 {currency_code}: {e}")
        return pd.DataFrame()

def save_to_mongodb(currency_name, df):
    """MongoDB에 데이터 저장"""
    if df.empty:
        print(f"{currency_name}: 저장할 데이터가 없습니다.")
        return
    
    collection = db[currency_name]
    
    # 기존 인덱스 생성 (중복 방지)
    collection.create_index([("date", 1), ("currency_code", 1)], unique=True)
    
    # 데이터 저장
    records = df.to_dict('records')
    inserted_count = 0
    updated_count = 0
    
    for record in records:
        try:
            result = collection.replace_one(
                {"date": record['date'], "currency_code": record['currency_code']},
                record,
                upsert=True
            )
            if result.upserted_id:
                inserted_count += 1
            else:
                updated_count += 1
        except Exception as e:
            print(f"저장 오류 - {currency_name}: {e}")
    
    print(f"{currency_name}: 신규 {inserted_count}개, 업데이트 {updated_count}개 저장 완료")

def main():
    """메인 실행 함수"""
    print("=== 환율 데이터 수집 및 저장 시작 ===")
    
    # 날짜 설정 (2010년 1월 1일부터 오늘까지)
    start_date = "20100101"
    today = datetime.now().strftime('%Y%m%d')
    
    print(f"수집 기간: {start_date} ~ {today}")
    
    for currency_code, currency_name in currencies.items():
        print(f"\n--- {currency_name} 환율 데이터 수집 중 ---")
        
        # API 호출 제한을 고려한 지연
        time.sleep(1)
        
        # 데이터 조회
        df = get_exchange_rate_batch(currency_code, start_date, today)
        
        if not df.empty:
            print(f"{currency_name}: {len(df)}개 데이터 조회 완료")
            
            # MongoDB에 저장
            save_to_mongodb(currency_name, df)
            
            # 최신 데이터 확인
            latest_rate = df.iloc[-1]
            print(f"{currency_name} 최신 환율: {latest_rate['rate']:.2f} ({latest_rate['date'].strftime('%Y-%m-%d')})")
        else:
            print(f"{currency_name}: 조회된 데이터가 없습니다")
    
    print("\n=== 모든 환율 데이터 저장 완료 ===")
    
    # 저장된 데이터 확인
    print("\n=== 저장된 데이터 확인 ===")
    for currency_name in currencies.values():
        collection = db[currency_name]
        count = collection.count_documents({})
        print(f"{currency_name} 컬렉션: {count}개 문서")

# 특정 통화의 최신 데이터 조회 함수
def get_latest_rates():
    """모든 통화의 최신 환율 조회"""
    print("\n=== 최신 환율 정보 ===")
    
    for currency_name in currencies.values():
        collection = db[currency_name]
        latest = collection.find().sort("date", -1).limit(1)
        
        for doc in latest:
            print(f"{currency_name}: {doc['rate']:.2f}원 ({doc['date'].strftime('%Y-%m-%d')})")

if __name__ == "__main__":
    # 메인 실행
    main()
    
    # 최신 환율 확인
    get_latest_rates()
    
    # 연결 종료
    client.close()
