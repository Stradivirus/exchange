# ==========================================================================
# 설정 및 전역 변수 (Settings & Global Variables)
# ==========================================================================

from sklearn.linear_model import LinearRegression, Ridge
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor

# 실행할 프로젝트들
PROJECTS_TO_RUN = ['crude_oil', 'sp500', 'usd_krw']

# 출력 설정
OUTPUT_CONFIG = {
    'save_charts': True,           # 차트를 파일로 저장할지 여부
    'show_detailed_logs': False,   # 상세 로그 출력 여부 (데이터 상세 출력 제어)
    'save_format': ['html', 'png'] # 저장 형식
}

# 프로젝트별 설정 정보
PROJECT_CONFIGS = {
    'usd_krw': {
        'target': 'USD/KRW', 
        'forecast_days': 5,
        'description': '원/달러 환율 예측 (5일 후)'
    },
    'sp500': {
        'target': 'SP 500', 
        'forecast_days': 30,
        'description': 'S&P 500 지수 예측 (30일 후)'
    },
    'crude_oil': {
        'target': 'CrudeOil', 
        'forecast_days': 7,
        'description': '원유 가격 예측 (7일 후)'
    }
}

MODELS = {
    "Linear": LinearRegression(),
    "Ridge": Ridge(alpha=1.0),
    "RandomForest": RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1),
    "XGBoost": XGBRegressor(n_estimators=100, random_state=42, n_jobs=-1)
}

# 데이터베이스 설정
PG_HOST, PG_DB, PG_USER, PG_PASSWORD = "64.110.115.12", "exchange", "exchange_admin", "exchange_password"
