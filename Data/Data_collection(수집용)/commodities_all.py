# /home/exchange/commodities.py
import os
from dotenv import load_dotenv
import yfinance as yf
import pandas as pd
from datetime import datetime
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

def collect_commodities_and_indices():
    """원자재 및 지수 데이터 수집"""
    print(f"=== 원자재 및 지수 데이터 수집 시작 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ===")

    # 환경변수 로드
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))
    mongo_uri = os.getenv('MONGODB_URI')
    mongo_db = os.getenv('MONGODB_DB', 'exchange_all')
    client = MongoClient(mongo_uri)
    db = client[mongo_db]
    
    # 원자재 및 지수 데이터
    commodities_and_indices = {
        # 원자재
        "GOLD": "GC=F",           # 금 선물
        "CRUDE_OIL": "CL=F",      # 원유 선물 (WTI)
        "BRENT_OIL": "BZ=F",     # 브렌트유 선물
        "SILVER": "SI=F",         # 은 선물
        
        # 달러 관련
        "DXY": "DX=F",            # 달러 인덱스
        
        # 기타
        "VIX": "^VIX",            # 변동성 지수
        "COPPER": "HG=F",         # 구리 선물
    }
    
    # 2010년부터 현재까지
    start_date = "2010-01-01"
    end_date = datetime.now().strftime('%Y-%m-%d')
    
    total_saved = 0
    
    for name, ticker in commodities_and_indices.items():
        try:
            print(f"\n--- {name} ({ticker}) 데이터 수집 중 ---")
            
            # 데이터 다운로드
            data = yf.download(ticker, start=start_date, end=end_date, auto_adjust=True, progress=False)
            
            if not data.empty:
                print(f"{name}: {len(data)}개 데이터 조회됨")
                
                df = data.reset_index()
                collection = db[name]
                collection.create_index([("date", 1)], unique=True)
                
                inserted_count = 0
                updated_count = 0
                
                for _, row in df.iterrows():
                    try:
                        record = {
                            'date': safe_clean_value(row['Date']),
                            'open': safe_clean_value(row['Open']),
                            'high': safe_clean_value(row['High']),
                            'low': safe_clean_value(row['Low']),
                            'close': safe_clean_value(row['Close']),
                            'volume': safe_clean_value(row['Volume']),
                            'price': safe_clean_value(row['Close']),  # 호환성
                            'created_at': datetime.now()
                        }
                        
                        result = collection.replace_one(
                            {"date": record['date']},
                            record,
                            upsert=True
                        )
                        
                        if result.upserted_id:
                            inserted_count += 1
                        elif result.modified_count > 0:
                            updated_count += 1
                            
                    except Exception as e:
                        print(f"개별 저장 오류 - {name}: {e}")
                
                total_saved += inserted_count + updated_count
                print(f"{name}: 신규 {inserted_count}개, 업데이트 {updated_count}개 저장 완료")
                
                # 최신 데이터 확인
                latest = df.iloc[-1]
                latest_value = safe_clean_value(latest['Close'])
                date_str = safe_clean_value(latest['Date']).strftime('%Y-%m-%d')
                
                print(f"{name} 최신 가격: ${latest_value:,.2f} ({date_str})")
                
            else:
                print(f"{name}: 데이터가 비어있음")
                
        except Exception as e:
            print(f"{name} 전체 처리 오류: {e}")
    
    print(f"\n=== 원자재/지수 데이터 수집 완료 - 총 {total_saved}개 처리됨 ===")
    
    # 저장된 데이터 확인
    print("\n=== 저장된 데이터 확인 ===")
    for index_name in commodities_and_indices.keys():
        collection = db[index_name]
        count = collection.count_documents({})
        print(f"{index_name} 컬렉션: {count:,}개 문서")
    
    client.close()

if __name__ == "__main__":
    collect_commodities_and_indices()
