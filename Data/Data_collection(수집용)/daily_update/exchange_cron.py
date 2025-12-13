# daily_update/exchange_cron.py
"""
환율 일일 업데이트 (최근 5일)
"""
import sys
sys.path.append('..')

import requests
import pandas as pd
from datetime import datetime
import time
from common import (
    get_mongo_client, get_collection, save_records, create_date_index,
    BOK_API_KEY, CURRENCY_CODES, get_recent_date_range, print_summary
)


def get_recent_exchange_rates(currency_code):
    """최근 환율 데이터 조회"""
    start_date, end_date = get_recent_date_range(days_back=5)
    stat_code = "731Y001"
    
    url = f"https://ecos.bok.or.kr/api/StatisticSearch/{BOK_API_KEY}/json/kr/1/100/{stat_code}/D/{start_date}/{end_date}/{currency_code}"
    
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
                return pd.DataFrame()
        else:
            print(f"API 오류 {response.status_code}")
            return pd.DataFrame()
            
    except Exception as e:
        print(f"오류 - {currency_code}: {e}")
        return pd.DataFrame()


def main():
    """메인 실행"""
    print(f"=== 환율 일일 업데이트 시작 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ===")
    
    client = get_mongo_client()
    total_new = 0
    
    for currency_code, currency_name in CURRENCY_CODES.items():
        print(f"\n--- {currency_name} 최신 데이터 확인 중 ---")
        
        time.sleep(1)
        
        df = get_recent_exchange_rates(currency_code)
        
        if not df.empty:
            collection = get_collection(client, currency_name)
            create_date_index(collection, [("date", 1), ("currency_code", 1)])
            
            records = df.to_dict('records')
            inserted, updated = save_records(
                collection,
                records,
                unique_fields=["date", "currency_code"],
                verbose=False
            )
            
            total_new += inserted
            
            if inserted > 0:
                latest = df.iloc[-1]
                print_summary(
                    currency_name,
                    inserted,
                    updated,
                    latest['rate'],
                    latest['date']
                )
            else:
                print(f"{currency_name}: 변경사항 없음")
        else:
            print(f"{currency_name}: 새로운 데이터 없음")
    
    print(f"\n=== 업데이트 완료 - 총 신규: {total_new}개 ===")
    client.close()


if __name__ == "__main__":
    main()