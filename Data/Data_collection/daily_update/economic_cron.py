# daily_update/economic_cron.py
"""
경제지표 일일 업데이트
- 수정사항: 고정 기간 조회 -> DB 마지막 저장일 기준 자동 증분 업데이트
"""
import sys
sys.path.append('..')

import requests
import pandas as pd
from datetime import datetime
import time
from common import (
    get_mongo_client, get_collection, create_date_index,
    BOK_API_KEY, ECONOMIC_INDICATORS, get_latest_record
)


def get_economic_data(stat_code, item_code, start_date, end_date, period="M"):
    """경제지표 데이터 조회"""
    url = f"https://ecos.bok.or.kr/api/StatisticSearch/{BOK_API_KEY}/json/kr/1/1000/{stat_code}/{period}/{start_date}/{end_date}/{item_code}"
    
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
    today = datetime.now()
    
    for indicator in ECONOMIC_INDICATORS:
        print(f"\n--- {indicator['indicator_name']} 최신 데이터 확인 중 ---")
        
        collection = get_collection(client, indicator['collection_name'])
        
        # 인덱스 생성
        index_fields = [("date", 1), ("indicator_name", 1)]
        if 'type' in indicator:
            index_fields.append(("type", 1))
        create_date_index(collection, index_fields)
        
        # DB에서 최신 데이터 확인
        # (주의: 같은 컬렉션에 여러 indicator가 섞여있을 수 있으므로 쿼리로 필터링 필요할 수 있음. 
        # 여기서는 get_latest_record가 단순 정렬만 하므로, 정확성을 위해 쿼리를 직접 작성)
        query = {"indicator_name": indicator['indicator_name']}
        if 'type' in indicator:
            query['type'] = indicator['type']
            
        latest_doc = collection.find_one(query, sort=[("date", -1)])
        
        period = indicator['period']
        date_fmt = '%Y%m' if period == 'M' else '%Y'
        
        if latest_doc:
            last_date = latest_doc['date']
            
            # 다음 기간 계산
            if period == 'M':
                start_dt = (last_date.replace(day=1) + pd.DateOffset(months=1))
            else: # 'A' (연간)
                start_dt = (last_date.replace(day=1) + pd.DateOffset(years=1))
            
            if start_dt > today:
                print(f"{indicator['indicator_name']}: 이미 최신 데이터임 ({last_date.strftime('%Y-%m-%d')})")
                continue
                
            start_date_str = start_dt.strftime(date_fmt)
        else:
            # 데이터 없으면 2년 전부터 (경제지표는 발표가 늦으므로 넉넉하게)
            if period == 'M':
                start_date_str = (today - pd.DateOffset(months=24)).strftime(date_fmt)
            else:
                start_date_str = (today - pd.DateOffset(years=5)).strftime(date_fmt)
            print(f"{indicator['indicator_name']}: 초기 데이터 수집")
            
        end_date_str = today.strftime(date_fmt)
        print(f"조회 기간: {start_date_str} ~ {end_date_str}")
        
        time.sleep(0.5)
        
        df = get_economic_data(
            indicator['stat_code'],
            indicator['item_code'],
            start_date_str,
            end_date_str,
            period
        )
        
        if not df.empty:
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
                check_query = {
                    "date": record['date'],
                    "indicator_name": indicator['indicator_name']
                }
                if 'type' in indicator:
                    check_query["type"] = indicator['type']
                
                exists = collection.find_one(check_query)
                
                if not exists:
                    collection.insert_one(record)
                    inserted_count += 1
            
            total_new += inserted_count
            
            if inserted_count > 0:
                latest = df.iloc[-1]
                print(f" -> 신규 {inserted_count}개, 최신값: {latest['value']:.2f} ({latest['date'].strftime('%Y-%m-%d')})")
            else:
                print(f" -> 변경사항 없음")
        else:
            print(f" -> 새로운 데이터 없음")
    
    print(f"\n=== 업데이트 완료 - 총 신규: {total_new}개 ===")
    client.close()


if __name__ == "__main__":
    main()