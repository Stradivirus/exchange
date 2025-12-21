# daily_update/commodities_cron.py
"""
원자재/지수 일일 업데이트 (네이버 금융 크롤링 적용 - GitHub Actions 차단 방지)
"""
import sys
sys.path.append('..')

import pandas as pd
import requests
from datetime import datetime, timedelta
import time
from common import (
    get_mongo_client, get_collection, save_records, create_date_index,
    COMMODITIES_INDICES, safe_clean_value, print_summary,
    get_latest_record
)

# 네이버 금융 원자재 코드 매핑
NAVER_COMMODITIES = {
    "GOLD": "CMDT_GC",       # 금
    "CRUDE_OIL": "OIL_CL",   # WTI
    "BRENT_OIL": "OIL_LCO",  # 브렌트유
    "SILVER": "CMDT_SI",     # 은
    "COPPER": "CMDT_HG",     # 구리
    "CORN": "CMDT_C",        # 옥수수
    "WHEAT": "CMDT_W",       # 밀
    "RICE": "CMDT_RR",       # 쌀 (Rough Rice)
    "COFFEE": "CMDT_KC",     # 커피
    "SUGAR": "CMDT_SB",      # 설탕
    "DXY": "FX_USDX",        # 달러 인덱스 (코드 확인 필요, 없을 시 스킵)
    "VIX": "SPI_VIX"         # S&P 500 VIX
}

def get_naver_commodity(code, pages=2):
    """네이버 금융 국제시장 리스트 크롤링"""
    # pages=2 정도면 최근 20일치 데이터 확보 가능
    df_list = []
    try:
        for page in range(1, pages + 1):
            url = f"https://finance.naver.com/marketindex/worldDailyQuote.naver?marketindexCd={code}&fdtc=2&page={page}"
            dfs = pd.read_html(url)
            if dfs:
                df_page = dfs[0]
                df_list.append(df_page)
            time.sleep(0.5)
        
        if df_list:
            df = pd.concat(df_list, ignore_index=True)
            # 컬럼 정리: 날짜, 종가, 전일대비, 등락율
            # 네이버 컬럼: ['날짜', '종가', '전일대비', '등락율']
            df.columns = ['date', 'close', 'diff', 'rate']
            df['date'] = pd.to_datetime(df['date'])
            df['close'] = df['close'].astype(float)
            
            # 없는 컬럼 채우기 (Open, High, Low 정보는 리스트에 없음. Close와 동일하게 처리하거나 비움)
            df['open'] = df['close']
            df['high'] = df['close']
            df['low'] = df['close']
            df['volume'] = 0
            
            # 오름차순 정렬
            df = df.sort_values('date').reset_index(drop=True)
            return df
        return pd.DataFrame()
    except Exception as e:
        print(f"네이버 크롤링 실패 ({code}): {e}")
        return pd.DataFrame()

def main():
    print(f"=== 원자재/지수 업데이트 (Naver) 시작 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ===")
    
    client = get_mongo_client()
    total_new = 0
    today = datetime.now()
    
    for name, _ in COMMODITIES_INDICES.items():
        naver_code = NAVER_COMMODITIES.get(name)
        
        if not naver_code:
            print(f"--- {name}: 네이버 코드 매핑 없음 (Skip) ---")
            continue

        try:
            collection = get_collection(client, name)
            create_date_index(collection, [("date", 1)])

            # 1. DB에서 마지막 날짜 확인
            latest_doc = get_latest_record(collection)
            start_date_str = "초기 데이터"
            
            if latest_doc:
                last_date = latest_doc['date']
                start_dt = last_date + timedelta(days=1)
                
                # 이미 최신이면 스킵 (주말 등 고려)
                if start_dt.date() > today.date():
                    print(f"--- {name}: 이미 최신 데이터 ({last_date.strftime('%Y-%m-%d')}) ---")
                    continue
                start_date_str = start_dt.strftime('%Y-%m-%d')
            else:
                print(f"--- {name}: 초기 데이터 수집 ---")

            print(f"\n--- {name} ({naver_code}) 조회 ---")
            
            # 2. 네이버에서 데이터 가져오기 (최근 20일치)
            df = get_naver_commodity(naver_code, pages=3) 
            
            if not df.empty:
                # DB 마지막 날짜 이후 데이터만 필터링
                if latest_doc:
                    df = df[df['date'] > latest_doc['date']]
                
                if df.empty:
                    print(f"{name}: 새로운 데이터 없음")
                    continue

                records = []
                for _, row in df.iterrows():
                    record = {
                        'date': safe_clean_value(row['date']),
                        'open': safe_clean_value(row['open']),
                        'high': safe_clean_value(row['high']),
                        'low': safe_clean_value(row['low']),
                        'close': safe_clean_value(row['close']),
                        'volume': safe_clean_value(row['volume']),
                        'price': safe_clean_value(row['close']),
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
                    latest_value = safe_clean_value(df.iloc[-1]['close'])
                    latest_date = safe_clean_value(df.iloc[-1]['date'])
                    print_summary(name, inserted, updated, latest_value, latest_date)
                else:
                    print(f"{name}: 변경사항 없음")
            else:
                print(f"{name}: 데이터 수신 실패 (네이버)")
                
        except Exception as e:
            print(f"{name} 오류: {e}")
    
    print(f"\n=== 업데이트 완료 - 총 신규: {total_new}개 ===")
    client.close()

if __name__ == "__main__":
    main()