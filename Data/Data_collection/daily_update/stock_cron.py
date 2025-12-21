# daily_update/stock_cron.py
"""
주가지수 일일 업데이트 (FinanceDataReader 적용)
"""
import sys
sys.path.append('..')

import FinanceDataReader as fdr
import pandas as pd
from datetime import datetime, timedelta
from common import (
    get_mongo_client, get_collection, create_date_index,
    STOCK_INDICES, safe_clean_value, print_summary, get_latest_record
)

# FDR용 심볼 매핑 (Yahoo -> FDR/Naver)
FDR_TICKERS = {
    "KOSPI": "KS11",
    "KOSDAQ": "KQ11",
    "DOW_JONES": "DJI",
    "NASDAQ": "IXIC",
    "SP500": "US500"
}

def main():
    print(f"=== 주가지수 업데이트 (FDR) 시작 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ===")
    
    client = get_mongo_client()
    total_new = 0
    today = datetime.now()
    
    for name, _ in STOCK_INDICES.items(): # 기존 ticker 무시하고 FDR_TICKERS 사용
        fdr_symbol = FDR_TICKERS.get(name)
        if not fdr_symbol:
            continue

        try:
            collection = get_collection(client, name)
            
            # 1. DB에서 마지막 날짜 확인
            latest_doc = get_latest_record(collection)
            
            if latest_doc:
                last_date = latest_doc['date']
                start_dt = last_date + timedelta(days=1)
                
                # 이미 최신이면 스킵
                if start_dt.date() > today.date():
                    print(f"--- {name}: 이미 최신 데이터 ({last_date.strftime('%Y-%m-%d')}) ---")
                    continue
                
                start_date_str = start_dt.strftime('%Y-%m-%d')
            else:
                start_date_str = (today - timedelta(days=365)).strftime('%Y-%m-%d')
                print(f"--- {name}: 초기 데이터 수집 ---")

            print(f"\n--- {name} ({fdr_symbol}) 조회: {start_date_str} ~ ---")
            
            # 2. FDR로 데이터 수집 (start만 넣으면 오늘까지 다 가져옴)
            df = fdr.DataReader(fdr_symbol, start=start_date_str)
            
            if not df.empty:
                df = df.reset_index() # Date 컬럼 생성
                create_date_index(collection, [("date", 1)])
                
                inserted_count = 0
                updated_count = 0
                
                for _, row in df.iterrows():
                    # 컬럼명 소문자 통일 및 매핑
                    # FDR 컬럼: Date, Open, High, Low, Close, Volume, Change 등
                    record = {
                        'date': safe_clean_value(row['Date']),
                        'open': safe_clean_value(row['Open']),
                        'high': safe_clean_value(row['High']),
                        'low': safe_clean_value(row['Low']),
                        'close': safe_clean_value(row['Close']),
                        'volume': safe_clean_value(row['Volume']),
                        'created_at': datetime.now()
                    }
                    
                    query = {"date": record['date']}
                    existing = collection.find_one(query)
                    
                    if not existing:
                        collection.insert_one(record)
                        inserted_count += 1
                    else:
                        if any(record[k] != existing.get(k) for k in ['open', 'high', 'low', 'close', 'volume']):
                            collection.replace_one(query, record, upsert=True)
                            updated_count += 1
                
                total_new += inserted_count + updated_count
                
                if inserted_count > 0 or updated_count > 0:
                    latest_value = safe_clean_value(df.iloc[-1]['Close'])
                    latest_date = safe_clean_value(df.iloc[-1]['Date'])
                    print_summary(name, inserted_count, updated_count, latest_value, latest_date)
                else:
                    print(f"{name}: 변경사항 없음")
            else:
                print(f"{name}: 새로운 데이터 없음 (휴장일 가능성)")
                
        except Exception as e:
            print(f"{name} 오류: {e}")

    print(f"\n=== 업데이트 완료 - 총 신규: {total_new}개 ===")
    client.close()

if __name__ == "__main__":
    main()