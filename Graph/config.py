# ==========================================================================
# 통합 설정 파일 (Configuration) - Control Tower
# Graph/config.py
# ==========================================================================
import os
from pathlib import Path
from dotenv import load_dotenv # .env 파일 로드용

# 1. 경로 및 환경변수 로드 설정
# 현재 파일(config.py)의 위치: .../exchange/Graph/config.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# .env 파일 위치: .../exchange/.env (Graph 폴더의 상위 폴더)
ROOT_DIR = os.path.dirname(BASE_DIR)
ENV_PATH = os.path.join(ROOT_DIR, '.env')

# .env 파일 로드 (이제 os.environ에서 값을 꺼낼 수 있음)
if os.path.exists(ENV_PATH):
    load_dotenv(ENV_PATH)
else:
    print(f"⚠️ .env 파일을 찾을 수 없습니다: {ENV_PATH}")

# 2. 시스템 리소스 설정
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

SYSTEM_CONFIG = {
    "N_JOBS_LIMIT": "1",
    "OMP_NUM_THREADS": "1"
}

# 3. MongoDB 설정 (환경변수 우선, 없으면 에러 발생 가능)
MONGO_URI = os.environ.get("MONGO_URI")
# .env에는 MONGO_DB라고 되어 있고, 코드에서는 DB_NAME을 썼으니 둘 다 체크
DB_NAME = os.environ.get("MONGO_DB", os.environ.get("DB_NAME", "exchange_all"))

# 5. 경로 설정
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")

OUTPUT_PATHS = {
    "gu": os.path.join(OUTPUT_DIR, "gu"),
    "hong": os.path.join(OUTPUT_DIR, "hong"),
    "kim": os.path.join(OUTPUT_DIR, "kim")
}

# 6. [GU] 프로젝트 실행 설정
PROJECTS_TO_RUN = ['crude_oil', 'sp500', 'usd_krw']

PROJECT_CONFIGS = {
    'usd_krw': {
        'description': '원/달러 환율 예측 (5일 후)',
        'target_col': 'USD/KRW',
        'forecast_days': 5,
        'models': ['Linear', 'Ridge', 'RandomForest', 'XGBoost', 'LSTM', 'GRU']
    },
    'sp500': {
        'description': 'S&P 500 지수 예측 (30일 후)',
        'target_col': 'SP 500',
        'forecast_days': 30,
        'models': ['Linear', 'Ridge', 'RandomForest', 'XGBoost', 'LSTM', 'GRU', 'Prophet']
    },
    'crude_oil': {
        'description': '원유 가격 예측 (7일 후)',
        'target_col': 'CrudeOil',
        'forecast_days': 7,
        'models': ['Linear', 'Ridge', 'RandomForest', 'XGBoost', 'LSTM', 'GRU', 'ARIMA']
    }
}

MODELS = {} 
OUTPUT_CONFIG = {'show_detailed_logs': False}