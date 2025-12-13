import pandas as pd
import numpy as np
import sys
import os
from pymongo import MongoClient
from functools import reduce
from sklearn.preprocessing import MinMaxScaler

# 상위 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# [수정] PG 설정 제거, MONGO 설정 사용
from gu_config import MONGO_URI, DB_NAME, PROJECT_CONFIGS

def get_mongo_data(collection_name, target_col_name):
    try:
        client = MongoClient(MONGO_URI)
        db = client[DB_NAME]
        col = db[collection_name]
        
        start_date = pd.Timestamp('2015-01-01')
        
        # 값 필드 찾기
        doc = col.find_one({}, {'_id': 0, 'value': 1, 'price': 1, 'rate': 1, 'close': 1})
        if not doc: return None
        val_field = next((k for k in ['value', 'price', 'rate', 'close'] if k in doc), None)
        
        data = list(col.find({}, {'_id': 0, 'date': 1, val_field: 1}))
        if not data: return None
            
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])
        df = df[df['date'] >= start_date].set_index('date').sort_index()
        df = df.rename(columns={val_field: target_col_name})
        df = df[~df.index.duplicated(keep='last')]
        
        client.close()
        return df
    except Exception as e:
        print(f"⚠️ MongoDB 로드 실패 ({collection_name}): {e}")
        return None

def prepare_data(project_name):
    print("📊 데이터 준비 중... (MongoDB)")
    try:
        # 컬렉션 이름 매핑 (실제 DB 이름과 일치해야 함)
        sp500 = get_mongo_data('SP500', 'SP 500')
        kospi = get_mongo_data('KOSPI', 'KOSPI')
        usd = get_mongo_data('USD', 'USD/KRW')
        oil = get_mongo_data('CRUDE_OIL', 'CrudeOil')
        
        dfs = [d for d in [sp500, kospi, usd, oil] if d is not None]
        if not dfs: return None, None, None, None, None

        # 데이터 병합
        df_raw = reduce(lambda left, right: pd.merge(left, right, left_index=True, right_index=True, how='inner'), dfs)
        
    except Exception as e:
        print(f"❌ 데이터 준비 오류: {e}")
        return None, None, None, None, None
    
    if (df_raw == 0).sum().sum() > 0:
        df_raw.replace(0, np.nan, inplace=True)
        df_raw.fillna(method='ffill', inplace=True)
        df_raw.dropna(inplace=True)
    
    cfg = PROJECT_CONFIGS[project_name]
    target_col, forecast_days = cfg['target_col'], cfg['forecast_days']
    
    if target_col not in df_raw.columns:
        print(f"❌ 타겟 '{target_col}' 없음. (보유: {df_raw.columns.tolist()})")
        return None, None, None, None, None

    print("⚙️ 피처 엔지니어링...")
    df_returns = df_raw.pct_change()
    df_returns.replace([np.inf, -np.inf], np.nan, inplace=True)
    
    X = pd.DataFrame(index=df_raw.index)
    for col in df_returns.columns:
        X[f'{col}_lag7'] = df_returns[col].shift(7)
        X[f'{col}_ma20'] = df_returns[col].rolling(window=20).mean()
    
    y = df_raw[target_col].shift(-forecast_days)
    final_df = X.copy()
    final_df['y'] = y
    final_df.dropna(inplace=True)
    
    if final_df.empty: return None, None, None, None, None
    return df_raw, final_df.drop('y', axis=1), final_df['y'], target_col, forecast_days

def prepare_data_for_lstm(df_raw, target_col, forecast_days, time_steps=60):
    if target_col not in df_raw.columns: return [], [], [], [], None, []
    
    df = df_raw.copy()
    cols = [target_col] + [c for c in df.columns if c != target_col]
    df = df[cols]
    
    scaler = MinMaxScaler()
    data_scaled = scaler.fit_transform(df)
    
    X, y = [], []
    for i in range(time_steps, len(data_scaled) - forecast_days + 1):
        X.append(data_scaled[i-time_steps:i, :])
        y.append(data_scaled[i + forecast_days - 1, 0])
    
    X, y = np.array(X), np.array(y)
    if len(X) == 0: return [], [], [], [], scaler, []

    train_size = int(len(X) * 0.8)
    return X[:train_size], X[train_size:], y[:train_size], y[train_size:], scaler, df.index[train_size + time_steps + forecast_days - 1:]