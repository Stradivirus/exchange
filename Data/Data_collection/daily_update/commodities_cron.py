# daily_update/commodities_cron.py
"""
원자재/지수 일일 업데이트
- 수정사항: 최근 5일 고정 -> DB 마지막 저장일 기준 자동 증분 업데이트
"""
import sys
sys.path.append('..')

import yfinance as yf
from datetime import datetime, timedelta
from common import (
    get_mongo_client, get_collection, save_records, create_date_index,
    COMMODITIES_INDICES, safe_clean_value, print_summary,
    get_latest_record
)


def main():
    """메인 실행"""
    print(f"=== 원자재/지수 일일 업데이트 시작 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ===")
    
    # 오늘 날짜 (종료일은 내일로 설정하여 오늘 데이터 포함 보장)
    today = datetime.now()
    next_day = today + timedelta(days=1)
    end_date_str = next_day.strftime('%Y-%m-%d')
    
    client = get_mongo_client()
    total_new = 0
    
    for name, ticker in COMMODITIES_INDICES.items():
        try:
            collection = get_collection(client, name)
            create_date_index(collection, [("date", 1)])

            # 1. DB에서 가장 최근 데이터 날짜 조회
            latest_doc = get_latest_record(collection, sort_field="date")
            
            if latest_doc and 'date' in latest_doc:
                last_date = latest_doc['date']
                if isinstance(last_date, str):
                    last_date = datetime.strptime(last_date, "%Y-%m-%d")
                
                # 마지막 저장일 다음날부터 조회
                start_dt = last_date + timedelta(days=1)
                
                # 만약 시작일이 오늘보다 미래라면(이미 최신임) 스킵
                if start_dt.date() > today.date():
                    print(f"--- {name}: 이미 최신 데이터임 ({last_date.strftime('%Y-%m-%d')}) ---")
                    continue
                
                start_date_str = start_dt.strftime('%Y-%m-%d')
            else:
                # 데이터가 없으면 1년 전부터
                start_date_str = (today - timedelta(days=365)).strftime('%Y-%m-%d')
                print(f"--- {name}: 초기 데이터(1년치) 수집 ---")

            print(f"\n--- {name} 데이터 확인 중 ({start_date_str} ~ {today.strftime('%Y-%m-%d')}) ---")
            
            # 2. yfinance 데이터 다운로드
            data = yf.download(ticker, start=start_date_str, end=end_date_str,
                             auto_adjust=True, progress=False)
            
            if not data.empty:
                df = data.reset_index()
                
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