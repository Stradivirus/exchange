# daily_update/stock_cron.py
"""
주가지수 일일 업데이트
- 수정사항: 최근 5일 고정 -> DB 마지막 저장일 기준 자동 증분 업데이트
"""
import sys
sys.path.append('..')

import yfinance as yf
from datetime import datetime, timedelta
# get_latest_record 추가 임포트
from common import (
    get_mongo_client, get_collection, create_date_index,
    STOCK_INDICES, safe_clean_value, print_summary,
    get_latest_record 
)


def main():
    """메인 실행"""
    print(f"=== 주가지수 일일 업데이트 시작 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ===")
    
    # 오늘 날짜 (검색 종료일은 내일로 설정해야 오늘 데이터까지 포함됨)
    today = datetime.now()
    next_day = today + timedelta(days=1)
    end_date_str = next_day.strftime('%Y-%m-%d')
    
    client = get_mongo_client()
    total_new = 0
    
    for name, ticker in STOCK_INDICES.items():
        try:
            collection = get_collection(client, name)
            
            # 1. DB에서 가장 최근 데이터 날짜 조회
            latest_doc = get_latest_record(collection, sort_field="date")
            
            if latest_doc and 'date' in latest_doc:
                # 마지막 저장일 다음날부터 조회
                last_date = latest_doc['date']
                if isinstance(last_date, str):
                    last_date = datetime.strptime(last_date, "%Y-%m-%d")
                
                start_dt = last_date + timedelta(days=1)
                start_date_str = start_dt.strftime('%Y-%m-%d')
                
                # 만약 시작일이 오늘보다 미래라면(이미 최신임) 스킵
                if start_dt.date() > today.date():
                    print(f"--- {name}: 이미 최신 데이터임 ({last_date.strftime('%Y-%m-%d')}) ---")
                    continue
            else:
                # 데이터가 아예 없으면 1년 전부터 조회 (초기화)
                start_date_str = (today - timedelta(days=365)).strftime('%Y-%m-%d')
                print(f"--- {name}: 초기 데이터(1년치) 수집 ---")

            print(f"\n--- {name} 데이터 확인 중 ({start_date_str} ~ {today.strftime('%Y-%m-%d')}) ---")
            
            # 2. yfinance로 데이터 다운로드 (종료일은 end_date_str까지)
            data = yf.download(ticker, start=start_date_str, end=end_date_str,
                             auto_adjust=True, progress=False)
            
            if not data.empty:
                df = data.reset_index()
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
            import traceback
            traceback.print_exc()
    
    print(f"\n=== 업데이트 완료 - 총 신규: {total_new}개 ===")
    client.close()


if __name__ == "__main__":
    main()