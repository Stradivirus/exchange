# daily_update/mental_cron.py
"""
심리지수 일일 업데이트
- 수정사항: 고정 기간 조회 -> DB 마지막 저장일 기준 자동 증분 업데이트
"""
import sys
sys.path.append('..')

import requests
import pandas as pd
from datetime import datetime, timedelta
import time
from common import (
    get_mongo_client, get_collection, create_date_index,
    BOK_API_KEY, SENTIMENT_INDICATORS, get_latest_record
)

def get_sentiment_data(stat_code, item_code, start_date, end_date, period="M"):
    """심리지수 데이터 조회"""
    url = f"https://ecos.bok.or.kr/api/StatisticSearch/{BOK_API_KEY}/json/kr/1/10000/{stat_code}/{period}/{start_date}/{end_date}/{item_code}"
    
    try:
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'StatisticSearch' in data and 'row' in data['StatisticSearch']:
                rows = data['StatisticSearch']['row']
                df = pd.DataFrame(rows)
                
                if period == "D":
                    df['date'] = pd.to_datetime(df['TIME'], format='%Y%m%d')
                else:
                    df['date'] = pd.to_datetime(df['TIME'], format='%Y%m')
                
                df['value'] = pd.to_numeric(df['DATA_VALUE'], errors='coerce')
                df['stat_code'] = stat_code
                df['item_code'] = item_code
                df['item_name'] = df['ITEM_NAME1']
                df['unit_name'] = df['UNIT_NAME']
                df['created_at'] = datetime.now()
                
                if stat_code == "511Y004":
                    df['region_code'] = df['ITEM_CODE2']
                    df['region_name'] = df['ITEM_NAME2']
                    return df[['date', 'value', 'stat_code', 'item_code', 'item_name',
                             'unit_name', 'region_code', 'region_name', 'created_at']]
                
                return df[['date', 'value', 'stat_code', 'item_code', 'item_name',
                         'unit_name', 'created_at']]
            else:
                return pd.DataFrame()
        else:
            print(f"API 오류 {response.status_code}")
            return pd.DataFrame()
            
    except Exception as e:
        print(f"오류 - {stat_code}: {e}")
        return pd.DataFrame()


def main():
    """메인 실행"""
    print(f"=== 심리지수 일일 업데이트 시작 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ===")
    
    client = get_mongo_client()
    total_new = 0
    today = datetime.now()
    
    for stat_code, config in SENTIMENT_INDICATORS.items():
        print(f"\n--- {config['indicator_name']} 데이터 수집 중 ---")
        
        collection = get_collection(client, config['collection_name'])
        create_date_index(collection, [("date", 1), ("item_code", 1)])
        
        # DB에서 최신 데이터 확인
        latest_doc = get_latest_record(collection)
        is_daily = config['period'] == "D"
        
        # 시작일 계산
        if latest_doc:
            last_date = latest_doc['date']
            if is_daily:
                start_dt = last_date + timedelta(days=1)
                date_fmt = '%Y%m%d'
            else:
                # 월별: 다음 달 1일로 설정
                start_dt = (last_date.replace(day=1) + pd.DateOffset(months=1))
                date_fmt = '%Y%m'
            
            # 이미 최신 데이터까지 있으면 스킵
            if start_dt > today:
                print(f"{config['indicator_name']}: 이미 최신 데이터임 ({last_date.strftime('%Y-%m-%d')})")
                continue
                
            start_date_str = start_dt.strftime(date_fmt)
        else:
            # 데이터 없으면 1년 전부터
            if is_daily:
                start_date_str = (today - timedelta(days=365)).strftime('%Y%m%d')
            else:
                start_date_str = (today - pd.DateOffset(months=12)).strftime('%Y%m')
            print(f"{config['indicator_name']}: 초기 데이터 수집")
            
        # 종료일 계산
        if is_daily:
            end_date_str = today.strftime('%Y%m%d')
        else:
            end_date_str = today.strftime('%Y%m')
            
        print(f"조회 기간: {start_date_str} ~ {end_date_str}")
        time.sleep(1)
        
        for item_code in config['item_codes']:
            df = get_sentiment_data(
                stat_code,
                item_code,
                start_date_str,
                end_date_str,
                config['period']
            )
            
            if not df.empty:
                inserted_count = 0
                for _, row in df.iterrows():
                    record = row.to_dict()
                    
                    # 중복 체크
                    exists = collection.find_one({
                        "date": record['date'],
                        "item_code": record['item_code']
                    })
                    
                    if not exists:
                        collection.insert_one(record)
                        inserted_count += 1
                
                total_new += inserted_count
                
                if inserted_count > 0:
                    latest = df.iloc[-1]
                    print(f" -> 신규 {inserted_count}개, 최신값: {latest['value']:.1f} ({latest['date'].strftime('%Y-%m-%d')})")
                else:
                    print(f" -> 변경사항 없음 (API 데이터는 수신됨)")
            else:
                print(f" -> 새로운 데이터 없음")
            
            time.sleep(0.5)
    
    print(f"\n=== 심리지수 업데이트 완료 - 총 신규: {total_new}개 ===")
    client.close()


if __name__ == "__main__":
    main()