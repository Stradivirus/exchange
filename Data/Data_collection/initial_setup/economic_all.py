# initial_setup/economic_all.py
"""
경제지표 데이터 전체 수집 (2010년~현재)
- 소비자물가지수
- 수출/수입물가지수
- 물가인식 및 기대인플레이션율
"""
import sys
sys.path.append('..')

import requests
import pandas as pd
from datetime import datetime
import time
from common import (
    get_mongo_client, get_collection, save_records, create_date_index,
    BOK_API_KEY, ECONOMIC_INDICATORS, get_collection_stats
)


def get_economic_data(stat_code, item_code, start_date, end_date, period="M"):
    """경제지표 데이터 조회"""
    url = f"https://ecos.bok.or.kr/api/StatisticSearch/{BOK_API_KEY}/json/kr/1/10000/{stat_code}/{period}/{start_date}/{end_date}/{item_code}"
    
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
                print(f"데이터 없음 - {stat_code}:{item_code}")
                return pd.DataFrame()
        else:
            print(f"API 오류 {response.status_code}")
            return pd.DataFrame()
            
    except Exception as e:
        print(f"오류 - {stat_code}: {e}")
        return pd.DataFrame()


def main():
    """메인 실행"""
    print("=== 경제지표 데이터 전체 수집 시작 ===")
    
    client = get_mongo_client()
    
    # 수집 기간 설정
    start_date = "201001"  # 2010년 1월
    end_date = datetime.now().strftime('%Y%m')
    
    print(f"수집 기간: {start_date} ~ {end_date}")
    
    for indicator in ECONOMIC_INDICATORS:
        print(f"\n--- {indicator['indicator_name']} 데이터 수집 중 ---")
        
        time.sleep(1)  # API 제한 고려
        
        df = get_economic_data(
            indicator['stat_code'],
            indicator['item_code'],
            start_date,
            end_date,
            indicator['period']
        )
        
        if not df.empty:
            print(f"{indicator['indicator_name']}: {len(df)}개 데이터 조회 완료")
            
            # 추가 필드 설정
            records = df.to_dict('records')
            for record in records:
                record['indicator_name'] = indicator['indicator_name']
                if 'type' in indicator:
                    record['type'] = indicator['type']
            
            # MongoDB 저장
            collection = get_collection(client, indicator['collection_name'])
            
            # 인덱스 생성
            index_fields = [("date", 1), ("indicator_name", 1)]
            if 'type' in indicator:
                index_fields.append(("type", 1))
            create_date_index(collection, index_fields)
            
            # 중복 체크 필드
            unique_fields = ["date", "indicator_name"]
            if 'type' in indicator:
                unique_fields.append("type")
            
            inserted, updated = save_records(
                collection,
                records,
                unique_fields=unique_fields
            )
            
            print(f"{indicator['indicator_name']}: 신규 {inserted}개, 업데이트 {updated}개")
            
            # 최신 데이터
            latest = df.iloc[-1]
            date_format = '%Y-%m-%d' if indicator['period'] == 'M' else '%Y'
            print(f"최신값: {latest['value']:.2f} ({latest['date'].strftime(date_format)})")
        else:
            print(f"{indicator['indicator_name']}: 조회 실패")
        
        time.sleep(0.5)
    
    print("\n=== 전체 수집 완료 ===")
    
    # 통계 출력
    print("\n=== 저장된 데이터 확인 ===")
    collection_names = set([ind['collection_name'] for ind in ECONOMIC_INDICATORS])
    for collection_name in collection_names:
        stats = get_collection_stats(client, collection_name)
        print(f"{collection_name}: {stats['total_count']:,}개")
    
    client.close()


if __name__ == "__main__":
    main()