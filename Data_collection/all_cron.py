"""
all_cron.py
- commodities, stock, exchange, interest 크론 기능을 한 파일에 직접 통합
- 각 파트별 함수로 분리, main에서 순차 실행
- 각 함수별 예외는 개별 처리
"""
import os
from dotenv import load_dotenv
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from pymongo import MongoClient
import numpy as np
import requests
from fredapi import Fred
import time

def safe_clean_value(value):
    if isinstance(value, pd.Series):
        value = value.iloc[0]
    if pd.isna(value):
        return None
    if isinstance(value, (pd.Timestamp, np.datetime64)):
        return pd.to_datetime(value).to_pydatetime()
    if isinstance(value, (np.integer, np.floating)):
        return float(value)
    return value

def update_commodities():
    print("\n=== [CRON] 원자재/지수 일일 업데이트 ===")
    try:
        load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))
        mongo_uri = os.getenv('MONGODB_URI')
        mongo_db = os.getenv('MONGODB_DB', 'exchange_all')
        client = MongoClient(mongo_uri)
        db = client[mongo_db]
        commodities_and_indices = {
            "GOLD": "GC=F",
            "CRUDE_OIL": "CL=F",
            "BRENT_OIL": "BZ=F",
            "SILVER": "SI=F",
            "DXY": "DX=F",
            "VIX": "^VIX",
            "COPPER": "HG=F",
        }
        today = datetime.now()
        start_date = (today - timedelta(days=5)).strftime('%Y-%m-%d')
        end_date = today.strftime('%Y-%m-%d')
        total_new = 0
        for name, ticker in commodities_and_indices.items():
            try:
                print(f"\n--- {name} 최신 데이터 확인 중 ---")
                data = yf.download(ticker, start=start_date, end=end_date, auto_adjust=True, progress=False)
                if not data.empty:
                    df = data.reset_index()
                    collection = db[name]
                    collection.create_index([("date", 1)], unique=True)
                    inserted_count = 0
                    for _, row in df.iterrows():
                        record = {
                            'date': safe_clean_value(row['Date']),
                            'open': safe_clean_value(row['Open']),
                            'high': safe_clean_value(row['High']),
                            'low': safe_clean_value(row['Low']),
                            'close': safe_clean_value(row['Close']),
                            'volume': safe_clean_value(row['Volume']),
                            'price': safe_clean_value(row['Close']),
                            'created_at': datetime.now()
                        }
                        result = collection.replace_one({"date": record['date']}, record, upsert=True)
                        if result.upserted_id:
                            inserted_count += 1
                    total_new += inserted_count
                    if inserted_count > 0:
                        latest_value = safe_clean_value(df.iloc[-1]['Close'])
                        print(f"{name}: 신규 {inserted_count}개 저장, 최신값: ${latest_value:,.2f}")
                    else:
                        print(f"{name}: 변경사항 없음")
                else:
                    print(f"{name}: 새로운 데이터 없음")
            except Exception as e:
                print(f"{name} 오류: {e}")
        print(f"\n=== 업데이트 완료 - 총 신규: {total_new}개 ===")
        client.close()
    except Exception as e:
        print(f"[FAIL] commodities_cron: {e}")

def update_stock():
    print("\n=== [CRON] 주가지수 일일 업데이트 ===")
    try:
        load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))
        mongo_uri = os.getenv('MONGODB_URI')
        mongo_db = os.getenv('MONGODB_DB', 'exchange_all')
        client = MongoClient(mongo_uri)
        db = client[mongo_db]
        indices = {
            "KOSPI": "^KS11",
            "KOSDAQ": "^KQ11",
            "DOW_JONES": "^DJI",
            "NASDAQ": "^IXIC",
            "SP500": "^GSPC"
        }
        today = datetime.now()
        start_date = (today - timedelta(days=5)).strftime('%Y-%m-%d')
        end_date = today.strftime('%Y-%m-%d')
        total_new = 0
        for name, ticker in indices.items():
            try:
                print(f"\n--- {name} 최신 데이터 확인 중 ---")
                data = yf.download(ticker, start=start_date, end=end_date, auto_adjust=True, progress=False)
                if not data.empty:
                    df = data.reset_index()
                    collection = db[name]
                    collection.create_index([("date", 1)], unique=True)
                    inserted_count = 0
                    for _, row in df.iterrows():
                        record = {
                            'date': safe_clean_value(row['Date']),
                            'open': safe_clean_value(row['Open']),
                            'high': safe_clean_value(row['High']),
                            'low': safe_clean_value(row['Low']),
                            'close': safe_clean_value(row['Close']),
                            'volume': safe_clean_value(row['Volume']),
                            'created_at': datetime.now()
                        }
                        result = collection.replace_one({"date": record['date']}, record, upsert=True)
                        if result.upserted_id:
                            inserted_count += 1
                    total_new += inserted_count
                    if inserted_count > 0:
                        latest_value = safe_clean_value(df.iloc[-1]['Close'])
                        print(f"{name}: 신규 {inserted_count}개 저장, 최신값: {latest_value:,.2f}")
                    else:
                        print(f"{name}: 변경사항 없음")
                else:
                    print(f"{name}: 새로운 데이터 없음")
            except Exception as e:
                print(f"{name} 오류: {e}")
        print(f"\n=== 업데이트 완료 - 총 신규: {total_new}개 ===")
        client.close()
    except Exception as e:
        print(f"[FAIL] stock_cron: {e}")

def update_exchange():
    print("\n=== [CRON] 환율 일일 업데이트 ===")
    try:
        load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))
        mongo_uri = os.getenv('MONGODB_URI')
        mongo_db = os.getenv('MONGODB_DB', 'exchange_all')
        api_key = os.getenv('BOK_API_KEY')
        stat_code = "731Y001"
        client = MongoClient(mongo_uri)
        db = client[mongo_db]
        currencies = {
            "0000001": "USD",
            "0000002": "JPY",
            "0000053": "CNY",
            "0000003": "EUR"
        }
        today = datetime.now()
        start_date = (today - timedelta(days=5)).strftime('%Y%m%d')
        end_date = today.strftime('%Y%m%d')
        total_new = 0
        total_updated = 0
        for currency_code, currency_name in currencies.items():
            try:
                url = f"https://ecos.bok.or.kr/api/StatisticSearch/{api_key}/json/kr/1/100/{stat_code}/D/{start_date}/{end_date}/{currency_code}"
                response = requests.get(url, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    if 'StatisticSearch' in data and 'row' in data['StatisticSearch']:
                        rows = data['StatisticSearch']['row']
                        df = pd.DataFrame(rows)
                        df['date'] = pd.to_datetime(df['TIME'], format='%Y%m%d')
                        df['rate'] = df['DATA_VALUE'].astype(float)
                        df['currency_code'] = currency_code
                        df['unit_name'] = df['UNIT_NAME']
                        df['created_at'] = datetime.now()
                        collection = db[currency_name]
                        collection.create_index([("date", 1), ("currency_code", 1)], unique=True)
                        inserted_count = 0
                        updated_count = 0
                        for _, row in df.iterrows():
                            record = row.to_dict()
                            result = collection.replace_one({"date": record['date'], "currency_code": record['currency_code']}, record, upsert=True)
                            if result.upserted_id:
                                inserted_count += 1
                            elif result.modified_count > 0:
                                updated_count += 1
                        total_new += inserted_count
                        total_updated += updated_count
                        if inserted_count > 0 or updated_count > 0:
                            latest_rate = df.iloc[-1]
                            print(f"{currency_name}: 신규 {inserted_count}개, 업데이트 {updated_count}개, 최신 환율: {latest_rate['rate']:.2f}원 ({latest_rate['date'].strftime('%Y-%m-%d')})")
                        else:
                            print(f"{currency_name}: 변경사항 없음")
                    else:
                        print(f"{currency_name}: 새로운 데이터 없음")
                else:
                    print(f"{currency_name}: API 오류 {response.status_code}")
            except Exception as e:
                print(f"{currency_name} 오류: {e}")
        print(f"\n=== 업데이트 완료 - 총 신규: {total_new}개, 업데이트: {total_updated}개 ===")
        client.close()
    except Exception as e:
        print(f"[FAIL] exchange_cron: {e}")

def update_interest():
    print("\n=== [CRON] 기준금리 일일 업데이트 ===")
    try:
        load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))
        mongo_uri = os.getenv('MONGODB_URI')
        mongo_db = os.getenv('MONGODB_DB', 'exchange_all')
        bok_api_key = os.getenv('BOK_API_KEY')
        fred_api_key = os.getenv('FRED_API_KEY')
        client = MongoClient(mongo_uri)
        db = client[mongo_db]
        today = datetime.now()
        total_new = 0
        # 한국 기준금리
        try:
            start_date = (today - timedelta(days=7)).strftime('%Y%m%d')
            end_date = today.strftime('%Y%m%d')
            url = f"https://ecos.bok.or.kr/api/StatisticSearch/{bok_api_key}/json/kr/1/100/722Y001/D/{start_date}/{end_date}/0101000"
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                data = response.json()
                if 'StatisticSearch' in data and 'row' in data['StatisticSearch']:
                    rows = data['StatisticSearch']['row']
                    collection = db['KOR_BASE_RATE']
                    collection.create_index([("date", 1)], unique=True)
                    latest_db_rate = collection.find().sort("date", -1).limit(1)
                    latest_db_rate = list(latest_db_rate)
                    prev_rate = latest_db_rate[0]['rate'] if latest_db_rate else None
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
                            result = collection.replace_one({"date": record['date']}, record, upsert=True)
                            if result.upserted_id:
                                inserted_count += 1
                            prev_rate = current_rate
                    total_new += inserted_count
                    if inserted_count > 0:
                        print(f"한국 기준금리: 신규 {inserted_count}개 저장")
                    else:
                        print("한국 기준금리: 변경사항 없음")
                else:
                    print("한국 기준금리: 새로운 데이터 없음")
            else:
                print(f"한국 기준금리: API 오류 {response.status_code}")
        except Exception as e:
            print(f"한국 기준금리 오류: {e}")
        # 미국 연방기금금리
        try:
            fred = Fred(api_key=fred_api_key)
            start_date = (today - timedelta(days=90)).strftime('%Y-%m-%d')
            fed_rate_data = fred.get_series('FEDFUNDS', start=start_date)
            if not fed_rate_data.empty:
                latest_fred_date = fed_rate_data.index[-1]
                latest_fred_rate = fed_rate_data.iloc[-1]
                collection = db['US_FED_RATE']
                collection.create_index([("date", 1)], unique=True)
                latest_db = collection.find().sort("date", -1).limit(1)
                latest_db = list(latest_db)
                inserted_count = 0
                if latest_db:
                    latest_db_date = latest_db[0]['date']
                    latest_db_rate = latest_db[0]['rate']
                    if (latest_fred_date.to_pydatetime().date() > latest_db_date.date() or abs(latest_fred_rate - latest_db_rate) >= 0.01):
                        record = {
                            'date': latest_fred_date.to_pydatetime(),
                            'rate': float(latest_fred_rate),
                            'type': 'fed_funds_rate',
                            'country': 'USA',
                            'source': 'FRED_API',
                            'series_id': 'FEDFUNDS',
                            'created_at': datetime.now()
                        }
                        result = collection.replace_one({"date": record['date']}, record, upsert=True)
                        if result.upserted_id:
                            inserted_count += 1
                else:
                    record = {
                        'date': latest_fred_date.to_pydatetime(),
                        'rate': float(latest_fred_rate),
                        'type': 'fed_funds_rate',
                        'country': 'USA',
                        'source': 'FRED_API',
                        'series_id': 'FEDFUNDS',
                        'created_at': datetime.now()
                    }
                    collection.insert_one(record)
                    inserted_count += 1
                total_new += inserted_count
                if inserted_count > 0:
                    print(f"미국 연방기금금리: 신규 {inserted_count}개 저장")
                else:
                    print("미국 연방기금금리: 변경사항 없음")
            else:
                print("미국 연방기금금리: 새로운 데이터 없음")
        except Exception as e:
            print(f"미국 연방기금금리 오류: {e}")
        print(f"\n=== 기준금리 업데이트 완료 - 총 신규: {total_new}개 ===")
        client.close()
    except Exception as e:
        print(f"[FAIL] interest_cron: {e}")

if __name__ == "__main__":
    print("=== 모든 크론 작업 시작 ===")
    update_commodities()
    update_stock()
    update_exchange()
    update_interest()
    print("=== 모든 크론 작업 종료 ===")
