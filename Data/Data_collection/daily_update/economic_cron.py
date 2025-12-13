# daily_update/economic_cron.py
"""
경제지표 일일 업데이트 (최근 1개월)
"""
import sys
sys.path.append('..')

import requests
import pandas as pd
from datetime import datetime
import time
from common import (
    get_mongo_client, get_collection, create_date_index,
    BOK_API_KEY, ECONOMIC_INDICATORS
)


def get_latest_period(period):
    """최신 기간 반환"""
    now = datetime.now()
    if period == "M":
        return now.strftime("%Y%m")
    elif period == "A":
        return now.strftime("%Y")
    else:
        return now.strftime("%Y%m")


def get_economic_data(stat_code, item_code, start_date, end_date, period="M"):
    """경제지표 데이터 조회"""
    url = f"https://ecos.bok.or.kr/api/StatisticSearch/{BOK_API_KEY}/json/kr/1/10/{stat_code}/{period}/{start_date}/{end_date}/{item_code}"
    
    try:
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'StatisticSearch' in data and 'row' in data['StatisticSearch']:
                rows = data['StatisticSearch']['row']
                df = pd.DataFrame(rows)
                
                # 날짜 포맷 처리
                if period == "A":
                    df['date'] = pd.to_datetime(df['TIME'], format='%Y')
                elif period == "M":
                    df['date'] = pd.to_datetime(df['TIME'], format='%Y%m')
                else:
                    df['date'] = pd.to_datetime(df['TIME'], errors='coerce')
                
                df['value'] = pd.to_numeric(df['DATA_VALUE'], errors='coerce')
                df['unit_name'] = df.get('UNIT_NAME', 'N/A')
                df['created_at'] = datetime.now()
                
                return df[['date', 'value', 'unit_name', 'created_at']]
            else:
                return pd.DataFrame()
        else:
            return pd.DataFrame()
            
    except Exception as e:
        print(f"오류 - {stat_code}: {e}")
        return pd.DataFrame()


def main():
    """메인 실행"""
    print(f"=== 경제지표 일일 업데이트 시작 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ===")
    
    client = get_mongo_client()
    total_new = 0
    
    for indicator in ECONOMIC_INDICATORS:
        print(f"\n--- {indicator['indicator_name']} 최신 데이터 확인 중 ---")
        
        time.sleep(0.5)
        
        # 최신 기간만 조회
        latest_period = get_latest_period(indicator['period'])
        
        df = get_economic_data(
            indicator['stat_code'],
            indicator['item_code'],
            latest_period,
            latest_period,
            indicator['period']
        )
        
        if not df.empty:
            collection = get_collection(client, indicator['collection_name'])
            
            # 인덱스 생성
            index_fields = [("date", 1), ("indicator_name", 1)]
            if 'type' in indicator:
                index_fields.append(("type", 1))
            create_date_index(collection, index_fields)
            
            inserted_count = 0
            
            for _, row in df.iterrows():
                record = {
                    'date': row['date'],
                    'value': row['value'],
                    'unit_name': row['unit_name'],
                    'indicator_name': indicator['indicator_name'],
                    'created_at': row['created_at']
                }
                
                if 'type' in indicator:
                    record['type'] = indicator['type']
                
                # 중복 체크 쿼리
                query = {
                    "date": record['date'],
                    "indicator_name": indicator['indicator_name']
                }
                if 'type' in indicator:
                    query["type"] = indicator['type']
                
                # 존재 여부 확인
                exists = collection.find_one(query)
                
                if not exists:
                    collection.insert_one(record)
                    inserted_count += 1
            
            total_new += inserted_count
            
            if inserted_count > 0:
                latest = df.iloc[-1]
                date_format = '%Y-%m-%d' if indicator['period'] == 'M' else '%Y'
                print(f"{indicator['indicator_name']}: 신규 {inserted_count}개, 최신값: {latest['value']:.2f} ({latest['date'].strftime(date_format)})")
            else:
                print(f"{indicator['indicator_name']}: 변경사항 없음")
        else:
            print(f"{indicator['indicator_name']}: 새로운 데이터 없음")
    
    print(f"\n=== 업데이트 완료 - 총 신규: {total_new}개 ===")
    client.close()


if __name__ == "__main__":
    main()