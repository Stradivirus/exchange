import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
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

# ===============================
# 2. 데이터 전처리
# ===============================
def prepare_data(df, target_currency, n_lags=5):
    df = df.copy()
    if 'date' in df.columns:
        df.set_index('date', inplace=True)
    df.sort_index(inplace=True)

    # 결측치 보간 (데이터 소멸 방지)
    df = df.ffill()

    df.columns = df.columns.str.lower()
    target_currency = target_currency.lower()

    for i in range(1, n_lags + 1):
        df[f'{target_currency}_lag_{i}'] = df[target_currency].shift(i)
    
    df.dropna(inplace=True)
    
    feature_cols = [col for col in df.columns if col != target_currency]
    
    if len(df) < 10:
        return pd.DataFrame()

    if not feature_cols:
        return df
        
    scaler = MinMaxScaler()
    df[feature_cols] = scaler.fit_transform(df[feature_cols])
    return df

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
        
        df = df.rename(columns={value_field: col_name.upper()})
        df = df[['date', col_name.upper()]]
        dfs.append(df)
        
    client.close()
    if not dfs: return pd.DataFrame()
        
    df_merged = reduce(lambda left, right: pd.merge(left, right, on='date', how='outer'), dfs)
    df_merged = df_merged.sort_values(by='date').reset_index(drop=True)
    return df_merged

# ===============================
# 3. 모델 생성 함수
# ===============================
def create_lstm_model(input_shape, optimizer='adam'):
    model = Sequential([
        LSTM(30, activation='relu', input_shape=input_shape),
        Dense(1)
    ])
    model.compile(optimizer=optimizer, loss='mse')
    return model

# ===============================
# 4. 모델 학습 및 평가
# ===============================
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
        print(f"⚠️ LSTM 학습 오류: {e}")
    finally:
        clear_session()
        gc.collect()

    if not current_results: return None, split_ratio
    return current_results, split_ratio

# ===============================
# 5. 시각화
# ===============================
def plot_predictions(results_dict, full_df):
    valid_currencies = [curr for curr, (res, _) in results_dict.items() if res is not None]
    if not valid_currencies: return go.Figure()

    fig = make_subplots(rows=len(valid_currencies), cols=1, subplot_titles=valid_currencies, vertical_spacing=0.1)
    full_df.columns = full_df.columns.str.lower()

    for i, currency in enumerate(valid_currencies):
        results, best_split = results_dict[currency]
        best_model_name = max(results, key=lambda k: results[k]['R2'])
        idx, _, y_pred = results[best_model_name]['preds']
        
        split_date = idx[0] if len(idx) > 0 else None
        
        fig.add_trace(go.Scatter(x=full_df['date'], y=full_df[currency.lower()], mode='lines', name=f'{currency} (Actual)'), row=i+1, col=1)
        fig.add_trace(go.Scatter(x=idx, y=y_pred, mode='lines', name=f'{currency} (Predicted) - {best_model_name}'), row=i+1, col=1)
        
        if split_date:
            fig.add_vline(x=split_date, line_width=2, line_dash="dash", line_color="grey", row=i+1, col=1)
        
    fig.update_layout(title_text='통화별 최적 모델 예측 결과', height=300*len(valid_currencies), showlegend=True)
    return fig

def plot_summary_table(summary_data):
    if not summary_data: return go.Figure()
    df_summary = pd.DataFrame(summary_data)
    fig = go.Figure(data=[go.Table(header=dict(values=list(df_summary.columns), fill_color='lightblue'), cells=dict(values=[df_summary[c] for c in df_summary.columns]))])
    fig.update_layout(title='모델 성능 요약')
    return fig

def plot_performance_bars(summary_data):
    if not summary_data: return go.Figure()
    df_summary = pd.DataFrame(summary_data)
    currencies = df_summary['Currency'].unique()
    fig = make_subplots(rows=len(currencies), cols=2, subplot_titles=[f"{c} R2/RMSE" for c in currencies])
    for i, currency in enumerate(currencies):
        row = i + 1
        cdf = df_summary[df_summary['Currency'] == currency]
        fig.add_trace(go.Bar(x=cdf['R2 Score'], y=cdf['Model'], orientation='h', name='R2'), row=row, col=1)
        fig.add_trace(go.Bar(x=cdf['RMSE'], y=cdf['Model'], orientation='h', name='RMSE'), row=row, col=2)
    fig.update_layout(height=250*len(currencies), showlegend=False, title_text="성능 비교")
    return fig

def plot_correlation_heatmap(df):
    label_map = {
        'kor_base_rate': '한국금리', 'export_import_price_index': '수출입 지수', 'news_sentiment': '뉴스 심리',
        'usd': 'USD', 'eur': 'EUR', 'jpy': 'JPY', 'cny': 'CNY', 'crude_oil': '오일', 'gold': '금', 'sp500': 'S&P500'
    }
    ordered_cols = ['usd', 'eur', 'jpy', 'cny', 'crude_oil', 'gold', 'sp500', 'kor_base_rate', 'export_import_price_index', 'news_sentiment']
    
    df_proc = df.copy()
    df_proc.columns = df_proc.columns.str.lower()
    
    valid_cols = [c for c in ordered_cols if c in df_proc.columns]
    if len(valid_cols) < 2: return go.Figure()
    
    corr_matrix = df_proc[valid_cols].corr()
    mask = np.triu(np.ones(corr_matrix.shape), k=1).astype(bool)
    corr_matrix_masked = corr_matrix.copy()
    corr_matrix_masked.values[mask] = np.nan
    
    display_labels = [label_map.get(col, col) for col in corr_matrix.columns]
    
    fig = go.Figure(data=go.Heatmap(
        z=corr_matrix_masked, x=display_labels, y=display_labels,
        colorscale='RdBu', zmin=-1, zmax=1,
        text=corr_matrix_masked.map(lambda val: f'{val:.2f}' if pd.notna(val) else ''),
        texttemplate="%{text}", textfont={"size":10}))
    fig.update_layout(title_text="상관계수 분석", height=800, width=900)
    return fig

if __name__ == '__main__':
    logging.basicConfig(level=logging.WARNING)
    print("🚀 [Hong] 환율 예측 분석 시작 (Optimized)")

    collections = ['USD', 'EUR', 'JPY', 'CNY', 'CRUDE_OIL', 'GOLD', 'SP500', 'KOR_BASE_RATE', 'export_import_price_index', 'news_sentiment']
    raw_df = get_currency_data(collections)

    if raw_df.empty:
        logging.warning("데이터 로드 실패")
    else:
        # [수정] config에서 경로 가져오기 (만약 main.py에서 env 주입 안될 경우 대비)
        from config import OUTPUT_PATHS
        results_dir = os.environ.get("RESULTS_DIR", OUTPUT_PATHS["hong"])
        currency_dir = os.path.join(results_dir, "currency")
        os.makedirs(currency_dir, exist_ok=True)

        print("📊 히트맵 생성 중...")
        plot_correlation_heatmap(raw_df).write_html(os.path.join(currency_dir, "correlation_heatmap_basic.html"))

        model_df = raw_df[raw_df['date'] >= '2020-01-01'].copy()
        currencies_to_model = ["USD", "EUR", "JPY", "CNY"]
        
        all_results_for_plotting = {}
        summary_data = []

        for currency in currencies_to_model:
            curr_col = next((c for c in model_df.columns if c.upper() == currency.upper()), None)
            
            if not curr_col:
                print(f"⚠️ {currency} 데이터 없음. 건너뜀.")
                continue
                
            print(f"\n--- {currency} 모델링 ---")
            processed_df = prepare_data(model_df.copy(), curr_col)
            
            if processed_df.empty:
                print(f"⚠️ {currency} 데이터 부족. 건너뜀.")
                continue

            results, best_split = evaluate_models_with_split_optimization(processed_df, curr_col)
            
            if results:
                all_results_for_plotting[currency] = (results, best_split)
                for model_name, model_info in results.items():
                    optimizer = "N/A"
                    if 'LSTM' in model_name: optimizer = model_name.split('_')[1]
                    summary_data.append({'Currency': currency, 'Model': model_name, 'R2 Score': f"{model_info['R2']:.4f}", 'RMSE': f"{model_info['RMSE']:.2f}", 'Train/Test Split': f"{int(best_split*100)}:{int((1-best_split)*100)}", 'Optimizer': optimizer})
            
            gc.collect()

        if summary_data:
            print("💾 결과 저장 중...")
            plot_predictions(all_results_for_plotting, model_df).write_html(os.path.join(currency_dir, "allcurrencies_predictions.html"))
            plot_summary_table(summary_data).write_html(os.path.join(currency_dir, "allcurrencies_summary_table.html"))
            plot_performance_bars(summary_data).write_html(os.path.join(currency_dir, "allcurrencies_performance_bar.html"))
            print("✅ 분석 완료")
        else:
            print("⚠️ 유효한 모델링 결과 없음")