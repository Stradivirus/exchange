import os
from dotenv import load_dotenv
from pymongo import MongoClient
import requests
import pandas as pd
from datetime import datetime, timedelta
import time

# 환경변수 로드
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))
mongo_uri = os.getenv('MONGODB_URI')
mongo_db = os.getenv('MONGODB_DB', 'exchange_all')
api_key = os.getenv('BOK_API_KEY')
stat_code = "731Y001"
client = MongoClient(mongo_uri)
db = client[mongo_db]

currencies = {
    "0000001": "USD",
    "0000002": "JPY", 
    "0000053": "CNY",
    "0000003": "EUR"
}

def get_recent_exchange_rates(currency_code, days_back=5):
    """최근 며칠간의 환율 데이터만 조회 (크론용)"""
    today = datetime.now()
    start_date = (today - timedelta(days=days_back)).strftime('%Y%m%d')
    end_date = today.strftime('%Y%m%d')
    
    url = f"https://ecos.bok.or.kr/api/StatisticSearch/{api_key}/json/kr/1/100/{stat_code}/D/{start_date}/{end_date}/{currency_code}"
    
    try:
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'StatisticSearch' in data and 'row' in data['StatisticSearch']:
                rows = data['StatisticSearch']['row']
                df = pd.DataFrame(rows)
                
                df['date'] = pd.to_datetime(df['TIME'], format='%Y%m%d')
                df['rate'] = df['DATA_VALUE'].astype(float)
                df['currency_code'] = currency_code
                df['unit_name'] = df['UNIT_NAME']
                df['created_at'] = datetime.now()
                
                return df[['date', 'rate', 'currency_code', 'unit_name', 'created_at']]
            else:
                print(f"최근 데이터가 없습니다 - 통화코드: {currency_code}")
                return pd.DataFrame()
        else:
            print(f"API 오류 {response.status_code} - 통화코드: {currency_code}")
            return pd.DataFrame()
            
    except Exception as e:
        print(f"오류 발생 - 통화코드 {currency_code}: {e}")
        return pd.DataFrame()

def daily_update():
    """매일 실행할 업데이트 함수"""
    print(f"=== 환율 데이터 일일 업데이트 시작 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ===")
    
    total_new = 0
    total_updated = 0
    
    for currency_code, currency_name in currencies.items():
        print(f"\n--- {currency_name} 최신 데이터 확인 중 ---")
        
        # API 호출 제한 고려
        time.sleep(1)
        
        # 최근 5일 데이터 조회 (주말, 공휴일 고려)
        df = get_recent_exchange_rates(currency_code, days_back=5)
        
        if not df.empty:
            collection = db[currency_name]
            
            # 인덱스 생성 (한 번만 실행됨)
            collection.create_index([("date", 1), ("currency_code", 1)], unique=True)
            
            inserted_count = 0
            updated_count = 0
            
            for _, record in df.iterrows():
                try:
                    result = collection.replace_one(
                        {"date": record['date'], "currency_code": record['currency_code']},
                        record.to_dict(),
                        upsert=True
                    )
                    
                    if result.upserted_id:
                        inserted_count += 1
                    elif result.modified_count > 0:
                        updated_count += 1
                        
                except Exception as e:
                    print(f"저장 오류 - {currency_name}: {e}")
            
            total_new += inserted_count
            total_updated += updated_count
            
            if inserted_count > 0 or updated_count > 0:
                print(f"{currency_name}: 신규 {inserted_count}개, 업데이트 {updated_count}개")
                
                # 최신 데이터 출력
                latest_rate = df.iloc[-1]
                print(f"{currency_name} 최신 환율: {latest_rate['rate']:.2f}원 ({latest_rate['date'].strftime('%Y-%m-%d')})")
            else:
                print(f"{currency_name}: 변경사항 없음")
        else:
            print(f"{currency_name}: 새로운 데이터 없음")
    
    print(f"\n=== 업데이트 완료 - 총 신규: {total_new}개, 업데이트: {total_updated}개 ===")
    
    # 연결 종료
    client.close()

if __name__ == "__main__":
    daily_update()
