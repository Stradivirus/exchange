# /home/exchange/stock_cron.py

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from pymongo import MongoClient
import numpy as np

def safe_clean_value(value):
    """안전한 데이터 변환"""
    if isinstance(value, pd.Series):
        value = value.iloc[0]
    if pd.isna(value):
        return None
    if isinstance(value, (pd.Timestamp, np.datetime64)):
        return pd.to_datetime(value).to_pydatetime()
    if isinstance(value, (np.integer, np.floating)):
        return float(value)
    return value

def daily_stock_update():
    """매일 실행할 주가지수 업데이트"""
    print(f"=== 주가지수 일일 업데이트 시작 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ===")
    
    # 하드코딩 환경설정
    mongo_uri = "mongodb+srv://stradivirus:1q2w3e4r6218@cluster0.e7rvfpz.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    mongo_db = "exchange_all"
    client = MongoClient(mongo_uri)
    db = client[mongo_db]
    
    # 전체 주가지수 포함
    indices = {
        "KOSPI": "^KS11",      # 코스피
        "KOSDAQ": "^KQ11",     # 코스닥 ← 추가
        "DOW_JONES": "^DJI",   # 다우존스 ← 추가
        "NASDAQ": "^IXIC",     # 나스닥
        "SP500": "^GSPC"       # S&P 500
    }
    
    # 최근 5일 데이터만 조회
    today = datetime.now()
    start_date = (today - timedelta(days=5)).strftime('%Y-%m-%d')
    end_date = today.strftime('%Y-%m-%d')
    
    total_new = 0
    
    for name, ticker in indices.items():
        try:
            print(f"\n--- {name} 최신 데이터 확인 중 ---")
            data = yf.download(ticker, start=start_date, end=end_date, auto_adjust=True, progress=False)
            if not data.empty:
                df = data.reset_index()
                collection = db[name]
                collection.create_index([("date", 1)], unique=True)
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
                        if any(record[k] != existing.get(k) for k in ['open','high','low','close','volume']):
                            collection.replace_one(query, record, upsert=True)
                            updated_count += 1
                total_new += inserted_count + updated_count
                if inserted_count > 0 or updated_count > 0:
                    latest_value = safe_clean_value(df.iloc[-1]['Close'])
                    print(f"{name}: 신규 {inserted_count}개, 업데이트 {updated_count}개 저장, 최신값: {latest_value:,.2f}")
                else:
                    print(f"{name}: 변경사항 없음")
            else:
                print(f"{name}: 새로운 데이터 없음")
        except Exception as e:
            print(f"{name} 오류: {e}")
    
    print(f"\n=== 업데이트 완료 - 총 신규: {total_new}개 ===")
    client.close()

if __name__ == "__main__":
    daily_stock_update()

