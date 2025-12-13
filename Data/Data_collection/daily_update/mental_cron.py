# daily_update/mental_cron.py
"""
심리지수 일일 업데이트
- 소비자심리지수 (월별 - 최근 1개월)
- 경제심리지수 (월별 - 최근 1개월)
- 뉴스심리지수 (일별 - 최근 7일)
"""
import sys
sys.path.append('..')

import requests
import pandas as pd
from datetime import datetime
import time
from common import (
    get_mongo_client, get_collection, create_date_index,
    BOK_API_KEY, SENTIMENT_INDICATORS,
    get_recent_date_range, get_recent_month_range
)


def get_sentiment_data(stat_code, item_code, start_date, end_date, period="M"):
    """심리지수 데이터 조회"""
    url = f"https://ecos.bok.or.kr/api/StatisticSearch/{BOK_API_KEY}/json/kr/1/10000/{stat_code}/{period}/{start_date}/{end_date}/{item_code}"
    
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
                    return df[['date', 'value', 'stat_code', 'item_code', 'item_name',
                             'unit_name', 'region_code', 'region_name', 'created_at']]
                
                return df[['date', 'value', 'stat_code', 'item_code', 'item_name',
                         'unit_name', 'created_at']]
            else:
                return pd.DataFrame()
        else:
            print(f"API 오류 {response.status_code}")
            return pd.DataFrame()
            
    except Exception as e:
        print(f"오류 - {stat_code}: {e}")
        return pd.DataFrame()


def main():
    """메인 실행"""
    print("=== 심리지수 일일 업데이트 시작 ===")
    
    client = get_mongo_client()
    
    for stat_code, config in SENTIMENT_INDICATORS.items():
        print(f"\n--- {config['indicator_name']} 데이터 수집 중 ---")
        
        # 날짜 범위 계산
        if config['period'] == "D":
            start_date, end_date = get_recent_date_range(days_back=6)
        else:
            start_date, end_date = get_recent_month_range(months_back=1)
        
        print(f"최근 기간: {start_date} ~ {end_date}")
        
        time.sleep(1)
        
        for item_code in config['item_codes']:
            print(f"항목코드 {item_code} 수집 중...")
            
            df = get_sentiment_data(
                stat_code,
                item_code,
                start_date,
                end_date,
                config['period']
            )
            
            if not df.empty:
                print(f"{config['indicator_name']}: {len(df)}개 데이터 조회 완료")
                
                collection = get_collection(client, config['collection_name'])
                create_date_index(collection, [("date", 1), ("item_code", 1)])
                
                inserted_count = 0
                for _, row in df.iterrows():
                    record = row.to_dict()
                    
                    # 중복 체크
                    exists = collection.find_one({
                        "date": record['date'],
                        "item_code": record['item_code']
                    })
                    
                    if not exists:
                        collection.insert_one(record)
                        inserted_count += 1
                
                if inserted_count > 0:
                    print(f"{config['indicator_name']}: 신규 {inserted_count}개 저장")
                else:
                    print(f"{config['indicator_name']}: 변경사항 없음")
            else:
                print(f"{config['indicator_name']}: 조회된 데이터 없음")
            
            time.sleep(0.5)
    
    print("\n=== 심리지수 업데이트 완료 ===")
    client.close()


if __name__ == "__main__":
    main()