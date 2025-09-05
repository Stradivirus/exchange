# /home/exchange/interest_cron.py
import requests
from fredapi import Fred
from datetime import datetime, timedelta
from pymongo import MongoClient

def daily_korea_us_rates_update():
    """한국 + 미국 기준금리 일일 업데이트"""
    print(f"=== 한국 + 미국 기준금리 일일 업데이트 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ===")
    

    # 하드코딩 환경설정
    mongo_uri = "mongodb+srv://stradivirus:1q2w3e4r6218@cluster0.e7rvfpz.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    mongo_db = "exchange_all"
    bok_api_key = "GYMU5SDZ3BMQ9GWY2JAF"
    fred_api_key = "be3c10f05ec901151d380553080f640e"
    client = MongoClient(mongo_uri)
    db = client[mongo_db]
    
    total_new = 0
    
    # ========== 1. 한국 기준금리 체크 ==========
    print("\n--- 한국 기준금리 변동 체크 중 ---")
    
    try:
        # 최근 7일간만 확인
        today = datetime.now()
        start_date = (today - timedelta(days=7)).strftime('%Y%m%d')
        end_date = today.strftime('%Y%m%d')
        
        url = f"https://ecos.bok.or.kr/api/StatisticSearch/{bok_api_key}/json/kr/1/100/722Y001/D/{start_date}/{end_date}/0101000"
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'StatisticSearch' in data and 'row' in data['StatisticSearch']:
                rows = data['StatisticSearch']['row']
                
                # DB에서 최신 기준금리 조회
                collection = db['KOR_BASE_RATE']
                collection.create_index([("date", 1)], unique=True)
                
                latest_db_rate = collection.find().sort("date", -1).limit(1)
                latest_db_rate = list(latest_db_rate)
                prev_rate = latest_db_rate[0]['rate'] if latest_db_rate else None
                
                # 새로운 데이터에서 변동 확인
                inserted_count = 0
                for row in rows:
                    current_rate = float(row['DATA_VALUE'])
                    current_date = datetime.strptime(row['TIME'], '%Y%m%d')
                    
                    # 이전 금리와 다르면 저장
                    if prev_rate is None or current_rate != prev_rate:
                        record = {
                            'date': current_date,
                            'rate': current_rate,
                            'type': 'base_rate',
                            'country': 'Korea',
                            'source': 'BOK_ECOS',
                            'created_at': datetime.now()
                        }
                        
                        result = collection.replace_one(
                            {"date": record['date']},
                            record,
                            upsert=True
                        )
                        
                        if result.upserted_id:
                            inserted_count += 1
                            print(f"한국 기준금리 변동: {current_date.strftime('%Y-%m-%d')} {prev_rate}% → {current_rate}%")
                        
                        prev_rate = current_rate
                
                total_new += inserted_count
                
                if inserted_count > 0:
                    print(f"한국 기준금리: 신규 {inserted_count}개 저장")
                else:
                    print("한국 기준금리: 변경사항 없음")
                    
            else:
                print("한국 기준금리: 새로운 데이터 없음")
        else:
            print(f"한국 기준금리: API 오류 {response.status_code}")
            
    except Exception as e:
        print(f"한국 기준금리 오류: {e}")
    
    # ========== 2. 미국 연방기금금리 체크 ==========
    print("\n--- 미국 연방기금금리 변동 체크 중 ---")
    
    try:
        # FRED API 초기화
        fred = Fred(api_key=fred_api_key)
        
        # 최근 3개월 데이터만 조회
        start_date = (today - timedelta(days=90)).strftime('%Y-%m-%d')
        fed_rate_data = fred.get_series('FEDFUNDS', start=start_date)
        
        if not fed_rate_data.empty:
            # 최신 데이터만
            latest_fred_date = fed_rate_data.index[-1]
            latest_fred_rate = fed_rate_data.iloc[-1]
            
            # DB에서 최신 데이터 조회
            collection = db['US_FED_RATE']
            collection.create_index([("date", 1)], unique=True)
            
            latest_db = collection.find().sort("date", -1).limit(1)
            latest_db = list(latest_db)
            
            if latest_db:
                latest_db_date = latest_db[0]['date']
                latest_db_rate = latest_db[0]['rate']
                
                # 새로운 데이터가 있거나 금리가 변동된 경우
                if (latest_fred_date.to_pydatetime().date() > latest_db_date.date() or 
                    abs(latest_fred_rate - latest_db_rate) >= 0.01):
                    
                    record = {
                        'date': latest_fred_date.to_pydatetime(),
                        'rate': float(latest_fred_rate),
                        'type': 'fed_funds_rate',
                        'country': 'USA',
                        'source': 'FRED_API',
                        'series_id': 'FEDFUNDS',
                        'created_at': datetime.now()
                    }
                    
                    collection.replace_one(
                        {"date": record['date']},
                        record,
                        upsert=True
                    )
                    
                    total_new += 1
                    print(f"미국 연방기금금리 업데이트: {latest_fred_date.strftime('%Y-%m-%d')} {latest_fred_rate:.2f}%")
                else:
                    print("미국 연방기금금리: 변경사항 없음")
            else:
                # DB가 비어있으면 최신 데이터 저장
                record = {
                    'date': latest_fred_date.to_pydatetime(),
                    'rate': float(latest_fred_rate),
                    'type': 'fed_funds_rate',
                    'country': 'USA',
                    'source': 'FRED_API',
                    'series_id': 'FEDFUNDS',
                    'created_at': datetime.now()
                }
                
                collection.insert_one(record)
                total_new += 1
                print(f"미국 연방기금금리 신규 저장: {latest_fred_date.strftime('%Y-%m-%d')} {latest_fred_rate:.2f}%")
                
        else:
            print("미국 연방기금금리: 새로운 데이터 없음")
            
    except Exception as e:
        print(f"미국 연방기금금리 오류: {e}")
    
    print(f"\n=== 기준금리 업데이트 완료 - 총 신규: {total_new}개 ===")
    client.close()

if __name__ == "__main__":
    daily_korea_us_rates_update()
