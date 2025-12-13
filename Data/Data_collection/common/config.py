# common/config.py
"""
환경 설정 및 API 키 관리
GitHub Actions Secrets 사용 가능하도록 설계
"""
import os

# MongoDB 설정
MONGO_URI = os.getenv(
    'MONGO_URI',
)
MONGO_DB = os.getenv('MONGO_DB')

# 한국은행 API 키
BOK_API_KEY = os.getenv('BOK_API_KEY')

# FRED API 키
FRED_API_KEY = os.getenv('FRED_API_KEY')

# 통화 코드 매핑
CURRENCY_CODES = {
    "0000001": "USD",  # 달러
    "0000002": "JPY",  # 엔 (100엔당)
    "0000053": "CNY",  # 위안
    "0000003": "EUR"   # 유로
}

# 주가지수 티커
STOCK_INDICES = {
    "KOSPI": "^KS11",
    "KOSDAQ": "^KQ11",
    "DOW_JONES": "^DJI",
    "NASDAQ": "^IXIC",
    "SP500": "^GSPC"
}

# 원자재 및 지수 티커
COMMODITIES_INDICES = {
    # 원자재
    "GOLD": "GC=F",
    "CRUDE_OIL": "CL=F",
    "BRENT_OIL": "BZ=F",
    "SILVER": "SI=F",
    "COPPER": "HG=F",
    # 곡물
    "CORN": "ZC=F",
    "WHEAT": "ZW=F",
    "RICE": "ZR=F",
    # 기타
    "COFFEE": "KC=F",
    "SUGAR": "SB=F",
    # 지수
    "DXY": "DX=F",
    "VIX": "^VIX",
}

# 심리지수 설정
SENTIMENT_INDICATORS = {
    "511Y004": {  # 소비자심리지수
        "collection_name": "consumer_sentiment",
        "indicator_name": "소비자심리지수",
        "item_codes": ["FME"],
        "period": "M"
    },
    "513Y001": {  # 경제심리지수
        "collection_name": "economic_sentiment",
        "indicator_name": "경제심리지수",
        "item_codes": ["E1000"],
        "period": "M"
    },
    "521Y001": {  # 뉴스심리지수
        "collection_name": "news_sentiment",
        "indicator_name": "뉴스심리지수",
        "item_codes": ["A001"],
        "period": "D"
    }
}

# 기준금리 설정
INTEREST_RATE_CONFIG = {
    "korea": {
        "collection_name": "KOR_BASE_RATE",
        "stat_code": "722Y001",
        "item_code": "0101000"
    },
    "usa": {
        "collection_name": "US_FED_RATE",
        "series_id": "FEDFUNDS"
    }
}