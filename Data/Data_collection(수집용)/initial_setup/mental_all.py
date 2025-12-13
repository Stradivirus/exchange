# initial_setup/mental_all.py
"""
심리지수 데이터 전체 수집 (2010년~현재)
- 소비자심리지수 (월별)
- 경제심리지수 (월별)
- 뉴스심리지수 (일별)
"""
import sys
sys.path.append('..')

import requests
import pandas as pd
from datetime import datetime
import time
from common import (
    get_mongo_client, get_collection, save_records, create_date_index,
    BOK_API_KEY, SENTIMENT_INDICATORS, get_collection_stats
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
                
                # 날짜 포맷 처리
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
                
                # 소비자심리지수의 경우 지역 정보 추가
                if stat_code == "511Y004":
                    df['region_code'] = df['ITEM_CODE2']
                    df['region_name'] = df['ITEM_NAME2']
                    return df[['date', 'value', 'stat_code', 'item_code', 'item_name', 
                             'unit_name', 'region_code', 'region_name', 'created_at']]
                
                return df[['date', 'value', 'stat_code', 'item_code', 'item_name', 
                         'unit_name', 'created_at']]
            else:
                print(f"데이터 없음 - {stat_code}:{item_code}")
                return pd.DataFrame()
        else:
            print(f"API 오류 {response.status_code}")
            return pd.DataFrame()
            
    except Exception as e:
        print(f"오류 - {stat_code}: {e}")
        return pd.DataFrame()


def main():
    """메인 실행"""
    print("=== 심리지수 데이터 전체 수집 시작 ===")
    
    client = get_mongo_client()
    
    for stat_code, config in SENTIMENT_INDICATORS.items():
        print(f"\n--- {config['indicator_name']} 데이터 수집 중 ---")
        
        # 날짜 설정
        if config['period'] == "D":
            start_date = "20100101"
            today = datetime.now().strftime('%Y%m%d')
        else:
            start_date = "201001"
            today = datetime.now().strftime('%Y%m')
        
        print(f"수집 기간: {start_date} ~ {today}")
        
        time.sleep(1)  # API 제한 고려
        
        for item_code in config['item_codes']:
            print(f"항목코드 {item_code} 수집 중...")
            
            df = get_sentiment_data(
                stat_code, 
                item_code, 
                start_date, 
                today, 
                config['period']
            )
            
            if not df.empty:
                print(f"{config['indicator_name']}: {len(df)}개 데이터 조회 완료")
                
                # MongoDB 저장
                collection = get_collection(client, config['collection_name'])
                create_date_index(collection, [("date", 1), ("item_code", 1)])
                
                records = df.to_dict('records')
                inserted, updated = save_records(
                    collection,
                    records,
                    unique_fields=["date", "item_code"]
                )
                
                print(f"{config['indicator_name']}: 신규 {inserted}개, 업데이트 {updated}개")
                
                # 기본 통계
                print(f"기본 통계:")
                print(f"  최소값: {df['value'].min():.2f}")
                print(f"  최대값: {df['value'].max():.2f}")
                print(f"  평균값: {df['value'].mean():.2f}")
                
                # 최신 데이터
                latest = df.iloc[-1]
                date_format = '%Y-%m-%d' if config['period'] == 'D' else '%Y-%m'
                print(f"최신값: {latest['value']:.2f} ({latest['date'].strftime(date_format)})")
            else:
                print(f"{config['indicator_name']}: 조회 실패")
            
            time.sleep(0.5)
    
    print("\n=== 전체 수집 완료 ===")
    
    # 통계 출력
    print("\n=== 저장된 데이터 확인 ===")
    for config in SENTIMENT_INDICATORS.values():
        stats = get_collection_stats(client, config['collection_name'])
        print(f"{config['collection_name']}: {stats['total_count']:,}개")
    
    client.close()


if __name__ == "__main__":
    main()