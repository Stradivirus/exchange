import pandas as pd
import numpy as np
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

def get_feature_and_target_data(collections, feature_col_name, db_name=DB_NAME, connection_string=MONGO_URI):
    client = MongoClient(connection_string)
    db = client[db_name]
    dfs = []

    for col in collections:
        collection = db[col]
        doc = collection.find_one({}, {"_id": 0, "date": 1, "rate": 1, "value": 1})
        value_field = 'value' if doc and 'value' in doc else 'rate'
        df = pd.DataFrame(list(collection.find({}, {"_id": 0, "date": 1, value_field: 1})))
        
        if df.empty:
            print(f"경고: '{col}' 컬렉션에 데이터가 없습니다.")
            continue

        df["date"] = pd.to_datetime(df["date"])
        new_col_name = col.upper()
        df = df.rename(columns={value_field: new_col_name})
        dfs.append(df)
        
    client.close()

    if not dfs:
        return pd.DataFrame()

    final_df = reduce(lambda left, right: pd.merge(left, right, on='date', how='outer'), dfs)
    final_df = final_df.sort_values(by='date').reset_index(drop=True)
    
    if feature_col_name in final_df.columns:
        final_df[feature_col_name] = final_df[feature_col_name].fillna(method='ffill')

    final_df.dropna(inplace=True)
    return final_df

# ===============================
# 2. 데이터 전처리 및 모델링 함수
# ===============================
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
    model = Sequential([LSTM(50, activation='relu', input_shape=input_shape), Dense(1)])
    model.compile(optimizer=optimizer, loss='mse')
    return model

def evaluate_models_with_split_optimization(df, target_currency):
    feature_columns = [col for col in df.columns if col != target_currency]
    X = df[feature_columns]
    y = df[target_currency]
    if X.empty: return None, None
    overall_best_r2, overall_best_results, best_split_ratio = -np.inf, None, None
    for split_ratio in [0.7, 0.8]:
        split_idx = int(len(X) * split_ratio)
        X_train, X_test, y_train, y_test = X.iloc[:split_idx], X.iloc[split_idx:], y.iloc[:split_idx], y.iloc[split_idx:]
        current_results = {}
        models = {'LGBM': lgb.LGBMRegressor(random_state=42), 'CatBoost': cb.CatBoostRegressor(verbose=0, random_state=42), 'XGBoost': xgb.XGBRegressor(random_state=42)}
        for name, model in models.items():
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            r2 = r2_score(y_test, y_pred)
            current_results[name] = {'R2': r2, 'RMSE': np.sqrt(mean_squared_error(y_test, y_pred)), 'model': model, 'preds': (y_test.index, y_test, y_pred)}
        X_train_lstm, X_test_lstm = np.reshape(X_train.values, (X_train.shape[0], 1, X_train.shape[1])), np.reshape(X_test.values, (X_test.shape[0], 1, X_test.shape[1]))
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
            overall_best_r2, overall_best_results, best_split_ratio = current_max_r2, current_results, split_ratio
    return overall_best_results, best_split_ratio

# ===============================
# 5. 시각화
# ===============================
def plot_correlation_heatmap(df, feature_col_name):
    currencies = [col for col in ['USD', 'EUR', 'JPY', 'CNY'] if col in df.columns]
    corr_cols = [feature_col_name] + currencies
    if len(corr_cols) < 2: return go.Figure()

    corr_matrix = df[corr_cols].corr()
    mask = np.triu(np.ones_like(corr_matrix, dtype=bool), k=1)
    corr_matrix_lower = corr_matrix.mask(mask)
    text_matrix = corr_matrix_lower.applymap(lambda val: f'{val:.2f}' if pd.notna(val) else '')

    fig = go.Figure(data=go.Heatmap(
        z=corr_matrix_lower, x=corr_cols, y=corr_cols, colorscale='RdBu', zmin=-1, zmax=1,
        hoverongaps=False, text=text_matrix, texttemplate="%{text}", textfont={"size":10}))
    fig.update_layout(title="수출입물가지수와 통화 간 상관관계 히트맵", xaxis_showgrid=False, yaxis_showgrid=False,
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
    """
    [수정] 각 통화별 실제 값, 최적 모델 예측 값, 그리고 수출입물가지수를 함께 시각화합니다.
    """
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

        # 기본 Y축: 실제값과 예측값
        fig.add_trace(go.Scatter(x=full_df['date'], y=full_df[currency], mode='lines', name=f'{currency} (Actual)', line=dict(color='cornflowerblue')), row=row, col=1, secondary_y=False)
        fig.add_trace(go.Scatter(x=idx, y=y_pred, mode='lines', name=f'{currency} (Predicted) - {best_model_name}', line=dict(color='darkviolet', dash='dot')), row=row, col=1, secondary_y=False)
        
        # [추가] 보조 Y축: 수출입물가지수
        fig.add_trace(go.Scatter(x=full_df['date'], y=full_df[feature_col_name], name=feature_col_name, line=dict(color='tomato', dash='dash')), row=row, col=1, secondary_y=True)

        # Train/Test 분할선
        fig.add_vline(x=split_date, line_width=2, line_dash="dash", line_color="grey", row=row, col=1)
        
        # Y축 제목 설정
        fig.update_yaxes(title_text=f"<b>{currency}</b> Value", row=row, col=1, secondary_y=False)
        fig.update_yaxes(title_text=f"<b>{feature_col_name}</b>", row=row, col=1, secondary_y=True)

    fig.update_layout(title_text='통화별 최적 모델 예측 결과 및 수출입물가지수 비교', height=350*len(valid_currencies), showlegend=True, legend_tracegroupgap=180)
    return fig

def plot_summary_table(summary_data):
    if not summary_data: return go.Figure()
    df_summary = pd.DataFrame(summary_data).sort_values(by=['Currency', 'R2 Score'], ascending=[True, False])
    fig = go.Figure(data=[go.Table(header=dict(values=list(df_summary.columns), fill_color='lightblue', align='center'), cells=dict(values=[df_summary[c] for c in df_summary.columns], align='center'))])
    fig.update_layout(title='전체 모델 성능 요약표')
    return fig

def plot_performance_bars(summary_data):
    if not summary_data: return go.Figure()
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

# ===============================
# 6. 메인 파이프라인
# ===============================
if __name__ == '__main__':
    FEATURE_COLLECTION = 'export_import_price_index'
    TARGET_COLLECTIONS = ['USD', 'EUR', 'JPY', 'CNY']
    ALL_COLLECTIONS = [FEATURE_COLLECTION] + TARGET_COLLECTIONS
    FEATURE_COL_NAME_UPPER = FEATURE_COLLECTION.upper()
    raw_df = get_feature_and_target_data(ALL_COLLECTIONS, FEATURE_COL_NAME_UPPER)

    if not raw_df.empty:
        raw_df = raw_df[(raw_df['date'] >= '2015-01-01') & (raw_df['date'] <= '2025-12-31')].copy()
        results_dir = os.environ.get("RESULTS_DIR", "results")
        expimp_dir = os.path.join(results_dir, "expimp")
        os.makedirs(expimp_dir, exist_ok=True)

        # 1. 상관관계 분석 시각화
        correlation_heatmap_fig = plot_correlation_heatmap(raw_df, FEATURE_COL_NAME_UPPER)
        correlation_heatmap_fig.write_html(os.path.join(expimp_dir, "expimp_correlation_heatmap.html"))
        try:
            correlation_heatmap_fig.write_image(os.path.join(expimp_dir, "expimp_correlation_heatmap.png"), scale=2)
        except Exception as e:
            print(f"[경고] heatmap png 저장 실패: {e}")

        correlation_bar_fig = plot_correlation_bars(raw_df, FEATURE_COL_NAME_UPPER)
        correlation_bar_fig.write_html(os.path.join(expimp_dir, "expimp_correlation_bar.html"))
        try:
            correlation_bar_fig.write_image(os.path.join(expimp_dir, "expimp_correlation_bar.png"), scale=2)
        except Exception as e:
            print(f"[경고] bar png 저장 실패: {e}")

        all_results_for_plotting = {}
        summary_data = []

        # 2. 통화별 모델링 루프
        for currency in TARGET_COLLECTIONS:
            if currency not in raw_df.columns:
                continue
            processed_df = prepare_data(raw_df, target_currency=currency, feature_cols=[FEATURE_COL_NAME_UPPER])
            results, best_split = evaluate_models_with_split_optimization(processed_df, target_currency=currency)
            if results:
                all_results_for_plotting[currency] = (results, best_split)
                for model_name, model_info in results.items():
                    optimizer = "N/A"
                    if 'LSTM' in model_name:
                        optimizer = model_name.split('_')[1]
                    summary_data.append({'Currency': currency, 'Model': model_name, 'R2 Score': f"{model_info['R2']:.4f}", 'RMSE': f"{model_info['RMSE']:.2f}", 'Train/Test Split': f"{int(best_split*100)}:{int((1-best_split)*100)}", 'Optimizer': optimizer})

        # 3. 모델링 결과 시각화
        predictions_fig = plot_predictions(all_results_for_plotting, raw_df, FEATURE_COL_NAME_UPPER)
        summary_table_fig = plot_summary_table(summary_data)
        performance_bar_fig = plot_performance_bars(summary_data)

        predictions_fig.write_html(os.path.join(expimp_dir, "expimp_predictions.html"))
        try:
            predictions_fig.write_image(os.path.join(expimp_dir, "expimp_predictions.png"), scale=2)
        except Exception as e:
            print(f"[경고] predictions png 저장 실패: {e}")

        summary_table_fig.write_html(os.path.join(expimp_dir, "expimp_summary_table.html"))
        try:
            summary_table_fig.write_image(os.path.join(expimp_dir, "expimp_summary_table.png"), scale=2)
        except Exception as e:
            print(f"[경고] summary_table png 저장 실패: {e}")

        performance_bar_fig.write_html(os.path.join(expimp_dir, "expimp_performance_bar.html"))
        try:
            performance_bar_fig.write_image(os.path.join(expimp_dir, "expimp_performance_bar.png"), scale=2)
        except Exception as e:
            print(f"[경고] performance_bar png 저장 실패: {e}")