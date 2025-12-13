# common/config.py
"""
환경 설정 및 API 키 관리
GitHub Actions Secrets 사용 가능하도록 설계
"""
import os

# MongoDB 설정
MONGO_URI = os.getenv(
    'MONGO_URI',
    'mongodb+srv://stradivirus:1q2w3e4r6218@cluster0.e7rvfpz.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0'
)
MONGO_DB = os.getenv('MONGO_DB', 'exchange_all')

# 한국은행 API 키
BOK_API_KEY = os.getenv('BOK_API_KEY', 'GYMU5SDZ3BMQ9GWY2JAF')

# FRED API 키
FRED_API_KEY = os.getenv('FRED_API_KEY', 'be3c10f05ec901151d380553080f640e')

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

# 경제지표 설정
ECONOMIC_INDICATORS = [
    {
        "stat_code": "901Y009",
        "indicator_name": "소비자물가지수(총지수)",
        "item_code": "0",
        "period": "M",
        "collection_name": "cpi_index"
    },
    {
        "stat_code": "402Y014",
        "indicator_name": "수출물가지수(기본분류, 총지수)",
        "item_code": "*AA",
        "period": "M",
        "collection_name": "export_import_price_index",
        "type": "export"
    },
    {
        "stat_code": "401Y015",
        "indicator_name": "수입물가지수(기본분류, 총지수)",
        "item_code": "*AA",
        "period": "M",
        "collection_name": "export_import_price_index",
        "type": "import"
    },
    {
        "stat_code": "511Y003",
        "indicator_name": "물가인식(지난 1년)",
        "item_code": "FMA",
        "period": "M",
        "collection_name": "inflation_expectation"
    },
    {
        "stat_code": "511Y003",
        "indicator_name": "향후1년 기대인플레이션율",
        "item_code": "FMB",
        "period": "M",
        "collection_name": "inflation_expectation"
    }
]