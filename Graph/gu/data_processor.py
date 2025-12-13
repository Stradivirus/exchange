# ==========================================================================
# 데이터 준비 함수 (Data Preparation Functions)
# ==========================================================================

import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from sklearn.preprocessing import MinMaxScaler
from config import PG_HOST, PG_DB, PG_USER, PG_PASSWORD, OUTPUT_CONFIG

def prepare_data(project_name):
    """
    데이터베이스에서 데이터를 로딩하고 전처리합니다.
    """
    print("📊 데이터 준비 중...")
    
    try:
        db_uri = f"postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}/{PG_DB}"
        engine = create_engine(db_uri)
        
        stock_df = pd.read_sql("SELECT date, sp500, kospi FROM stock ORDER BY date", engine, index_col='date', parse_dates=True)
        usd_df = pd.read_sql("SELECT date, usd FROM exchange ORDER BY date", engine, index_col='date', parse_dates=True)
        oil_df = pd.read_sql("SELECT date, crude_oil FROM commodities ORDER BY date", engine, index_col='date', parse_dates=True)
        
        df_raw = stock_df.join(usd_df, how='inner').join(oil_df, how='inner')
        df_raw.columns = ['SP 500', 'KOSPI', 'USD/KRW', 'CrudeOil']
        
    except Exception as e:
        print(f"❌ 데이터 로딩 실패: {e}")
        return None, None, None, None, None
    
    print("🔄 데이터 정제 중...")
    df_raw.dropna(inplace=True)
    df_raw.index = pd.to_datetime(df_raw.index)
    
    zero_counts = (df_raw == 0).sum()
    if zero_counts.sum() > 0:
        df_raw.replace(0, np.nan, inplace=True)
        df_raw.fillna(method='ffill', inplace=True)
    
    df_raw = df_raw.loc['2015-01-01':]
    
    # 상세 로그는 조건부 출력
    if OUTPUT_CONFIG['show_detailed_logs']:
        print(f"데이터 기간: {df_raw.index.min().strftime('%Y-%m-%d')} ~ {df_raw.index.max().strftime('%Y-%m-%d')}")
        print(f"데이터 크기: {len(df_raw)}행")
    
    configs = {
        'usd_krw': {'target': 'USD/KRW', 'forecast_days': 5},
        'sp500': {'target': 'SP 500', 'forecast_days': 30},
        'crude_oil': {'target': 'CrudeOil', 'forecast_days': 7}
    }
    
    cfg = configs[project_name]
    target_col, forecast_days = cfg['target'], cfg['forecast_days']
    
    print("⚙️ 피처 엔지니어링 중...")
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
    
    if final_df.empty:
        print("❌ 최종 데이터셋이 비어있습니다.")
        return None, None, None, None, None
    
    X = final_df.drop('y', axis=1)
    y = final_df['y']
    
    if X.isnull().values.any() or y.isnull().values.any():
        print("❌ NaN 값이 남아있습니다.")
        return None, None, None, None, None
    
    print("✅ 데이터 준비 완료")
    return df_raw, X, y, target_col, forecast_days

def prepare_data_for_lstm(df_raw, target_col, forecast_days, time_steps=60):
    """
    딥러닝 모델 학습을 위해 시계열 데이터를 전처리하고 시퀀스 형태로 변환합니다.
    """
    print("🔄 LSTM용 데이터 전처리 중...")
    
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
    
    train_size = int(len(X) * 0.8)
    X_train, X_test, y_train, y_test = X[:train_size], X[train_size:], y[:train_size], y[train_size:]
    
    test_dates = df.index[train_size + time_steps + forecast_days - 1:]
    
    return X_train, X_test, y_train, y_test, scaler, test_dates
