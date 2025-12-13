# daily_update/commodities_cron.py
"""
원자재/지수 일일 업데이트 (최근 5일)
"""
import sys
sys.path.append('..')

import yfinance as yf
from datetime import datetime, timedelta
from common import (
    get_mongo_client, get_collection, save_records, create_date_index,
    COMMODITIES_INDICES, safe_clean_value, print_summary
)


def main():
    """메인 실행"""
    print(f"=== 원자재/지수 일일 업데이트 시작 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ===")
    
    today = datetime.now()
    start_date = (today - timedelta(days=5)).strftime('%Y-%m-%d')
    end_date = today.strftime('%Y-%m-%d')
    
    client = get_mongo_client()
    total_new = 0
    
    for name, ticker in COMMODITIES_INDICES.items():
        try:
            print(f"\n--- {name} 최신 데이터 확인 중 ---")
            
            data = yf.download(ticker, start=start_date, end=end_date,
                             auto_adjust=True, progress=False)
            
            if not data.empty:
                df = data.reset_index()
                collection = get_collection(client, name)
                create_date_index(collection, [("date", 1)])
                
                records = []
                for _, row in df.iterrows():
                    record = {
                        'date': safe_clean_value(row['Date']),
                        'open': safe_clean_value(row['Open']),
                        'high': safe_clean_value(row['High']),
                        'low': safe_clean_value(row['Low']),
                        'close': safe_clean_value(row['Close']),
                        'volume': safe_clean_value(row['Volume']),
                        'price': safe_clean_value(row['Close']),
                        'created_at': datetime.now()
                    }
                    records.append(record)
                
                inserted, updated = save_records(
                    collection,
                    records,
                    unique_fields=["date"],
                    verbose=False
                )
                
                total_new += inserted
                
                if inserted > 0:
                    latest_value = safe_clean_value(df.iloc[-1]['Close'])
                    latest_date = safe_clean_value(df.iloc[-1]['Date'])
                    print_summary(name, inserted, updated, latest_value, latest_date)
                else:
                    print(f"{name}: 변경사항 없음")
            else:
                print(f"{name}: 새로운 데이터 없음")
                
        except Exception as e:
            print(f"{name} 오류: {e}")
    
    print(f"\n=== 업데이트 완료 - 총 신규: {total_new}개 ===")
    client.close()


if __name__ == "__main__":
    main()