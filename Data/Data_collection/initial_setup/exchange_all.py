# initial_setup/exchange_all.py
"""
환율 데이터 전체 수집 (2010년~현재)
"""
import sys
sys.path.append('..')

import requests
import pandas as pd
from datetime import datetime
import time
from common import (
    get_mongo_client, get_collection, save_records, create_date_index,
    BOK_API_KEY, CURRENCY_CODES, get_collection_stats
)


def get_exchange_rate_batch(currency_code, start_date, end_date):
    """환율 데이터 배치 조회"""
    stat_code = "731Y001"
    url = f"https://ecos.bok.or.kr/api/StatisticSearch/{BOK_API_KEY}/json/kr/1/10000/{stat_code}/D/{start_date}/{end_date}/{currency_code}"
    
    try:
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'StatisticSearch' in data and 'row' in data['StatisticSearch']:
                rows = data['StatisticSearch']['row']
                df = pd.DataFrame(rows)
                
                # 데이터 변환
                df['date'] = pd.to_datetime(df['TIME'], format='%Y%m%d')
                df['rate'] = df['DATA_VALUE'].astype(float)
                df['currency_code'] = currency_code
                df['unit_name'] = df['UNIT_NAME']
                df['created_at'] = datetime.now()
                
                return df[['date', 'rate', 'currency_code', 'unit_name', 'created_at']]
            else:
                print(f"데이터 없음 - 통화코드: {currency_code}")
                return pd.DataFrame()
        else:
            print(f"API 오류 {response.status_code}")
            return pd.DataFrame()
            
    except Exception as e:
        print(f"오류 - 통화코드 {currency_code}: {e}")
        return pd.DataFrame()


def main():
    """메인 실행"""
    print("=== 환율 데이터 전체 수집 시작 ===")
    
    start_date = "20100101"
    today = datetime.now().strftime('%Y%m%d')
    print(f"수집 기간: {start_date} ~ {today}")
    
    client = get_mongo_client()
    
    for currency_code, currency_name in CURRENCY_CODES.items():
        print(f"\n--- {currency_name} 환율 데이터 수집 중 ---")
        
        time.sleep(1)  # API 제한 고려
        
        df = get_exchange_rate_batch(currency_code, start_date, today)
        
        if not df.empty:
            print(f"{currency_name}: {len(df)}개 데이터 조회 완료")
            
            # MongoDB 저장
            collection = get_collection(client, currency_name)
            create_date_index(collection, [("date", 1), ("currency_code", 1)])
            
            records = df.to_dict('records')
            inserted, updated = save_records(
                collection, 
                records, 
                unique_fields=["date", "currency_code"]
            )
            
            print(f"{currency_name}: 신규 {inserted}개, 업데이트 {updated}개")
            
            # 최신 데이터
            latest = df.iloc[-1]
            print(f"최신 환율: {latest['rate']:.2f}원 ({latest['date'].strftime('%Y-%m-%d')})")
        else:
            print(f"{currency_name}: 조회 실패")
    
    print("\n=== 전체 수집 완료 ===")
    
    # 통계 출력
    print("\n=== 저장된 데이터 확인 ===")
    for currency_name in CURRENCY_CODES.values():
        stats = get_collection_stats(client, currency_name)
        print(f"{currency_name}: {stats['total_count']:,}개")
    
    client.close()


if __name__ == "__main__":
    main()