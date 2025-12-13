# initial_setup/interest_all.py
"""
한국 + 미국 기준금리 전체 데이터 수집 (2010년~현재)
"""
import sys
sys.path.append('..')

import requests
from fredapi import Fred
import pandas as pd
from datetime import datetime
import time
from common import (
    get_mongo_client, get_collection, save_records, create_date_index,
    BOK_API_KEY, FRED_API_KEY, INTEREST_RATE_CONFIG,
    filter_changed_values, get_collection_stats
)


def collect_korea_rates():
    """한국 기준금리 수집"""
    print("\n--- 한국 기준금리 데이터 수집 중 ---")
    
    config = INTEREST_RATE_CONFIG['korea']
    
    try:
        start_date = "20100101"
        today = datetime.now().strftime('%Y%m%d')
        
        url = f"https://ecos.bok.or.kr/api/StatisticSearch/{BOK_API_KEY}/json/kr/1/10000/{config['stat_code']}/D/{start_date}/{today}/{config['item_code']}"
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
                df = filter_changed_values(df, 'rate')
                
                print(f"변동 날짜만 {len(df)}개 필터링됨")
                
                # 레코드 생성
                records = []
                for _, row in df.iterrows():
                    record = {
                        'date': row['date'].to_pydatetime(),
                        'rate': row['rate'],
                        'type': 'base_rate',
                        'country': 'Korea',
                        'source': 'BOK_ECOS',
                        'created_at': datetime.now()
                    }
                    records.append(record)
                
                return records, df
            else:
                print("한국 기준금리: 데이터 없음")
                return [], pd.DataFrame()
        else:
            print(f"한국 기준금리: API 오류 {response.status_code}")
            return [], pd.DataFrame()
            
    except Exception as e:
        print(f"한국 기준금리 오류: {e}")
        return [], pd.DataFrame()


def collect_us_rates():
    """미국 연방기금금리 수집"""
    print("\n--- 미국 연방기금금리 데이터 수집 중 ---")
    
    config = INTEREST_RATE_CONFIG['usa']
    
    try:
        fred = Fred(api_key=FRED_API_KEY)
        fed_rate_data = fred.get_series(config['series_id'], start='2010-01-01')
        
        if not fed_rate_data.empty:
            print(f"미국 연방기금금리: {len(fed_rate_data)}개 원시 데이터 조회됨")
            
            # DataFrame 변환
            df = fed_rate_data.reset_index()
            df.columns = ['date', 'rate']
            df['date'] = pd.to_datetime(df['date'])
            
            # 변동된 날짜만 필터링
            df = filter_changed_values(df, 'rate')
            
            print(f"변동 날짜만 {len(df)}개 필터링됨")
            
            # 레코드 생성
            records = []
            for _, row in df.iterrows():
                record = {
                    'date': row['date'].to_pydatetime(),
                    'rate': float(row['rate']),
                    'type': 'fed_funds_rate',
                    'country': 'USA',
                    'source': 'FRED_API',
                    'series_id': config['series_id'],
                    'created_at': datetime.now()
                }
                records.append(record)
            
            return records, df
        else:
            print("미국 연방기금금리: 데이터 없음")
            return [], pd.DataFrame()
            
    except Exception as e:
        print(f"미국 연방기금금리 오류: {e}")
        return [], pd.DataFrame()


def main():
    """메인 실행"""
    print("=== 한국 + 미국 기준금리 전체 데이터 수집 시작 ===")
    
    client = get_mongo_client()
    
    # 한국 기준금리
    korea_records, korea_df = collect_korea_rates()
    if korea_records:
        config = INTEREST_RATE_CONFIG['korea']
        collection = get_collection(client, config['collection_name'])
        create_date_index(collection, [("date", 1)])
        
        inserted, updated = save_records(
            collection, 
            korea_records, 
            unique_fields=["date"]
        )
        
        print(f"한국 기준금리: 신규 {inserted}개, 업데이트 {updated}개")
        
        # 최근 변동 이력
        print("최근 5회 변동:")
        for _, row in korea_df.tail(5).iterrows():
            print(f"  {row['date'].strftime('%Y-%m-%d')}: {row['rate']:.2f}%")
    
    time.sleep(5)  # API 제한 고려
    
    # 미국 연방기금금리
    us_records, us_df = collect_us_rates()
    if us_records:
        config = INTEREST_RATE_CONFIG['usa']
        collection = get_collection(client, config['collection_name'])
        
        # 기존 데이터 삭제 후 재저장
        collection.drop()
        create_date_index(collection, [("date", 1)])
        
        inserted, updated = save_records(
            collection, 
            us_records, 
            unique_fields=["date"]
        )
        
        print(f"미국 연방기금금리: 신규 {inserted}개 저장")
        
        # 최근 변동 이력
        print("최근 5회 변동:")
        for _, row in us_df.tail(5).iterrows():
            print(f"  {row['date'].strftime('%Y-%m-%d')}: {row['rate']:.2f}%")
    
    # 통계 출력
    print("\n=== 저장된 데이터 확인 ===")
    for rate_type in ['korea', 'usa']:
        collection_name = INTEREST_RATE_CONFIG[rate_type]['collection_name']
        stats = get_collection_stats(client, collection_name)
        print(f"{collection_name}: {stats['total_count']:,}개")
    
    client.close()
    print("\n=== 전체 수집 완료 ===")


if __name__ == "__main__":
    main()