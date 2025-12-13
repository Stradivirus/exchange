import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
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

def get_feature_and_target_data(collections, feature_col_name, db_name=DB_NAME, connection_string=MONGO_URI):
    client = MongoClient(connection_string)
    db = client[db_name]
    dfs = []

    print("🔍 [ExpImp] MongoDB 데이터 조회 시작...")
    start_date_limit = pd.Timestamp.now() - pd.DateOffset(years=5)

    for col in collections:
        collection = db[col]
        doc = collection.find_one({}, {"_id": 0, "date": 1, "rate": 1, "value": 1})
        value_field = 'value' if doc and 'value' in doc else 'rate'
        
        data = list(collection.find({}, {"_id": 0, "date": 1, value_field: 1}))
        if not data:
            print(f"⚠️ [ExpImp] '{col}' 데이터 없음")
            continue
            
        df = pd.DataFrame(data)
        if df.empty or 'date' not in df.columns: continue

        df["date"] = pd.to_datetime(df["date"])
        df = df[df["date"] >= start_date_limit]
        
        if df.empty: continue

        new_col_name = col.upper()
        df = df.rename(columns={value_field: new_col_name})
        dfs.append(df)
        
    client.close()

    if not dfs:
        return pd.DataFrame()

    final_df = reduce(lambda left, right: pd.merge(left, right, on='date', how='outer'), dfs)
    final_df = final_df.sort_values(by='date').reset_index(drop=True)
    
    if feature_col_name in final_df.columns:
        final_df[feature_col_name] = final_df[feature_col_name].ffill()

    final_df.dropna(inplace=True)
    return final_df

def prepare_data(df, target_currency, feature_cols, n_lags=5):
    df = df.copy()
    if 'date' in df.columns:
        df.set_index('date', inplace=True)
    df.sort_index(inplace=True)
    for i in range(1, n_lags + 1):
        df[f'{target_currency}_lag_{i}'] = df[target_currency].shift(i)
    df.dropna(inplace=True)
    all_feature_cols = [col for col in df.columns if col != target_currency]
    if not all_feature_cols:
        return df
    scaler = MinMaxScaler()
    df[all_feature_cols] = scaler.fit_transform(df[all_feature_cols])
    return df

def create_lstm_model(input_shape, optimizer='adam'):
    model = Sequential([
        LSTM(30, activation='relu', input_shape=input_shape),
        Dense(1)
    ])
    model.compile(optimizer=optimizer, loss='mse')
    return model

def evaluate_models_with_split_optimization(df, target_currency):
    feature_columns = [col for col in df.columns if col != target_currency]
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
        'XGBoost': xgb.XGBRegressor(random_state=42, n_jobs=N_JOBS_LIMIT)
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

def plot_correlation_heatmap(df, feature_col_name):
    currencies = [col for col in ['USD', 'EUR', 'JPY', 'CNY'] if col in df.columns]
    corr_cols = [feature_col_name] + currencies
    if len(corr_cols) < 2: return go.Figure()

    corr_matrix = df[corr_cols].corr()
    mask = np.triu(np.ones_like(corr_matrix, dtype=bool), k=1)
    corr_matrix_lower = corr_matrix.mask(mask)
    text_matrix = corr_matrix_lower.map(lambda val: f'{val:.2f}' if pd.notna(val) else '')

    fig = go.Figure(data=go.Heatmap(
        z=corr_matrix_lower, x=corr_cols, y=corr_cols, colorscale='RdBu', zmin=-1, zmax=1,
        hoverongaps=False, text=text_matrix, texttemplate="%{text}", textfont={"size":10}))
    fig.update_layout(title="수출입물가지수와 통화 간 상관관계", xaxis_showgrid=False, yaxis_showgrid=False,
                      yaxis_autorange='reversed', margin=dict(l=40, r=40, t=80, b=40))
    return fig

def plot_correlation_bars(df, feature_col_name):
    currencies = [col for col in ['USD', 'EUR', 'JPY', 'CNY'] if col in df.columns]
    if not currencies or feature_col_name not in df.columns: return go.Figure()
    correlations = {currency: df[currency].corr(df[feature_col_name]) for currency in currencies}
    corr_df = pd.DataFrame(list(correlations.items()), columns=['Currency', 'Correlation']).sort_values(by='Correlation', ascending=True)
    fig = px.bar(corr_df, x='Correlation', y='Currency', orientation='h', text='Correlation', title=f'통화별 {feature_col_name} 상관계수')
    fig.update_traces(texttemplate='%{text:.3f}', textposition='outside')
    fig.update_layout(xaxis_title="상관계수", yaxis_title="통화", showlegend=False, xaxis=dict(range=[-1, 1]))
    return fig

def plot_predictions(results_dict, full_df, feature_col_name):
    valid_currencies = [curr for curr, (res, _) in results_dict.items() if res is not None]
    if not valid_currencies: return go.Figure()

    fig = make_subplots(
        rows=len(valid_currencies), cols=1,
        subplot_titles=[f'{currency} 예측' for currency in valid_currencies],
        vertical_spacing=0.1,
        specs=[[{"secondary_y": True}] for _ in valid_currencies]
    )

    for i, currency in enumerate(valid_currencies):
        row = i + 1
        results, best_split = results_dict[currency]
        best_model_name = max(results, key=lambda k: results[k]['R2'])
        idx, _, y_pred = results[best_model_name]['preds']
        split_date = idx[0]

        fig.add_trace(go.Scatter(x=full_df['date'], y=full_df[currency], mode='lines', name=f'{currency} (Actual)', line=dict(color='cornflowerblue')), row=row, col=1, secondary_y=False)
        fig.add_trace(go.Scatter(x=idx, y=y_pred, mode='lines', name=f'{currency} (Pred) - {best_model_name}', line=dict(color='darkviolet', dash='dot')), row=row, col=1, secondary_y=False)
        fig.add_trace(go.Scatter(x=full_df['date'], y=full_df[feature_col_name], name=feature_col_name, line=dict(color='tomato', dash='dash')), row=row, col=1, secondary_y=True)
        fig.add_vline(x=split_date, line_width=2, line_dash="dash", line_color="grey", row=row, col=1)

    fig.update_layout(title_text='통화별 예측 및 수출입물가지수', height=350*len(valid_currencies), showlegend=True)
    return fig

def plot_summary_table(summary_data):
    if not summary_data: return go.Figure()
    df_summary = pd.DataFrame(summary_data).sort_values(by=['Currency', 'R2 Score'], ascending=[True, False])
    fig = go.Figure(data=[go.Table(header=dict(values=list(df_summary.columns), fill_color='lightblue', align='center'), cells=dict(values=[df_summary[c] for c in df_summary.columns], align='center'))])
    fig.update_layout(title='성능 요약')
    return fig

def plot_performance_bars(summary_data):
    if not summary_data: return go.Figure()
    df_summary = pd.DataFrame(summary_data)
    df_summary['R2 Score'] = pd.to_numeric(df_summary['R2 Score'])
    currencies = df_summary['Currency'].unique()
    fig = make_subplots(rows=len(currencies), cols=1, subplot_titles=[f"{currency} R2 Score" for currency in currencies])
    for i, currency in enumerate(currencies):
        row = i + 1
        currency_df = df_summary[df_summary['Currency'] == currency].copy()
        r2_df = currency_df.sort_values('R2 Score', ascending=True)
        fig.add_trace(go.Bar(x=r2_df['R2 Score'], y=r2_df['Model'], orientation='h', text=r2_df['R2 Score'], texttemplate='%{x:.3f}', textposition='auto'), row=row, col=1)
    fig.update_layout(title_text='통화별 모델 성능 비교', height=200 * len(currencies), showlegend=False)
    return fig

if __name__ == '__main__':
    logging.basicConfig(level=logging.WARNING)
    print("🚀 [ExpImp] 수출입 지표 분석 시작 (Optimized)")

    FEATURE_COLLECTION = 'export_import_price_index'
    TARGET_COLLECTIONS = ['USD', 'EUR', 'JPY', 'CNY']
    ALL_COLLECTIONS = [FEATURE_COLLECTION] + TARGET_COLLECTIONS
    FEATURE_COL_NAME_UPPER = FEATURE_COLLECTION.upper()
    
    raw_df = get_feature_and_target_data(ALL_COLLECTIONS, FEATURE_COL_NAME_UPPER)

    if not raw_df.empty:
        # [수정] config에서 경로 가져오기
        from config import OUTPUT_PATHS
        results_dir = os.environ.get("RESULTS_DIR", OUTPUT_PATHS["hong"])
        expimp_dir = os.path.join(results_dir, "expimp")
        os.makedirs(expimp_dir, exist_ok=True)

        print("📊 시각화 생성 중 (HTML Only)...")
        plot_correlation_heatmap(raw_df, FEATURE_COL_NAME_UPPER).write_html(os.path.join(expimp_dir, "expimp_correlation_heatmap.html"))
        plot_correlation_bars(raw_df, FEATURE_COL_NAME_UPPER).write_html(os.path.join(expimp_dir, "expimp_correlation_bar.html"))

        all_results_for_plotting = {}
        summary_data = []

        for currency in TARGET_COLLECTIONS:
            if currency not in raw_df.columns: continue
            
            print(f"🤖 {currency} 모델링 중...")
            processed_df = prepare_data(raw_df, target_currency=currency, feature_cols=[FEATURE_COL_NAME_UPPER])
            results, best_split = evaluate_models_with_split_optimization(processed_df, target_currency=currency)
            
            if results:
                all_results_for_plotting[currency] = (results, best_split)
                for model_name, model_info in results.items():
                    optimizer = "N/A"
                    if 'LSTM' in model_name: optimizer = model_name.split('_')[1]
                    summary_data.append({'Currency': currency, 'Model': model_name, 'R2 Score': f"{model_info['R2']:.4f}", 'RMSE': f"{model_info['RMSE']:.2f}", 'Train/Test Split': f"{int(best_split*100)}:{int((1-best_split)*100)}", 'Optimizer': optimizer})
            
            gc.collect()

        if summary_data:
            print("💾 최종 결과 저장 중...")
            plot_predictions(all_results_for_plotting, raw_df, FEATURE_COL_NAME_UPPER).write_html(os.path.join(expimp_dir, "expimp_predictions.html"))
            plot_summary_table(summary_data).write_html(os.path.join(expimp_dir, "expimp_summary_table.html"))
            plot_performance_bars(summary_data).write_html(os.path.join(expimp_dir, "expimp_performance_bar.html"))
            print("✅ [ExpImp] 분석 완료")
        else:
            print("⚠️ [ExpImp] 결과 데이터 없음")
    else:
        print("⚠️ [ExpImp] 데이터 로드 실패")