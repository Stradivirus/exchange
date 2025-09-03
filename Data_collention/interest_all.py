# /home/exchange/interest_full.py

import requests
from fredapi import Fred
import pandas as pd
from datetime import datetime
from pymongo import MongoClient
import time

def collect_korea_us_rates_full():
    """한국 + 미국 기준금리 전체 데이터 수집"""
    print("=== 한국 + 미국 기준금리 전체 데이터 수집 시작 ===")
    
    client = MongoClient("mongodb+srv://stradivarius:1q2w3e4r6218@cluster0.e7rvfpz.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
    db = client['exchange_all']
    
    # API 키 설정
    bok_api_key = "GYMU5SDZ3BMQ9GWY2JAF"
    fred_api_key = "be3c10f05ec901151d380553080f640e"
    
    # ========== 1. 한국 기준금리 수집 ==========
    print("\n--- 한국 기준금리 데이터 수집 중 ---")
    
    try:
        start_date = "20000101"
        today = datetime.now().strftime('%Y%m%d')
        print(f"기간: {start_date} ~ {today}")
        
        url = f"https://ecos.bok.or.kr/api/StatisticSearch/{bok_api_key}/json/kr/1/10000/722Y001/D/{start_date}/{today}/0101000"
        response = requests.get(url, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'StatisticSearch' in data and 'row' in data['StatisticSearch']:
                rows = data['StatisticSearch']['row']
                df = pd.DataFrame(rows)
                print(f"한국 기준금리: {len(rows)}개 원시 데이터 조회됨")
                
                # 데이터 변환
                df['date'] = pd.to_datetime(df['TIME'], format='%Y%m%d')
                df['rate'] = df['DATA_VALUE'].astype(float)
                
                # 변동된 날짜만 필터링
                df = df.sort_values('date')
                df['prev_rate'] = df['rate'].shift(1)
                changed_dates_df = df[(df['prev_rate'].isna()) | (df['rate'] != df['prev_rate'])]
                
                print(f"한국 기준금리: 변동 날짜만 {len(changed_dates_df)}개 필터링됨")
                
                # MongoDB에 저장
                collection = db['KOR_BASE_RATE']
                collection.create_index([("date", 1)], unique=True)
                
                inserted_count = 0
                updated_count = 0
                for _, row in changed_dates_df.iterrows():
                    record = {
                        'date': row['date'].to_pydatetime(),
                        'rate': row['rate'],
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
                    elif result.modified_count > 0:
                        updated_count += 1
                
                print(f"한국 기준금리: 신규 {inserted_count}개, 업데이트 {updated_count}개 저장 완료")
                
                # 최근 변동 이력
                print("한국 기준금리 최근 5회 변동:")
                for _, hist in changed_dates_df.tail(5).iterrows():
                    print(f"  {hist['date'].strftime('%Y-%m-%d')}: {hist['rate']:.2f}%")
                    
            else:
                print("한국 기준금리: 데이터가 없습니다")
        else:
            print(f"한국 기준금리: API 오류 {response.status_code}")
            
    except Exception as e:
        print(f"한국 기준금리 오류: {e}")
    
    # 5초 대기
    time.sleep(5)
    
    # ========== 2. 미국 연방기금금리 수집 ==========
    print("\n--- 미국 연방기금금리 데이터 수집 중 ---")
    
    try:
        # FRED API 초기화
        fred = Fred(api_key=fred_api_key)
        
        # 연방기금금리 데이터 조회 (2000년부터)
        fed_rate_data = fred.get_series('FEDFUNDS', start='2000-01-01')
        
        if not fed_rate_data.empty:
            print(f"미국 연방기금금리: {len(fed_rate_data)}개 원시 데이터 조회됨")
            
            # DataFrame으로 변환
            df = fed_rate_data.reset_index()
            df.columns = ['date', 'rate']
            df['date'] = pd.to_datetime(df['date'])
            
            # 변동된 날짜만 필터링
            df = df.sort_values('date')
            df['prev_rate'] = df['rate'].shift(1)
            changed_dates_df = df[(df['prev_rate'].isna()) | (df['rate'] != df['prev_rate'])]
            
            print(f"미국 연방기금금리: 변동 날짜만 {len(changed_dates_df)}개 필터링됨")
            
            # 기존 데이터 삭제 후 새로 저장
            collection = db['US_FED_RATE']
            collection.drop()  # 기존 데이터 삭제
            collection.create_index([("date", 1)], unique=True)
            
            # MongoDB에 저장
            inserted_count = 0
            for _, row in changed_dates_df.iterrows():
                record = {
                    'date': row['date'].to_pydatetime(),
                    'rate': float(row['rate']),
                    'type': 'fed_funds_rate',
                    'country': 'USA',
                    'source': 'FRED_API',
                    'series_id': 'FEDFUNDS',
                    'created_at': datetime.now()
                }
                
                collection.insert_one(record)
                inserted_count += 1
            
            print(f"미국 연방기금금리: 신규 {inserted_count}개 저장 완료")
            
            # 최신 금리 확인
            latest = changed_dates_df.iloc[-1]
            print(f"최신 미국 연방기금금리: {latest['rate']:.2f}% ({latest['date'].strftime('%Y-%m-%d')})")
            
            # 최근 변동 이력
            print("미국 연방기금금리 최근 5회 변동:")
            for _, hist in changed_dates_df.tail(5).iterrows():
                print(f"  {hist['date'].strftime('%Y-%m-%d')}: {hist['rate']:.2f}%")
                
        else:
            print("미국 연방기금금리: 데이터 조회 실패")
            
    except Exception as e:
        print(f"미국 연방기금금리 오류: {e}")
    
    # 최종 확인
    print("\n=== 저장된 기준금리 데이터 확인 ===")
    for rate_name in ["KOR_BASE_RATE", "US_FED_RATE"]:
        collection = db[rate_name]
        count = collection.count_documents({})
        print(f"{rate_name} 컬렉션: {count:,}개 문서")
    
    client.close()
    print("\n=== 한국 + 미국 기준금리 데이터 수집 완료 ===")

if __name__ == "__main__":
    collect_korea_us_rates_full()
