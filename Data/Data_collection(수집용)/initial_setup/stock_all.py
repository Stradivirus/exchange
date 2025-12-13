# initial_setup/stock_all.py
"""
주가지수 데이터 전체 수집 (2010년~현재)
"""
import sys
sys.path.append('..')

import yfinance as yf
from datetime import datetime
from common import (
    get_mongo_client, get_collection, save_records, create_date_index,
    STOCK_INDICES, safe_clean_value, dataframe_to_records, get_collection_stats
)


def update_daily_changes(collection):
    """일일 변화량 계산"""
    try:
        cursor = collection.find({}).sort("date", 1)
        docs = list(cursor)
        
        for i in range(1, len(docs)):
            current = docs[i]
            prev = docs[i-1]
            
            if current.get('close') and prev.get('close'):
                current_value = current['close']
                prev_value = prev['close']
                
                daily_change = current_value - prev_value
                daily_change_pct = (daily_change / prev_value) * 100
                
                collection.update_one(
                    {"_id": current["_id"]},
                    {"$set": {
                        "daily_change": daily_change,
                        "daily_change_pct": daily_change_pct
                    }}
                )
    except Exception as e:
        print(f"변화량 계산 오류: {e}")


def main():
    """메인 실행"""
    print("=== 주가지수 데이터 전체 수집 시작 ===")
    
    start_date = "2010-01-01"
    end_date = datetime.now().strftime('%Y-%m-%d')
    print(f"수집 기간: {start_date} ~ {end_date}")
    
    client = get_mongo_client()
    total_saved = 0
    
    for name, ticker in STOCK_INDICES.items():
        try:
            print(f"\n--- {name} ({ticker}) 데이터 수집 중 ---")
            
            data = yf.download(ticker, start=start_date, end=end_date, 
                             auto_adjust=True, progress=False)
            
            if not data.empty:
                print(f"{name}: {len(data)}개 데이터 조회됨")
                
                df = data.reset_index()
                
                # 데이터 변환
                records = []
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
                    records.append(record)
                
                # MongoDB 저장
                collection = get_collection(client, name)
                create_date_index(collection, [("date", 1)])
                
                inserted, updated = save_records(
                    collection, 
                    records, 
                    unique_fields=["date"]
                )
                
                # 변화량 계산
                update_daily_changes(collection)
                
                total_saved += inserted + updated
                print(f"{name}: 신규 {inserted}개, 업데이트 {updated}개")
                
                # 최신 데이터
                latest = df.iloc[-1]
                latest_value = safe_clean_value(latest['Close'])
                date_str = safe_clean_value(latest['Date']).strftime('%Y-%m-%d')
                print(f"최신 지수: {latest_value:,.2f} ({date_str})")
            else:
                print(f"{name}: 데이터 없음")
                
        except Exception as e:
            print(f"{name} 오류: {e}")
    
    print(f"\n=== 전체 수집 완료 - 총 {total_saved}개 처리됨 ===")
    
    # 통계 출력
    print("\n=== 저장된 데이터 확인 ===")
    for index_name in STOCK_INDICES.keys():
        stats = get_collection_stats(client, index_name)
        print(f"{index_name}: {stats['total_count']:,}개")
    
    client.close()


if __name__ == "__main__":
    main()