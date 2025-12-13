from pymongo import MongoClient
import requests
import pandas as pd
from datetime import datetime
import time

# 하드코딩 환경설정
mongo_uri = "mongodb+srv://stradivirus:1q2w3e4r6218@cluster0.e7rvfpz.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
mongo_db = "exchange_all"
api_key = "GYMU5SDZ3BMQ9GWY2JAF"

client = MongoClient(mongo_uri)
db = client[mongo_db]

# 완전한 심리지수 설정 (3개 모두)
sentiment_indicators = {
    "511Y004": {  # 소비자심리지수
        "collection_name": "consumer_sentiment",
        "indicator_name": "소비자심리지수",
        "item_codes": ["FME"],  # 소비자심리지수
        "period": "M"
    },
    "513Y001": {  # 경제심리지수
        "collection_name": "economic_sentiment",
        "indicator_name": "경제심리지수",
        "item_codes": ["E1000"],  # 경제심리지수(원계열)
        "period": "M"
    },
    "521Y001": {  # 뉴스심리지수
        "collection_name": "news_sentiment",
        "indicator_name": "뉴스심리지수",
        "item_codes": ["A001"],  # 뉴스심리지수
        "period": "D"  # 일별 데이터

        
    }
}

def get_sentiment_data_batch(stat_code, item_code, start_date, end_date, period="M"):
    """심리지수 데이터를 배치로 조회하는 함수"""
    url = f"https://ecos.bok.or.kr/api/StatisticSearch/{api_key}/json/kr/1/10000/{stat_code}/{period}/{start_date}/{end_date}/{item_code}"
    
    try:
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'StatisticSearch' in data and 'row' in data['StatisticSearch']:
                rows = data['StatisticSearch']['row']
                df = pd.DataFrame(rows)
                
                # 날짜 포맷 처리 (일별 vs 월별)
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
                
                # 소비자심리지수의 경우 지역 정보 추가
                if stat_code == "511Y004":
                    df['region_code'] = df['ITEM_CODE2']
                    df['region_name'] = df['ITEM_NAME2']
                
                return df[['date', 'value', 'stat_code', 'item_code', 'item_name', 'unit_name', 'created_at'] + 
                         (['region_code', 'region_name'] if stat_code == "511Y004" else [])]
            else:
                print(f"데이터가 없습니다 - 통계코드: {stat_code}, 항목코드: {item_code}")
                return pd.DataFrame()
        else:
            print(f"API 오류 {response.status_code} - 통계코드: {stat_code}")
            return pd.DataFrame()
            
    except Exception as e:
        print(f"오류 발생 - 통계코드 {stat_code}: {e}")
        return pd.DataFrame()

def save_sentiment_to_mongodb(collection_name, df):
    """MongoDB에 심리지수 데이터 저장 - 주석처리"""
    if df.empty:
        print(f"{collection_name}: 저장할 데이터가 없습니다.")
        return
    
    collection = db[collection_name]
    
    # 기존 인덱스 생성 (중복 방지)
    collection.create_index([("date", 1), ("item_code", 1)], unique=True)
    
    # 데이터 저장
    records = df.to_dict('records')
    inserted_count = 0
    updated_count = 0
    
    for record in records:
        try:
            result = collection.replace_one(
                {"date": record['date'], "item_code": record['item_code']},
                record,
                upsert=True
            )
            if result.upserted_id:
                inserted_count += 1
            else:
                updated_count += 1
        except Exception as e:
            print(f"저장 오류 - {collection_name}: {e}")
    
    print(f"{collection_name}: 신규 {inserted_count}개, 업데이트 {updated_count}개 저장 완료")

def main():
    """메인 실행 함수"""
    print("=== 심리지수 데이터 수집 및 확인 시작 ===")
    
    for stat_code, config in sentiment_indicators.items():
        print(f"\n--- {config['indicator_name']} 데이터 수집 중 ---")
        
        # 날짜 설정 (모두 2010년부터 시작)
        if config['period'] == "D":  # 뉴스심리지수 (일별)
            start_date = "20100101"
            today = datetime.now().strftime('%Y%m%d')
        else:  # 소비자/경제심리지수 (월별)
            start_date = "201001"
            today = datetime.now().strftime('%Y%m')
        
        print(f"수집 기간: {start_date} ~ {today}")
        
        # API 호출 제한을 고려한 지연
        time.sleep(1)
        
        for item_code in config['item_codes']:
            print(f"항목코드 {item_code} 수집 중...")
            
            # 데이터 조회
            df = get_sentiment_data_batch(
                stat_code, 
                item_code, 
                start_date, 
                today, 
                config['period']
            )
            
            if not df.empty:
                print(f"{config['indicator_name']}: {len(df)}개 데이터 조회 완료")
                
                # ### MongoDB에 저장 - 주석처리 ###
                save_sentiment_to_mongodb(config['collection_name'], df)
                
                # 데이터 확인을 위한 출력
                print(f"\n=== {config['indicator_name']} 데이터 샘플 ===")
                print(f"컬럼: {list(df.columns)}")
                
                # 소비자심리지수의 경우 지역별 정보 출력
                if stat_code == "511Y004":
                    print(f"\n지역별 데이터:")
                    regions = df.groupby(['region_code', 'region_name']).size()
                    for (code, name), count in regions.items():
                        print(f"  {code}: {name} ({count}개)")
                
                print("\n최초 5개 데이터:")
                print(df.head().to_string())
                print("\n최근 5개 데이터:")
                print(df.tail().to_string())
                
                # 최신 데이터 확인
                latest_data = df.iloc[-1]
                date_format = '%Y-%m-%d' if config['period'] == 'D' else '%Y-%m'
                print(f"\n{config['indicator_name']} 최신값: {latest_data['value']:.2f} ({latest_data['date'].strftime(date_format)})")
                
                # 기본 통계
                print(f"\n{config['indicator_name']} 기본 통계:")
                print(f"- 최소값: {df['value'].min():.2f}")
                print(f"- 최대값: {df['value'].max():.2f}")
                print(f"- 평균값: {df['value'].mean():.2f}")
                print(f"- 표준편차: {df['value'].std():.2f}")
                
            else:
                print(f"{config['indicator_name']}: 조회된 데이터가 없습니다")
            
            # 항목 간 지연
            time.sleep(0.5)
    
    print("\n=== 심리지수 데이터 확인 완료 ===")

if __name__ == "__main__":
    main()
    client.close()
