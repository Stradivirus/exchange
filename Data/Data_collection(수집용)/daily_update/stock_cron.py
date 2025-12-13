# daily_update/stock_cron.py
"""
주가지수 일일 업데이트 (최근 5일)
"""
import sys
sys.path.append('..')

import yfinance as yf
from datetime import datetime, timedelta
from common import (
    get_mongo_client, get_collection, create_date_index,
    STOCK_INDICES, safe_clean_value, print_summary
)


def main():
    """메인 실행"""
    print(f"=== 주가지수 일일 업데이트 시작 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ===")
    
    today = datetime.now()
    start_date = (today - timedelta(days=5)).strftime('%Y-%m-%d')
    end_date = today.strftime('%Y-%m-%d')
    
    client = get_mongo_client()
    total_new = 0
    
    for name, ticker in STOCK_INDICES.items():
        try:
            print(f"\n--- {name} 최신 데이터 확인 중 ---")
            
            data = yf.download(ticker, start=start_date, end=end_date,
                             auto_adjust=True, progress=False)
            
            if not data.empty:
                df = data.reset_index()
                collection = get_collection(client, name)
                create_date_index(collection, [("date", 1)])
                
                inserted_count = 0
                updated_count = 0
                
                for _, row in df.iterrows():
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
                        # 주요 값이 바뀐 경우에만 update
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
                print(f"{name}: 새로운 데이터 없음")
                
        except Exception as e:
            print(f"{name} 오류: {e}")
    
    print(f"\n=== 업데이트 완료 - 총 신규: {total_new}개 ===")
    client.close()


if __name__ == "__main__":
    main()