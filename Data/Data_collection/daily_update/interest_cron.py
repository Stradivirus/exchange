# daily_update/interest_cron.py
"""
한국 + 미국 기준금리 일일 업데이트 (최근 7일)
"""
import sys
sys.path.append('..')

import requests
from fredapi import Fred
from datetime import datetime
from common import (
    get_mongo_client, get_collection, create_date_index,
    BOK_API_KEY, FRED_API_KEY, INTEREST_RATE_CONFIG,
    get_recent_date_range, get_latest_record
)


def check_korea_rates(client):
    """한국 기준금리 체크"""
    print("\n--- 한국 기준금리 변동 체크 중 ---")
    
    config = INTEREST_RATE_CONFIG['korea']
    
    try:
        start_date, end_date = get_recent_date_range(days_back=7)
        
        url = f"https://ecos.bok.or.kr/api/StatisticSearch/{BOK_API_KEY}/json/kr/1/100/{config['stat_code']}/D/{start_date}/{end_date}/{config['item_code']}"
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'StatisticSearch' in data and 'row' in data['StatisticSearch']:
                rows = data['StatisticSearch']['row']
                
                collection = get_collection(client, config['collection_name'])
                create_date_index(collection, [("date", 1)])
                
                latest_db = get_latest_record(collection)
                prev_rate = latest_db['rate'] if latest_db else None
                
                inserted_count = 0
                for row in rows:
                    current_rate = float(row['DATA_VALUE'])
                    current_date = datetime.strptime(row['TIME'], '%Y%m%d')
                    
                    if prev_rate is None or current_rate != prev_rate:
                        record = {
                            'date': current_date,
                            'rate': current_rate,
                            'type': 'base_rate',
                            'country': 'Korea',
                            'source': 'BOK_ECOS',
                            'created_at': datetime.now()
                        }
                        
                        result = collection.replace_one(
                            {"date": record['date']},
                            record,
                            upsert=True
                        )
                        
                        if result.upserted_id:
                            inserted_count += 1
                            print(f"한국 기준금리 변동: {current_date.strftime('%Y-%m-%d')} {prev_rate}% → {current_rate}%")
                        
                        prev_rate = current_rate
                
                if inserted_count > 0:
                    print(f"한국 기준금리: 신규 {inserted_count}개 저장")
                else:
                    print("한국 기준금리: 변경사항 없음")
                
                return inserted_count
            else:
                print("한국 기준금리: 새로운 데이터 없음")
                return 0
        else:
            print(f"한국 기준금리: API 오류 {response.status_code}")
            return 0
            
    except Exception as e:
        print(f"한국 기준금리 오류: {e}")
        return 0


def check_us_rates(client):
    """미국 연방기금금리 체크"""
    print("\n--- 미국 연방기금금리 변동 체크 중 ---")
    
    config = INTEREST_RATE_CONFIG['usa']
    
    try:
        fred = Fred(api_key=FRED_API_KEY)
        
        # 최근 3개월 데이터만 조회
        start_date, _ = get_recent_date_range(days_back=90, date_format='%Y-%m-%d')
        fed_rate_data = fred.get_series(config['series_id'], start=start_date)
        
        if not fed_rate_data.empty:
            latest_fred_date = fed_rate_data.index[-1]
            latest_fred_rate = fed_rate_data.iloc[-1]
            
            collection = get_collection(client, config['collection_name'])
            create_date_index(collection, [("date", 1)])
            
            latest_db = get_latest_record(collection)
            
            if latest_db:
                latest_db_date = latest_db['date']
                latest_db_rate = latest_db['rate']
                
                if (latest_fred_date.to_pydatetime().date() > latest_db_date.date() or
                    abs(latest_fred_rate - latest_db_rate) >= 0.01):
                    
                    record = {
                        'date': latest_fred_date.to_pydatetime(),
                        'rate': float(latest_fred_rate),
                        'type': 'fed_funds_rate',
                        'country': 'USA',
                        'source': 'FRED_API',
                        'series_id': config['series_id'],
                        'created_at': datetime.now()
                    }
                    
                    collection.replace_one(
                        {"date": record['date']},
                        record,
                        upsert=True
                    )
                    
                    print(f"미국 연방기금금리 업데이트: {latest_fred_date.strftime('%Y-%m-%d')} {latest_fred_rate:.2f}%")
                    return 1
                else:
                    print("미국 연방기금금리: 변경사항 없음")
                    return 0
            else:
                # DB가 비어있으면 최신 데이터 저장
                record = {
                    'date': latest_fred_date.to_pydatetime(),
                    'rate': float(latest_fred_rate),
                    'type': 'fed_funds_rate',
                    'country': 'USA',
                    'source': 'FRED_API',
                    'series_id': config['series_id'],
                    'created_at': datetime.now()
                }
                
                collection.insert_one(record)
                print(f"미국 연방기금금리 신규 저장: {latest_fred_date.strftime('%Y-%m-%d')} {latest_fred_rate:.2f}%")
                return 1
        else:
            print("미국 연방기금금리: 새로운 데이터 없음")
            return 0
            
    except Exception as e:
        print(f"미국 연방기금금리 오류: {e}")
        return 0


def main():
    """메인 실행"""
    print(f"=== 기준금리 일일 업데이트 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ===")
    
    client = get_mongo_client()
    
    total_new = 0
    total_new += check_korea_rates(client)
    total_new += check_us_rates(client)
    
    print(f"\n=== 업데이트 완료 - 총 신규: {total_new}개 ===")
    client.close()


if __name__ == "__main__":
    main()