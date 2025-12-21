# daily_update/exchange_cron.py
"""
환율 일일 업데이트
- 수정사항: 최근 5일 고정 -> DB 마지막 저장일 기준 자동 증분 업데이트
"""
import sys
sys.path.append('..')

import requests
import pandas as pd
from datetime import datetime, timedelta
import time
from common import (
    get_mongo_client, get_collection, save_records, create_date_index,
    BOK_API_KEY, CURRENCY_CODES, print_summary, get_latest_record
)


def get_exchange_rates_by_period(currency_code, start_date, end_date):
    """지정된 기간의 환율 데이터 조회"""
    stat_code = "731Y001"
    
    url = f"https://ecos.bok.or.kr/api/StatisticSearch/{BOK_API_KEY}/json/kr/1/1000/{stat_code}/D/{start_date}/{end_date}/{currency_code}"
    
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
    today = datetime.now()
    
    for currency_code, currency_name in CURRENCY_CODES.items():
        print(f"\n--- {currency_name} 최신 데이터 확인 중 ---")
        
        collection = get_collection(client, currency_name)
        create_date_index(collection, [("date", 1), ("currency_code", 1)])
        
        # 1. DB에서 마지막 날짜 확인
        latest_doc = get_latest_record(collection)
        
        if latest_doc:
            last_date = latest_doc['date']
            start_dt = last_date + timedelta(days=1)
            
            if start_dt.date() > today.date():
                print(f"{currency_name}: 이미 최신 데이터임 ({last_date.strftime('%Y-%m-%d')})")
                continue
                
            start_date_str = start_dt.strftime('%Y%m%d')
        else:
            # 데이터 없으면 1년치
            start_date_str = (today - timedelta(days=365)).strftime('%Y%m%d')
            print(f"{currency_name}: 초기 데이터 수집")
            
        end_date_str = today.strftime('%Y%m%d')
        print(f"조회 기간: {start_date_str} ~ {end_date_str}")
        
        time.sleep(0.5)
        
        # 2. 데이터 조회 및 저장
        df = get_exchange_rates_by_period(currency_code, start_date_str, end_date_str)
        
        if not df.empty:
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
                print(f"{currency_name}: 기간 내 새로운 데이터 없음 (휴장일 등)")
        else:
            print(f"{currency_name}: 새로운 데이터 없음")
    
    print(f"\n=== 업데이트 완료 - 총 신규: {total_new}개 ===")
    client.close()


if __name__ == "__main__":
    main()