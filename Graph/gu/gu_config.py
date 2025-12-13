# Graph/gu/gu_config.py
import sys
import os
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.ensemble import RandomForestRegressor
import xgboost as xgb

# [중요] 부모 폴더(Graph)를 파이썬 검색 경로 맨 앞에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 이제 Graph/config.py를 가져옵니다.
from config import *

# 모델 정의
MODELS = {
    'Linear': LinearRegression(),
    'Ridge': Ridge(),
    'RandomForest': RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=1),
    'XGBoost': xgb.XGBRegressor(n_estimators=100, learning_rate=0.05, random_state=42, n_jobs=1)
}