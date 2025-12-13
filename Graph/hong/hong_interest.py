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

def get_currency_data(collections, db_name=DB_NAME, connection_string=MONGO_URI):
    client = MongoClient(connection_string)
    db = client[db_name]
    dfs = []
    
    start_date_limit = pd.Timestamp('2015-01-01')

    for col in collections:
        collection = db[col.upper()]
        
        query = {}
        if collection.find_one({"date": {"$exists": True}}):
            query = {"date": {"$gte": start_date_limit}}

        data = list(collection.find(query, {"_id": 0, "date": 1, "rate": 1}))
        if not data:
            print(f"⚠️ [Interest] '{col}' 데이터 없음")
            continue
            
        df = pd.DataFrame(data)
        if df.empty or 'date' not in df.columns: continue

        df["date"] = pd.to_datetime(df["date"])
        df = df[df["date"] >= start_date_limit]
        
        if df.empty: continue

        df = df.rename(columns={"rate": col.upper()})
        dfs.append(df)
        
    client.close()
    if not dfs:
        return pd.DataFrame()
        
    final_df = reduce(lambda left, right: pd.merge(left, right, on='date', how='outer'), dfs)
    final_df = final_df.sort_values(by='date').reset_index(drop=True)
    
    if 'KOR_BASE_RATE' in final_df.columns:
        final_df['KOR_BASE_RATE'] = final_df['KOR_BASE_RATE'].ffill()
    
    final_df.dropna(inplace=True)
    return final_df

def prepare_data(df, target_currency, n_lags=5):
    df = df.copy()
    if 'date' in df.columns:
        df.set_index('date', inplace=True)
    df.sort_index(inplace=True)
    for i in range(1, n_lags + 1):
        df[f'{target_currency}_lag_{i}'] = df[target_currency].shift(i)
    df.dropna(inplace=True)
    feature_cols = [col for col in df.columns if col != target_currency]
    if not feature_cols:
        return df, None
    scaler = MinMaxScaler()
    df[feature_cols] = scaler.fit_transform(df[feature_cols])
    return df, feature_cols

def create_lstm_model(input_shape, optimizer='adam'):
    model = Sequential([
        LSTM(30, activation='relu', input_shape=input_shape),
        Dense(1)
    ])
    model.compile(optimizer=optimizer, loss='mse')
    return model

def evaluate_models_with_split_optimization(df, target_currency, feature_columns):
    X = df[feature_columns]
    y = df[target_currency]
    if X.empty: return None, None

    split_ratio = 0.8
    split_idx = int(len(X) * split_ratio)
    
    X_train = X.iloc[:split_idx]
    X_test = X.iloc[split_idx:]
    y_train = y.iloc[:split_idx]
    y_test = y.iloc[split_idx:]
    
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
            print(f"⚠️ {name} 오류: {e}")

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

def plot_correlation_heatmap(df):
    ordered_cols = ['KOR_BASE_RATE', 'USD', 'EUR', 'JPY', 'CNY']
    corr_cols = [col for col in ordered_cols if col in df.columns]
    if len(corr_cols) < 2: return go.Figure()

    corr_matrix = df[corr_cols].corr()
    mask = np.triu(np.ones_like(corr_matrix, dtype=bool), k=1)
    corr_matrix_lower = corr_matrix.mask(mask)
    text_matrix = corr_matrix_lower.map(lambda val: f'{val:.2f}' if pd.notna(val) else '')

    fig = go.Figure(data=go.Heatmap(
        z=corr_matrix_lower, x=corr_cols, y=corr_cols, colorscale='RdBu', zmin=-1, zmax=1,
        hoverongaps=False, text=text_matrix, texttemplate="%{text}", textfont={"size":10}))
    fig.update_layout(title="전체 변수 간 상관관계 히트맵", xaxis_showgrid=False, yaxis_showgrid=False,
                      yaxis_autorange='reversed', margin=dict(l=40, r=40, t=80, b=40))
    return fig

def plot_rate_correlation_bars(df):
    corr_cols = [col for col in ['USD', 'EUR', 'JPY', 'CNY', 'KOR_BASE_RATE'] if col in df.columns]
    if len(corr_cols) < 2 or 'KOR_BASE_RATE' not in corr_cols: return go.Figure()

    corr_with_rate = df[corr_cols].corr()['KOR_BASE_RATE'].drop('KOR_BASE_RATE')
    fig = go.Figure(go.Bar(
        x=corr_with_rate.values, y=corr_with_rate.index, orientation='h',
        text=[f'{val:.3f}' for val in corr_with_rate.values], textposition='auto', marker_color='indianred'))
    fig.update_layout(title='한국 기준금리와 통화별 상관관계', xaxis_title='상관계수', yaxis_title='통화')
    return fig

def plot_currency_vs_rate(df, results_dict):
    currencies = [col for col in ['USD', 'EUR', 'JPY', 'CNY'] if col in df.columns]
    if not currencies or 'KOR_BASE_RATE' not in df.columns: return go.Figure()

    fig = make_subplots(rows=len(currencies), cols=1, subplot_titles=currencies, specs=[[{"secondary_y": True}] for _ in currencies])

    for i, currency in enumerate(currencies, start=1):
        fig.add_trace(go.Scatter(x=df['date'], y=df[currency], name=f'{currency} (Actual)', line=dict(color='cornflowerblue')), row=i, col=1, secondary_y=False)
        
        if currency in results_dict:
            all_models, _ = results_dict[currency]
            lstm_models = {k: v for k, v in all_models.items() if 'LSTM' in k}
            if lstm_models:
                best_lstm = max(lstm_models, key=lambda k: lstm_models[k]['R2'])
                idx, _, y_pred = lstm_models[best_lstm]['preds']
                fig.add_trace(go.Scatter(x=idx, y=y_pred, name=f'{currency} (LSTM)', line=dict(color='darkviolet', dash='dot')), row=i, col=1, secondary_y=False)

        fig.add_trace(go.Scatter(x=df['date'], y=df['KOR_BASE_RATE'], name='KOR Base Rate', line=dict(color='tomato', dash='dash')), row=i, col=1, secondary_y=True)

    fig.update_layout(title_text="통화 가치 vs 금리", height=350 * len(currencies))
    return fig

def plot_summary_table(summary_data):
    if not summary_data: return go.Figure()
    df = pd.DataFrame(summary_data).sort_values(by=['Currency', 'R2 Score'], ascending=[True, False])
    fig = go.Figure(data=[go.Table(header=dict(values=list(df.columns), fill_color='lightblue'), cells=dict(values=[df[c] for c in df.columns]))])
    fig.update_layout(title='성능 요약')
    return fig

def plot_performance_bars(summary_data):
    if not summary_data: return go.Figure()
    df = pd.DataFrame(summary_data)
    currencies = df['Currency'].unique()
    fig = make_subplots(rows=len(currencies), cols=2, subplot_titles=[f"{c} R2/RMSE" for c in currencies])
    for i, currency in enumerate(currencies):
        row = i + 1
        cdf = df[df['Currency'] == currency]
        fig.add_trace(go.Bar(x=cdf['R2 Score'], y=cdf['Model'], orientation='h', name='R2'), row=row, col=1)
        fig.add_trace(go.Bar(x=cdf['RMSE'], y=cdf['Model'], orientation='h', name='RMSE'), row=row, col=2)
    fig.update_layout(title='모델 성능 비교', height=250 * len(currencies), showlegend=False)
    return fig

def plot_rate_scatter(df):
    currencies = [col for col in ['USD', 'EUR', 'JPY', 'CNY'] if col in df.columns]
    if not currencies or 'KOR_BASE_RATE' not in df.columns: return go.Figure()
    
    rows = (len(currencies) + 1) // 2
    fig = make_subplots(rows=rows, cols=2, subplot_titles=currencies)
    
    for i, currency in enumerate(currencies):
        row, col = (i // 2) + 1, (i % 2) + 1
        fig.add_trace(go.Scatter(x=df['KOR_BASE_RATE'], y=df[currency], mode='markers', marker=dict(color='blue', opacity=0.6)), row=row, col=col)
        
    fig.update_layout(title="금리 vs 통화 산점도", height=350 * rows, showlegend=False)
    return fig

def plot_feature_importance(results_dict):
    valid_currencies = [curr for curr, (res, _) in results_dict.items() if res is not None]
    if not valid_currencies: return go.Figure()

    fig = make_subplots(rows=len(valid_currencies), cols=1, subplot_titles=[f'{c} Features' for c in valid_currencies])

    for i, currency in enumerate(valid_currencies):
        row = i + 1
        results, _ = results_dict[currency]
        
        tree_models = {k: v for k, v in results.items() if k in ['LGBM', 'CatBoost', 'XGBoost']}
        if not tree_models: continue
        
        best_name = max(tree_models, key=lambda k: tree_models[k]['R2'])
        model = tree_models[best_name]['model']
        
        try:
            if hasattr(model, 'feature_importances_'):
                imp = model.feature_importances_
                fig.add_trace(go.Bar(x=imp, orientation='h', name=best_name), row=row, col=1)
        except: pass

    fig.update_layout(title='피처 중요도', height=250 * len(valid_currencies), showlegend=False)
    return fig

if __name__ == '__main__':
    logging.basicConfig(level=logging.WARNING)
    print("🚀 [Interest] 금리 영향 분석 시작 (Optimized)")

    collections = ["USD", "EUR", "JPY", "CNY", "KOR_BASE_RATE"]
    raw_df = get_currency_data(collections)
    
    if not raw_df.empty:
        # [수정] config에서 경로 가져오기
        from config import OUTPUT_PATHS
        results_dir = os.environ.get("RESULTS_DIR", OUTPUT_PATHS["hong"])
        interest_dir = os.path.join(results_dir, "interest")
        os.makedirs(interest_dir, exist_ok=True)

        print("📊 시각화 생성 중 (HTML Only)...")
        plot_correlation_heatmap(raw_df).write_html(os.path.join(interest_dir, "correlation_heatmap.html"))
        plot_rate_correlation_bars(raw_df).write_html(os.path.join(interest_dir, "rate_corr_bar.html"))
        plot_rate_scatter(raw_df).write_html(os.path.join(interest_dir, "rate_scatter.html"))

        currencies_to_model = ["USD", "EUR", "JPY", "CNY"]
        all_results_for_plotting = {}
        summary_data = []

        for currency in currencies_to_model:
            if currency not in raw_df.columns: continue
            
            print(f"🤖 {currency} 모델링 중...")
            processed_df, feature_cols = prepare_data(raw_df.copy(), currency)
            if feature_cols is None: continue

            results, best_split = evaluate_models_with_split_optimization(processed_df, currency, feature_cols)
            if results:
                all_results_for_plotting[currency] = (results, best_split)
                for model_name, model_info in results.items():
                    optimizer = "N/A"
                    if 'LSTM' in model_name: optimizer = model_name.split('_')[1]
                    summary_data.append({'Currency': currency, 'Model': model_name, 'R2 Score': model_info['R2'], 'RMSE': model_info['RMSE'], 'Optimizer': optimizer})
            
            gc.collect()

        if all_results_for_plotting:
            print("💾 최종 결과 저장 중...")
            plot_currency_vs_rate(raw_df, all_results_for_plotting).write_html(os.path.join(interest_dir, "currency_rate.html"))
            plot_summary_table(summary_data).write_html(os.path.join(interest_dir, "summary_table.html"))
            plot_performance_bars(summary_data).write_html(os.path.join(interest_dir, "performance_bar.html"))
            plot_feature_importance(all_results_for_plotting).write_html(os.path.join(interest_dir, "feature_importance.html"))
            print("✅ [Interest] 분석 완료")
        else:
            print("⚠️ [Interest] 결과 없음")
    else:
        print("⚠️ [Interest] 데이터 로드 실패")