import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from pymongo import MongoClient
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import r2_score, mean_squared_error
from functools import reduce

# 머신러닝/딥러닝 라이브러리
import lightgbm as lgb
import catboost as cb
import xgboost as xgb
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from tensorflow.keras.optimizers import Adam, AdamW

# ===============================
# 1. MongoDB 연결 및 데이터 통합 함수
# ===============================
import os
MONGO_URI = os.environ.get("MONGO_URI")
DB_NAME = os.environ.get("DB_NAME")

def get_currency_data(collections, db_name=DB_NAME, connection_string=MONGO_URI):
    client = MongoClient(connection_string)
    db = client[db_name]
    dfs = []
    for col in collections:
        collection = db[col.upper()]
        df = pd.DataFrame(list(collection.find({}, {"_id": 0, "date": 1, "rate": 1})))
        if df.empty:
            print(f"경고: '{col}' 컬렉션에 데이터가 없습니다.")
            continue
        df["date"] = pd.to_datetime(df["date"])
        df = df.rename(columns={"rate": col.upper()})
        dfs.append(df)
    client.close()
    if not dfs:
        return pd.DataFrame()
    final_df = reduce(lambda left, right: pd.merge(left, right, on='date', how='outer'), dfs)
    final_df = final_df.sort_values(by='date').reset_index(drop=True)
    if 'KOR_BASE_RATE' in final_df.columns:
        final_df['KOR_BASE_RATE'] = final_df['KOR_BASE_RATE'].fillna(method='ffill')
    final_df.dropna(inplace=True)
    return final_df

# ===============================
# 2. 데이터 전처리
# ===============================
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

# ===============================
# 3. 모델 생성 함수
# ===============================
def create_lstm_model(input_shape, optimizer='adam'):
    model = Sequential([
        LSTM(50, activation='relu', input_shape=input_shape),
        Dense(1)
    ])
    model.compile(optimizer=optimizer, loss='mse')
    return model

# ===============================
# 4. 모델 학습 및 평가
# ===============================
def evaluate_models_with_split_optimization(df, target_currency, feature_columns):
    X = df[feature_columns]
    y = df[target_currency]
    if X.empty:
        return None, None
    overall_best_r2 = -np.inf
    overall_best_results = None
    best_split_ratio = None
    for split_ratio in [0.7, 0.8]:
        split_idx = int(len(X) * split_ratio)
        X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
        current_results = {}
        models = {
            'LGBM': lgb.LGBMRegressor(random_state=42),
            'CatBoost': cb.CatBoostRegressor(verbose=0, random_state=42),
            'XGBoost': xgb.XGBRegressor(random_state=42),
        }
        for name, model in models.items():
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            r2 = r2_score(y_test, y_pred)
            current_results[name] = {'R2': r2, 'RMSE': np.sqrt(mean_squared_error(y_test, y_pred)), 'model': model, 'preds': (y_test.index, y_test, y_pred)}
        X_train_lstm = np.reshape(X_train.values, (X_train.shape[0], 1, X_train.shape[1]))
        X_test_lstm = np.reshape(X_test.values, (X_test.shape[0], 1, X_test.shape[1]))
        for optimizer_name in ['Adam', 'AdamW']:
            opt = Adam() if optimizer_name == 'Adam' else AdamW()
            lstm_model = create_lstm_model((X_train_lstm.shape[1], X_train_lstm.shape[2]), optimizer=opt)
            lstm_model.fit(X_train_lstm, y_train, epochs=50, batch_size=32, verbose=0)
            y_pred_lstm = lstm_model.predict(X_test_lstm).flatten()
            r2_lstm = r2_score(y_test, y_pred_lstm)
            model_name = f'LSTM_{optimizer_name}'
            current_results[model_name] = {'R2': r2_lstm, 'RMSE': np.sqrt(mean_squared_error(y_test, y_pred_lstm)), 'model': lstm_model, 'preds': (y_test.index, y_test, y_pred_lstm)}
        current_best_model_name = max(current_results, key=lambda k: current_results[k]['R2'])
        current_max_r2 = current_results[current_best_model_name]['R2']
        if current_max_r2 > overall_best_r2:
            overall_best_r2 = current_max_r2
            overall_best_results = current_results
            best_split_ratio = split_ratio
    return overall_best_results, best_split_ratio

# ===============================
# 5. 시각화
# ===============================
import os

# 예시 함수명 plot_correlation_heatmap, plot_predictions 등에서 아래처럼 사용
def plot_correlation_heatmap(df, feature_col_name):
    results_dir = os.environ.get("RESULTS_DIR", "results")
    interest_dir = os.path.join(results_dir, "interest")
    os.makedirs(interest_dir, exist_ok=True)
    # ...existing code...
    # fig.write_html(os.path.join(interest_dir, "correlation_heatmap_basic.html"))
    # fig.write_image(os.path.join(interest_dir, "correlation_heatmap_basic.png"), scale=2)
    # ...기존 plotly 저장 코드에서 위 경로로 저장하도록 변경...
def plot_correlation_heatmap(df):
    ordered_cols = ['KOR_BASE_RATE', 'USD', 'EUR', 'JPY', 'CNY']
    corr_cols = [col for col in ordered_cols if col in df.columns]
    
    if len(corr_cols) < 2:
        return go.Figure()

    corr_matrix = df[corr_cols].corr()
    
    mask = np.triu(np.ones_like(corr_matrix, dtype=bool), k=1)
    corr_matrix_lower = corr_matrix.mask(mask)

    text_matrix = corr_matrix_lower.applymap(lambda val: f'{val:.2f}' if pd.notna(val) else '')

    fig = go.Figure(data=go.Heatmap(
        z=corr_matrix_lower,
        x=corr_cols,
        y=corr_cols,
        colorscale='RdBu',
        zmin=-1, zmax=1,
        hoverongaps=False,
        text=text_matrix,
        texttemplate="%{text}",
        textfont={"size":10}
    ))

    fig.update_layout(
        title="전체 변수 간 상관관계 히트맵 (KOR_BASE_RATE 기준 정렬)",
        xaxis_showgrid=False,
        yaxis_showgrid=False,
        yaxis_autorange='reversed',
        margin=dict(l=40, r=40, t=80, b=40)
    )
    return fig

def plot_rate_correlation_bars(df):
    corr_cols = [col for col in ['USD', 'EUR', 'JPY', 'CNY', 'KOR_BASE_RATE'] if col in df.columns]
    if len(corr_cols) < 2 or 'KOR_BASE_RATE' not in corr_cols:
        return go.Figure()

    corr_with_rate = df[corr_cols].corr()['KOR_BASE_RATE'].drop('KOR_BASE_RATE')

    fig = go.Figure(go.Bar(
        x=corr_with_rate.values,
        y=corr_with_rate.index,
        orientation='h',
        text=[f'{val:.3f}' for val in corr_with_rate.values],
        textposition='auto',
        marker_color='indianred'
    ))

    fig.update_layout(
        title='한국 기준금리(KOR_BASE_RATE)와 통화별 상관관계',
        xaxis_title='상관계수',
        yaxis_title='통화',
        yaxis=dict(autorange="reversed"),
        margin=dict(l=50, r=50, t=80, b=50)
    )
    return fig


def plot_currency_vs_rate(df, results_dict):
    currencies = [col for col in ['USD', 'EUR', 'JPY', 'CNY'] if col in df.columns]
    if not currencies or 'KOR_BASE_RATE' not in df.columns:
        return go.Figure()

    fig = make_subplots(
        rows=len(currencies), cols=1, subplot_titles=currencies,
        specs=[[{"secondary_y": True}] for _ in currencies]
    )

    for i, currency in enumerate(currencies, start=1):
        fig.add_trace(
            go.Scatter(x=df['date'], y=df[currency], name=f'{currency} (Actual)', line=dict(color='cornflowerblue')),
            row=i, col=1, secondary_y=False
        )
        
        if currency in results_dict:
            all_models, _ = results_dict[currency]
            lstm_models = {k: v for k, v in all_models.items() if 'LSTM' in k}
            if lstm_models:
                best_lstm_name = max(lstm_models, key=lambda k: lstm_models[k]['R2'])
                idx, _, y_pred_lstm = lstm_models[best_lstm_name]['preds']
                fig.add_trace(
                    go.Scatter(x=idx, y=y_pred_lstm, name=f'{currency} (LSTM Predicted)', line=dict(color='darkviolet', dash='dot')),
                    row=i, col=1, secondary_y=False
                )

        fig.add_trace(
            go.Scatter(x=df['date'], y=df['KOR_BASE_RATE'], name='KOR Base Rate', line=dict(color='tomato', dash='dash')),
            row=i, col=1, secondary_y=True
        )

        fig.update_yaxes(title_text=f"<b>{currency}</b> Value", row=i, col=1, secondary_y=False)
        fig.update_yaxes(title_text="<b>KOR Base Rate</b> (%)", row=i, col=1, secondary_y=True)

    fig.update_layout(
        title_text="통화 가치, 기준금리 및 LSTM 예측 시계열 비교",
        height=350 * len(currencies),
        legend_tracegroupgap=180
    )
    return fig

def plot_summary_table(summary_data):
    if not summary_data:
        return go.Figure()
    df_summary = pd.DataFrame(summary_data)
    df_summary = df_summary.sort_values(by=['Currency', 'R2 Score'], ascending=[True, False])
    fig = go.Figure(data=[go.Table(header=dict(values=list(df_summary.columns), fill_color='lightblue', align='center'), cells=dict(values=[df_summary[c] for c in df_summary.columns], align='center'))])
    fig.update_layout(title='전체 모델 성능 요약표')
    return fig

def plot_performance_bars(summary_data):
    if not summary_data:
        return go.Figure()
    df_summary = pd.DataFrame(summary_data)
    df_summary['R2 Score'] = pd.to_numeric(df_summary['R2 Score'])
    df_summary['RMSE'] = pd.to_numeric(df_summary['RMSE'])
    currencies = df_summary['Currency'].unique()
    fig = make_subplots(rows=len(currencies), cols=2, subplot_titles=[item for currency in currencies for item in (f"{currency} R2 Score", f"{currency} RMSE")])
    for i, currency in enumerate(currencies):
        row = i + 1
        currency_df = df_summary[df_summary['Currency'] == currency].copy()
        r2_df = currency_df.sort_values('R2 Score', ascending=True)
        fig.add_trace(go.Bar(x=r2_df['R2 Score'], y=r2_df['Model'], orientation='h', text=r2_df['R2 Score'], texttemplate='%{x:.3f}', textposition='auto', marker_color='skyblue'), row=row, col=1)
        rmse_df = currency_df.sort_values('RMSE', ascending=False)
        fig.add_trace(go.Bar(x=rmse_df['RMSE'], y=rmse_df['Model'], orientation='h', text=rmse_df['RMSE'], texttemplate='%{x:.2f}', textposition='auto', marker_color='lightsalmon'), row=row, col=2)
    fig.update_layout(title_text='통화별 모델 성능 비교 (R2 Score & RMSE)', height=250 * len(currencies), showlegend=False, bargap=0.1)
    fig.update_yaxes(automargin=True)
    return fig

def plot_rate_scatter(df):
    currencies = [col for col in ['USD', 'EUR', 'JPY', 'CNY'] if col in df.columns]
    if not currencies or 'KOR_BASE_RATE' not in df.columns:
        return go.Figure()

    fig = make_subplots(rows=2, cols=2, subplot_titles=currencies)
    
    positions = [(1, 1), (1, 2), (2, 1), (2, 2)]
    for i, currency in enumerate(currencies):
        row, col = positions[i]
        fig.add_trace(
            go.Scatter(
                x=df['KOR_BASE_RATE'], 
                y=df[currency], 
                mode='markers',
                marker=dict(color='blue', opacity=0.6)
            ),
            row=row, col=col
        )
        fig.update_xaxes(title_text="KOR Base Rate (%)", row=row, col=col)
        fig.update_yaxes(title_text=currency, row=row, col=col)

    fig.update_layout(
        title_text="한국 기준금리와 주요 통화 간 산점도",
        height=700,
        showlegend=False,
        margin=dict(l=50, r=50, t=80, b=50)
    )
    return fig

def plot_feature_importance(results_dict):
    valid_currencies = [curr for curr, (res, _) in results_dict.items() if res is not None]
    if not valid_currencies:
        return go.Figure()

    fig = make_subplots(
        rows=len(valid_currencies), cols=1, 
        subplot_titles=[f'{currency} Feature Importance' for currency in valid_currencies],
        vertical_spacing=0.15
    )

    for i, currency in enumerate(valid_currencies):
        row = i + 1
        results, _ = results_dict[currency]
        
        tree_models = {name: info for name, info in results.items() if name in ['LGBM', 'CatBoost', 'XGBoost']}
        if not tree_models:
            continue
            
        best_model_name = max(tree_models, key=lambda name: tree_models[name]['R2'])
        best_model = tree_models[best_model_name]['model']

        if hasattr(best_model, 'feature_importances_'):
            importances = best_model.feature_importances_
            if hasattr(best_model, 'feature_name_'):
                feature_names = best_model.feature_name_
            elif hasattr(best_model, 'feature_names_'):
                feature_names = best_model.feature_names_
            else:
                if hasattr(best_model, 'feature_names_in_'):
                    feature_names = best_model.feature_names_in_
                else:
                    feature_names = [f'feature_{j}' for j in range(len(importances))]
        else:
            continue

        imp_df = pd.DataFrame({'feature': feature_names, 'importance': importances})
        imp_df = imp_df.sort_values(by='importance', ascending=True)

        fig.add_trace(go.Bar(
            x=imp_df['importance'],
            y=imp_df['feature'],
            orientation='h',
            text=imp_df['importance'],
            texttemplate='%{x}',
            textposition='auto'
        ), row=row, col=1)
        
        fig.update_yaxes(title_text=f"{best_model_name} (Best)", row=row, col=1)

    fig.update_layout(
        title_text='통화별 최적 모델의 피처 중요도 (금리 포함)',
        height=250 * len(valid_currencies),
        showlegend=False
    )
    return fig

# ===============================
# 6. 메인 파이프라인
# ===============================
if __name__ == '__main__':
    import os
    collections = ["USD", "EUR", "JPY", "CNY", "KOR_BASE_RATE"]
    raw_df = get_currency_data(collections)
    if not raw_df.empty:
        raw_df = raw_df[(raw_df['date'] >= '2016-01-01') & (raw_df['date'] <= '2025-12-31')].copy()
        results_dir = os.environ.get("RESULTS_DIR", "results")
        interest_dir = os.path.join(results_dir, "interest")
        os.makedirs(interest_dir, exist_ok=True)

        # --- 초기 데이터 탐색 시각화 ---
        correlation_fig = plot_correlation_heatmap(raw_df)
        correlation_fig.write_html(os.path.join(interest_dir, "correlation_heatmap.html"))
        try:
            correlation_fig.write_image(os.path.join(interest_dir, "correlation_heatmap.png"), scale=2)
        except Exception as e:
            print(f"[경고] correlation_heatmap png 저장 실패: {e}")

        rate_corr_bar_fig = plot_rate_correlation_bars(raw_df)
        rate_corr_bar_fig.write_html(os.path.join(interest_dir, "rate_corr_bar.html"))
        try:
            rate_corr_bar_fig.write_image(os.path.join(interest_dir, "rate_corr_bar.png"), scale=2)
        except Exception as e:
            print(f"[경고] rate_corr_bar png 저장 실패: {e}")

        rate_scatter_fig = plot_rate_scatter(raw_df)
        rate_scatter_fig.write_html(os.path.join(interest_dir, "rate_scatter.html"))
        try:
            rate_scatter_fig.write_image(os.path.join(interest_dir, "rate_scatter.png"), scale=2)
        except Exception as e:
            print(f"[경고] rate_scatter png 저장 실패: {e}")

        # --- 통화별 모델링 및 결과 집계 ---
        currencies_to_model = ["USD", "EUR", "JPY", "CNY"]
        all_results_for_plotting = {}
        summary_data = []

        for currency in currencies_to_model:
            if currency not in raw_df.columns:
                continue
            processed_df, feature_cols = prepare_data(raw_df.copy(), currency)
            if feature_cols is None:
                continue

            results, best_split = evaluate_models_with_split_optimization(processed_df, currency, feature_cols)
            if results:
                all_results_for_plotting[currency] = (results, best_split)
                for model_name, model_info in results.items():
                    optimizer = "N/A"
                    if 'LSTM' in model_name:
                        optimizer = model_name.split('_')[1]
                    summary_data.append({'Currency': currency, 'Model': model_name, 'R2 Score': f"{model_info['R2']:.4f}", 'RMSE': f"{model_info['RMSE']:.2f}", 'Train/Test Split': f"{int(best_split*100)}:{int((1-best_split)*100)}", 'Optimizer': optimizer})

        # --- 모델링 결과 시각화 ---
        if all_results_for_plotting:
            currency_rate_fig = plot_currency_vs_rate(raw_df, all_results_for_plotting)
            summary_table_fig = plot_summary_table(summary_data)
            performance_bar_fig = plot_performance_bars(summary_data)
            feature_importance_fig = plot_feature_importance(all_results_for_plotting)

            currency_rate_fig.write_html(os.path.join(interest_dir, "currency_rate.html"))
            try:
                currency_rate_fig.write_image(os.path.join(interest_dir, "currency_rate.png"), scale=2)
            except Exception as e:
                print(f"[경고] currency_rate png 저장 실패: {e}")

            summary_table_fig.write_html(os.path.join(interest_dir, "summary_table.html"))
            try:
                summary_table_fig.write_image(os.path.join(interest_dir, "summary_table.png"), scale=2)
            except Exception as e:
                print(f"[경고] summary_table png 저장 실패: {e}")

            performance_bar_fig.write_html(os.path.join(interest_dir, "performance_bar.html"))
            try:
                performance_bar_fig.write_image(os.path.join(interest_dir, "performance_bar.png"), scale=2)
            except Exception as e:
                print(f"[경고] performance_bar png 저장 실패: {e}")

            feature_importance_fig.write_html(os.path.join(interest_dir, "feature_importance.html"))
            try:
                feature_importance_fig.write_image(os.path.join(interest_dir, "feature_importance.png"), scale=2)
            except Exception as e:
                print(f"[경고] feature_importance png 저장 실패: {e}")