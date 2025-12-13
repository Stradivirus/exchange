import pandas as pd
import numpy as np
import plotly.graph_objects as go
from pymongo import MongoClient
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import r2_score, mean_squared_error
from functools import reduce

import lightgbm as lgb
import catboost as cb
import xgboost as xgb
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from tensorflow.keras.optimizers import Adam, AdamW
from tensorflow.keras.backend import clear_session
import gc
import os
import sys
import logging
import datetime as dt

# [핵심] 상위 폴더(Graph)의 config.py 불러오기
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import MONGO_URI, DB_NAME, SYSTEM_CONFIG

# [설정] Config 파일 값 적용
N_JOBS_LIMIT = int(SYSTEM_CONFIG["N_JOBS_LIMIT"])
os.environ["OMP_NUM_THREADS"] = SYSTEM_CONFIG["OMP_NUM_THREADS"]
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

try:
    tf.config.set_visible_devices([], 'GPU')
except:
    pass

def get_currency_data(collections, db_name=DB_NAME, connection_string=MONGO_URI):
    client = MongoClient(connection_string)
    db = client[db_name]
    dfs = []
    
    start_date_limit = pd.Timestamp.now() - pd.DateOffset(years=5)

    for col_name in collections:
        col = db[col_name]
        
        doc = col.find_one({}, {"_id": 0, "date": 1, "rate": 1, "value": 1, "price": 1, "close": 1})
        if doc is None: continue
        
        value_field = next((c for c in ['value', 'rate', 'close', 'price'] if c in doc), None)
        if not value_field: continue
            
        data = list(col.find({}, {"_id": 0, "date": 1, value_field: 1}))
        if not data: continue
            
        df = pd.DataFrame(data)
        if df.empty or 'date' not in df.columns: continue

        df["date"] = pd.to_datetime(df["date"])
        df = df[df["date"] >= start_date_limit]
        
        if df.empty: continue
        
        df = df.rename(columns={value_field: col_name})
        dfs.append(df)
        
    client.close()
    if not dfs: return pd.DataFrame()
        
    df_merged = reduce(lambda left, right: pd.merge(left, right, on='date', how='outer'), dfs)
    df_merged = df_merged.sort_values(by='date').reset_index(drop=True)
    return df_merged

def prepare_data(df, target_currency, n_lags=5):
    df = df.copy()
    if 'date' in df.columns:
        df.set_index('date', inplace=True)
    df.sort_index(inplace=True)
    df.columns = df.columns.str.lower()
    target_currency = target_currency.lower()

    for i in range(1, n_lags + 1):
        df[f'{target_currency}_lag_{i}'] = df[target_currency].shift(i)
    df.dropna(inplace=True)

    feature_cols = [col for col in df.columns if col != target_currency]
    if not feature_cols: return df
        
    scaler = MinMaxScaler()
    df[feature_cols] = scaler.fit_transform(df[feature_cols])
    return df

def create_lstm_model(input_shape, optimizer='adam'):
    model = Sequential([
        LSTM(30, activation='relu', input_shape=input_shape),
        Dense(1)
    ])
    model.compile(optimizer=optimizer, loss='mse')
    return model

def evaluate_models_with_split_optimization(df, target_currency):
    feature_columns = [col for col in df.columns if col != target_currency.lower()]
    X = df[feature_columns]
    y = df[target_currency.lower()]
    if X.empty: return None, None

    split_ratio = 0.8
    split_idx = int(len(X) * split_ratio)
    
    X_train = X.iloc[:split_idx]
    X_test = X.iloc[split_idx:]
    y_train = y.iloc[:split_idx]
    y_test = y.iloc[split_idx:]
    
    if len(X_train) < 5 or len(X_test) < 5:
        return None, split_ratio

    current_results = {}
    
    models = {
        'LGBM': lgb.LGBMRegressor(random_state=42, n_jobs=N_JOBS_LIMIT, verbose=-1),
        'CatBoost': cb.CatBoostRegressor(verbose=0, random_state=42, thread_count=N_JOBS_LIMIT),
        'XGBoost': xgb.XGBRegressor(random_state=42, n_jobs=N_JOBS_LIMIT),
    }

    for name, model in models.items():
        try:
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            r2 = r2_score(y_test, y_pred)
            current_results[name] = {'R2': r2, 'RMSE': np.sqrt(mean_squared_error(y_test, y_pred)), 'model': model, 'preds': (y_test.index, y_test, y_pred)}
        except Exception as e:
            print(f"⚠️ {name} 학습 오류: {e}")

    try:
        X_train_lstm = np.reshape(X_train.values, (X_train.shape[0], 1, X_train.shape[1]))
        X_test_lstm = np.reshape(X_test.values, (X_test.shape[0], 1, X_test.shape[1]))

        clear_session()
        lstm_model = create_lstm_model((X_train_lstm.shape[1], X_train_lstm.shape[2]), optimizer=AdamW())
        lstm_model.fit(X_train_lstm, y_train, epochs=20, batch_size=32, verbose=0)
        
        y_pred_lstm = lstm_model.predict(X_test_lstm, verbose=0).flatten()
        r2_lstm = r2_score(y_test, y_pred_lstm)
        current_results['LSTM_AdamW'] = {'R2': r2_lstm, 'RMSE': np.sqrt(mean_squared_error(y_test, y_pred_lstm)), 'model': lstm_model, 'preds': (y_test.index, y_test, y_pred_lstm)}
    except Exception as e:
        print(f"⚠️ LSTM 오류: {e}")
    finally:
        clear_session()
        gc.collect()

    if not current_results: return None, split_ratio
    return current_results, split_ratio

def plot_predictions(results_dict, full_df):
    valid_currencies = [curr for curr, (res, _) in results_dict.items() if res is not None]
    if not valid_currencies: return go.Figure()

    full_df.columns = full_df.columns.str.lower()
    full_df["date"] = pd.to_datetime(full_df["date"], errors="coerce")
    full_df = full_df.dropna(subset=["date"]).sort_values("date")

    fig = go.Figure()

    color_map = {
        "USD": ("#1f77b4", "#17becf"), "EUR": ("#2ca02c", "#98df8a"),
        "JPY": ("#ff7f0e", "#ffbb78"), "CNY": ("#d62728", "#ff9896"),
    }

    for currency in valid_currencies:
        results, _ = results_dict[currency]
        best_model_name = max(results, key=lambda k: results[k]["R2"])
        idx, _, y_pred = results[best_model_name]["preds"]

        x_pred = pd.to_datetime(idx, errors="coerce") if not isinstance(idx, pd.DatetimeIndex) else idx

        if currency.lower() in full_df.columns:
            actual_data = full_df[["date", currency.lower()]].dropna()
            if len(actual_data) > 0:
                fig.add_trace(go.Scatter(
                    x=actual_data["date"].dt.strftime("%Y-%m-%d"),
                    y=actual_data[currency.lower()],
                    mode="lines", name=f"{currency} (Actual)",
                    line=dict(color=color_map.get(currency, ("grey", "grey"))[0], width=2)
                ))

        pred_df = pd.DataFrame({"date": x_pred, "value": y_pred}).dropna()
        if len(pred_df) > 0:
            fig.add_trace(go.Scatter(
                x=pred_df["date"].dt.strftime("%Y-%m-%d"),
                y=pred_df["value"],
                mode="lines", name=f"{currency} (Pred) - {best_model_name}",
                line=dict(color=color_map.get(currency, ("grey", "grey"))[1], width=2)
            ))

    fig.update_layout(
        title="통화별 최적 모델 예측 결과 (통합)",
        yaxis=dict(title="환율 (KRW)"),
        template="plotly_white",
        height=600
    )
    return fig

if __name__ == '__main__':
    logging.basicConfig(level=logging.WARNING)
    print("🚀 [Pred] 종합 예측 분석 시작 (Optimized)")

    collections = [
        'USD', 'EUR', 'JPY', 'CNY', 'CRUDE_OIL', 'GOLD', 'SP500',
        'KOR_BASE_RATE', 'export_import_price_index', 'news_sentiment'
    ]
    raw_df = get_currency_data(collections)

    if not raw_df.empty:
        # [수정] config에서 경로 가져오기
        from config import OUTPUT_PATHS
        results_dir = os.environ.get("RESULTS_DIR", OUTPUT_PATHS["hong"])
        currency_dir = os.path.join(results_dir, "currency")
        os.makedirs(currency_dir, exist_ok=True)

        model_df = raw_df[raw_df["date"] >= (pd.Timestamp.now() - pd.DateOffset(years=5))].copy()
        
        currencies_to_model = ["USD", "EUR", "JPY", "CNY"]
        model_cols = ['date'] + currencies_to_model
        existing_cols = [c for c in model_df.columns if any(curr.lower() == c.lower() for curr in model_cols)]
        currency_only_df = model_df[existing_cols].dropna()

        all_results_for_plotting = {}

        for currency in currencies_to_model:
            target_col = next((c for c in currency_only_df.columns if c.lower() == currency.lower()), None)
            if not target_col: continue

            print(f"🤖 {currency} 모델링 중...")
            processed_df = prepare_data(currency_only_df.copy(), currency)
            results, best_split = evaluate_models_with_split_optimization(processed_df, currency)
            if results:
                all_results_for_plotting[currency] = (results, best_split)
            
            gc.collect()

        if all_results_for_plotting:
            print("💾 결과 저장 중...")
            predictions_fig = plot_predictions(all_results_for_plotting, currency_only_df)
            predictions_fig.write_html(os.path.join(currency_dir, "allcurrencies_predictions1.html"))
            print("✅ [Pred] 분석 완료")
        else:
            print("⚠️ [Pred] 결과 없음")
    else:
        print("⚠️ [Pred] 데이터 로드 실패")