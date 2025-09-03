# 설치 필요 : pip install yfinance
import yfinance as yf
import pandas as pd
from datetime import datetime
from pymongo import MongoClient
import numpy as np

# MongoDB 연결
client = MongoClient("mongodb+srv://stradivirus:1q2w3e4r6218@cluster0.e7rvfpz.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client['exchange_all']

def safe_clean_value(value):
    """안전한 데이터 변환 함수 - Series 객체 처리 포함"""
    # pandas Series가 넘어올 경우 첫 번째 값 사용
    if isinstance(value, pd.Series):
        value = value.iloc[0]
    
    # NaN 체크
    if pd.isna(value):
        return None
    
    # Timestamp 변환
    if isinstance(value, (pd.Timestamp, np.datetime64)):
        return pd.to_datetime(value).to_pydatetime()
    
    # numpy 숫자 타입 변환
    if isinstance(value, (np.integer, np.floating)):
        return float(value)
    
    # 복잡한 타입은 문자열로 변환
    if isinstance(value, (tuple, list, dict)):
        return str(value)
    
    return value

def get_stock_indices_yahoo():
    """Yahoo Finance에서 주가지수 데이터 조회 및 MongoDB 저장"""
    
    # 주가지수 티커 심볼
    indices = {
        "KOSPI": "^KS11",      # 코스피
        "KOSDAQ": "^KQ11",     # 코스닥
        "DOW_JONES": "^DJI",   # 다우존스
        "NASDAQ": "^IXIC",     # 나스닥
        "SP500": "^GSPC"       # S&P 500
    }
    
    # 2000년부터 현재까지 데이터 조회
    start_date = "2000-01-01"
    end_date = datetime.now().strftime('%Y-%m-%d')
    
    total_saved = 0
    
    for name, ticker in indices.items():
        try:
            print(f"\n--- {name} ({ticker}) 데이터 수집 중 ---")
            
            # 데이터 다운로드
            data = yf.download(ticker, start=start_date, end=end_date, auto_adjust=True, progress=False)
            
            if not data.empty:
                print(f"{name}: {len(data)}개 데이터 조회됨")
                
                # 데이터프레임 리셋
                df = data.reset_index()
                
                # MongoDB에 저장할 레코드 생성
                collection = db[name]
                collection.create_index([("date", 1)], unique=True)
                
                inserted_count = 0
                updated_count = 0
                
                for _, row in df.iterrows():
                    try:
                        # 안전한 데이터 변환
                        record = {
                            'date': safe_clean_value(row['Date']),
                            'open': safe_clean_value(row['Open']),
                            'high': safe_clean_value(row['High']),
                            'low': safe_clean_value(row['Low']),
                            'close': safe_clean_value(row['Close']),
                            'volume': safe_clean_value(row['Volume']),
                            'index_value': safe_clean_value(row['Close']),  # 호환성
                            'created_at': datetime.now()
                        }
                        
                        # MongoDB에 저장
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
                
                # 일일 변화량 계산 (저장 후)
                update_daily_changes(collection)
                
                total_saved += inserted_count + updated_count
                print(f"{name}: 신규 {inserted_count}개, 업데이트 {updated_count}개 저장 완료")
                
                # 최신 데이터 확인
                latest = df.iloc[-1]
                latest_value = safe_clean_value(latest['Close'])
                date_str = safe_clean_value(latest['Date']).strftime('%Y-%m-%d')
                
                print(f"{name} 최신 지수: {latest_value:,.2f} ({date_str})")
                
            else:
                print(f"{name}: 데이터가 비어있음")
                
        except Exception as e:
            print(f"{name} 전체 처리 오류: {e}")
    
    print(f"\n=== 주가지수 데이터 수집 완료 - 총 {total_saved}개 처리됨 ===")
    
    # 저장된 데이터 확인
    print("\n=== 저장된 데이터 확인 ===")
    for index_name in indices.keys():
        collection = db[index_name]
        count = collection.count_documents({})
        print(f"{index_name} 컬렉션: {count:,}개 문서")

def update_daily_changes(collection):
    """일일 변화량 계산 및 업데이트"""
    try:
        # 날짜순으로 정렬된 데이터 조회
        cursor = collection.find({}).sort("date", 1)
        docs = list(cursor)
        
        for i in range(1, len(docs)):
            current_doc = docs[i]
            prev_doc = docs[i-1]
            
            if current_doc.get('close') and prev_doc.get('close'):
                current_value = current_doc['close']
                prev_value = prev_doc['close']
                
                daily_change = current_value - prev_value
                daily_change_pct = (daily_change / prev_value) * 100
                
                # 변화량 업데이트
                collection.update_one(
                    {"_id": current_doc["_id"]},
                    {"$set": {
                        "daily_change": daily_change,
                        "daily_change_pct": daily_change_pct
                    }}
                )
    except Exception as e:
        print(f"변화량 계산 오류: {e}")

if __name__ == "__main__":
    get_stock_indices_yahoo()
    
    # 연결 종료
    client.close()
