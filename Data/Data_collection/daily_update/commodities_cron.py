# daily_update/commodities_cron.py
"""
원자재/지수 일일 업데이트 (FinanceDataReader 적용)
"""
import sys
sys.path.append('..')

import FinanceDataReader as fdr
import pandas as pd
from datetime import datetime, timedelta
from common import (
    get_mongo_client, get_collection, save_records, create_date_index,
    COMMODITIES_INDICES, safe_clean_value, print_summary,
    get_latest_record
)

# FDR용 선물/지수 심볼 매핑 (Yahoo -> FDR)
FDR_COMMODITIES = {
    "GOLD": "GC",           # 금 선물
    "CRUDE_OIL": "CL",      # WTI 원유
    "BRENT_OIL": "BZ",      # 브렌트유
    "SILVER": "SI",         # 은
    "COPPER": "HG",         # 구리
    "CORN": "ZC",           # 옥수수
    "WHEAT": "ZW",          # 밀
    "RICE": "ZR",           # 쌀 (Rough Rice)
    "COFFEE": "KC",         # 커피
    "SUGAR": "SB",          # 설탕
    "DXY": "DX",            # 달러 인덱스
    "VIX": "VIX"            # 공포 지수 (S&P 500 VIX는 FDR에서 지원 확인 필요, 보통 VIX 사용)
}

def main():
    print(f"=== 원자재/지수 업데이트 (FDR) 시작 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ===")
    
    client = get_mongo_client()
    total_new = 0
    today = datetime.now()
    
    for name, _ in COMMODITIES_INDICES.items():
        fdr_symbol = FDR_COMMODITIES.get(name)
        
        # 매핑되지 않은 항목은 스킵하거나 로그 남김
        if not fdr_symbol:
            print(f"--- {name}: FDR 심볼 매핑 없음 (Skip) ---")
            continue

        try:
            collection = get_collection(client, name)
            create_date_index(collection, [("date", 1)])

            # 1. DB에서 마지막 날짜 확인
            latest_doc = get_latest_record(collection)
            
            if latest_doc:
                last_date = latest_doc['date']
                start_dt = last_date + timedelta(days=1)
                
                if start_dt.date() > today.date():
                    print(f"--- {name}: 이미 최신 데이터 ({last_date.strftime('%Y-%m-%d')}) ---")
                    continue
                
                start_date_str = start_dt.strftime('%Y-%m-%d')
            else:
                # 데이터 없으면 1년 전부터
                start_date_str = (today - timedelta(days=365)).strftime('%Y-%m-%d')
                print(f"--- {name}: 초기 데이터(1년치) 수집 ---")

            print(f"\n--- {name} ({fdr_symbol}) 조회: {start_date_str} ~ ---")
            
            # 2. FDR 데이터 수집
            try:
                df = fdr.DataReader(fdr_symbol, start=start_date_str)
            except Exception:
                # VIX 같은 경우 symbol이 다를 수 있어 예외 처리
                if name == "VIX":
                    # FDR에서 VIX 데이터가 안 나오면 investing.com 티커 시도 등 (여기선 pass)
                    print(f"{name}: FDR 조회 실패 (심볼 확인 필요)")
                    continue
                raise

            if not df.empty:
                df = df.reset_index()
                
                records = []
                for _, row in df.iterrows():
                    # FDR 컬럼: Date, Open, High, Low, Close, Volume 등
                    record = {
                        'date': safe_clean_value(row['Date']),
                        'open': safe_clean_value(row.get('Open')),
                        'high': safe_clean_value(row.get('High')),
                        'low': safe_clean_value(row.get('Low')),
                        'close': safe_clean_value(row.get('Close')),
                        'volume': safe_clean_value(row.get('Volume')),
                        'price': safe_clean_value(row.get('Close')), # 호환성 유지
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