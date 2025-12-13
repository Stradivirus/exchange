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
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from tensorflow.keras.optimizers import Adam, AdamW

import os
import logging

# ===============================
# 2. 데이터 전처리
# ===============================
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
    if not feature_cols:
        return df
    scaler = MinMaxScaler()
    df[feature_cols] = scaler.fit_transform(df[feature_cols])
    return df

# 머신러닝/딥러닝 라이브러리



MONGO_URI = os.environ.get("MONGO_URI")
DB_NAME = os.environ.get("DB_NAME")

def get_currency_data(collections, db_name=DB_NAME, connection_string=MONGO_URI):
    client = MongoClient(connection_string)
    db = client[db_name]
    dfs = []
    for col_name in collections:
        col = db[col_name]
        doc = col.find_one({}, {"_id": 0, "date": 1, "rate": 1, "value": 1,"price": 1,"close": 1})
        if doc is None:
            print(f"경고: '{col_name}' 컬렉션에 데이터가 없습니다. 건너뜁니다.")
            continue
        # 우선순위: value > rate > close > price > open
        for candidate in ['value', 'rate', 'close', 'price']:
            if candidate in doc:
                value_field = candidate
                break
        else:
            print(f"경고: '{col_name}' 컬렉션에서 사용할 수 있는 값 필드가 없습니다. (value/rate/close/price)")
            continue
        df = pd.DataFrame(list(col.find({}, {"_id": 0, "date": 1, value_field: 1})))
        if df.empty:
            continue
        df["date"] = pd.to_datetime(df["date"])
        # 컬럼명은 소문자로 변환하되, 컬렉션명은 그대로 컬럼명으로 사용
        df = df.rename(columns={value_field: col_name})
        df.columns = [c.lower() if c != col_name else col_name for c in df.columns]
        dfs.append(df)
    if not dfs:
        return pd.DataFrame()
    # date 기준으로 병합
    df_merged = reduce(lambda left, right: pd.merge(left, right, on='date', how='outer'), dfs)
    df_merged = df_merged.sort_values(by='date').reset_index(drop=True)
    # 컬럼별 NaN 비율 출력 (진단용)
    print("[진단] 병합 후 컬럼별 NaN 비율:")
    print(df_merged.isna().mean())
    print("[진단] 병합 결과 상위 20개:")
    print(df_merged.head(20))
    print("[진단] 병합 결과 하위 20개:")
    print(df_merged.tail(20))
    return df_merged

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
def evaluate_models_with_split_optimization(df, target_currency):
    feature_columns = [col for col in df.columns if col != target_currency.lower()]
    X = df[feature_columns]
    y = df[target_currency.lower()]

    if X.empty:
        return None, None

    overall_best_r2, overall_best_results, best_split_ratio = -np.inf, None, None
    for split_ratio in [0.7, 0.8]:
        split_idx = int(len(X) * split_ratio)
        X_train, X_test, y_train, y_test = X.iloc[:split_idx], X.iloc[split_idx:], y.iloc[:split_idx], y.iloc[split_idx:]
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
        
        input_shape_for_lstm = (X_train_lstm.shape[1], X_train_lstm.shape[2])
        
        for optimizer_name in ['Adam', 'AdamW']:
            opt = Adam() if optimizer_name == 'Adam' else AdamW()
            lstm_model = create_lstm_model(input_shape_for_lstm, optimizer=opt)
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
def plot_predictions(results_dict, full_df):
    valid_currencies = [curr for curr, (res, _) in results_dict.items() if res is not None]
    if not valid_currencies: return go.Figure()

    fig = make_subplots(rows=len(valid_currencies), cols=1, subplot_titles=valid_currencies, vertical_spacing=0.1)
    full_df.columns = full_df.columns.str.lower()

    for i, currency in enumerate(valid_currencies):
        results, best_split = results_dict[currency]
        best_model_name = max(results, key=lambda k: results[k]['R2'])
        idx, _, y_pred = results[best_model_name]['preds']
        split_date = idx[0]
        
        fig.add_trace(go.Scatter(x=full_df['date'], y=full_df[currency.lower()], mode='lines', name=f'{currency} (Actual)'), row=i+1, col=1)
        fig.add_trace(go.Scatter(x=idx, y=y_pred, mode='lines', name=f'{currency} (Predicted) - {best_model_name}'), row=i+1, col=1)
        fig.add_vline(x=split_date, line_width=2, line_dash="dash", line_color="grey", row=i+1, col=1)
        
    fig.update_layout(title_text='통화별 최적 모델 예측 결과 (Train/Test 분할 표시)', height=300*len(valid_currencies), showlegend=True)
    return fig

def plot_summary_table(summary_data):
    if not summary_data: return go.Figure()
    df_summary = pd.DataFrame(summary_data)
    fig = go.Figure(data=[go.Table(header=dict(values=list(df_summary.columns), fill_color='lightblue', align='center'), cells=dict(values=[df_summary[c] for c in df_summary.columns], align='center'))])
    fig.update_layout(title='모델 성능 요약')
    return fig

def plot_performance_bars(summary_data):
    if not summary_data: return go.Figure()
    df_summary = pd.DataFrame(summary_data)
    df_summary['R2 Score'] = df_summary['R2 Score'].astype(float)
    df_summary['RMSE'] = df_summary['RMSE'].astype(float)
    currencies = df_summary['Currency'].unique()
    fig = make_subplots(rows=len(currencies), cols=2, subplot_titles=[item for currency in currencies for item in (f"{currency} R2", f"{currency} RMSE")])
    for i, currency in enumerate(currencies):
        row = i + 1
        currency_df = df_summary[df_summary['Currency'] == currency]
        r2_df = currency_df.sort_values('R2 Score', ascending=True)
        fig.add_trace(go.Bar(
            x=r2_df['R2 Score'], y=r2_df['Model'], orientation='h', text=[f"{val:.3f}" for val in r2_df['R2 Score']],
            textposition='auto', marker_color=[('royalblue' if val >=0 else 'indianred') for val in r2_df['R2 Score']], name=f'{currency} R2'
        ), row=row, col=1)
        rmse_df = currency_df.sort_values('RMSE', ascending=False)
        fig.add_trace(go.Bar(
            x=rmse_df['RMSE'], y=rmse_df['Model'], orientation='h', text=[f"{val:.2f}" for val in rmse_df['RMSE']],
            textposition='auto', marker_color='salmon', name=f'{currency} RMSE'
        ), row=row, col=2)
    fig.update_layout(height=250*len(currencies), showlegend=False, title_text="통화별 모델 성능 비교 (R2 Score & RMSE)", bargap=0.1)
    return fig

def plot_correlation_heatmap(df):
    """
    드롭다운 없는 히트맵만 반환
    """
    label_map = {
        'kor_base_rate': '한국금리',
        'export_import_price_index': '수출입 지수',
        'news_sentiment': '뉴스 심리',
        'usd': 'USD', 'eur': 'EUR', 'jpy': 'JPY', 'cny': 'CNY',
        'crude_oil': '오일', 'gold': '금', 'sp500': 'S&P500'
    }
    ordered_cols = [
        'usd', 'eur', 'jpy', 'cny', 'crude_oil', 'gold', 'sp500',
        'kor_base_rate', 'export_import_price_index', 'news_sentiment'
    ]
    df_proc = df.copy()
    df_proc.columns = df_proc.columns.str.lower()
    # 누락된 컬럼이 있으면 경고 출력
    missing = [col for col in ordered_cols if col not in df_proc.columns]
    if missing:
        logging.warning(f"데이터프레임에 누락된 컬럼: {missing}")
    corr_cols = [col for col in ordered_cols if col in df_proc.columns]
    if len(corr_cols) < 2:
        return go.Figure()
    corr_matrix = df_proc[corr_cols].corr()
    # 대각선 기준 위쪽(upper triangle)은 NaN으로 채움
    mask = np.triu(np.ones(corr_matrix.shape), k=1).astype(bool)
    corr_matrix_masked = corr_matrix.copy()
    corr_matrix_masked.values[mask] = np.nan
    display_labels = [label_map.get(col, col) for col in corr_matrix.columns]
    fig = go.Figure(data=go.Heatmap(
        z=corr_matrix_masked, x=display_labels, y=display_labels,
        colorscale='RdBu', zmin=-1, zmax=1,
        text=corr_matrix_masked.applymap(lambda val: f'{val:.2f}' if pd.notna(val) else ''),
        texttemplate="%{text}", textfont={"size":10}, colorbar=dict(title='상관계수')
    ))
    fig.update_layout(
        title_text="주요 경제/금융 변수 상관관계 분석 (대각선 아래만 표시)", height=800, width=900, showlegend=False,
        xaxis=dict(side='top'), yaxis=dict(autorange='reversed'),
        margin=dict(l=120, r=50, t=120, b=50)
    )
    return fig

def plot_correlation_dropdown_bar(df):
    """
    드롭다운 바만 있는 plotly figure 반환 (히트맵 없이)
    """
    label_map = {
        'kor_base_rate': '한국금리',
        'export_import_price_index': '수출입 지수',
        'news_sentiment': '뉴스 심리',
        'usd': 'USD', 'eur': 'EUR', 'jpy': 'JPY', 'cny': 'CNY',
        'crude_oil': '오일', 'gold': '금', 'sp500': 'S&P500'
    }
    ordered_cols = [
        'usd', 'eur', 'jpy', 'cny', 'crude_oil', 'gold', 'sp500',
        'kor_base_rate', 'export_import_price_index', 'news_sentiment'
    ]
    df_proc = df.copy()
    df_proc.columns = df_proc.columns.str.lower()
    missing = [col for col in ordered_cols if col not in df_proc.columns]
    if missing:
        logging.warning(f"데이터프레임에 누락된 컬럼: {missing}")
    corr_cols = [col for col in ordered_cols if col in df_proc.columns]
    if len(corr_cols) < 2:
        return go.Figure()
    corr_matrix = df_proc[corr_cols].corr()
    display_labels = [label_map.get(col, col) for col in corr_matrix.columns]
    fig = go.Figure()
    for i, col in enumerate(corr_matrix.columns):
        correlations = corr_matrix[col].drop(col).sort_values()
        colors = ['royalblue' if v >= 0 else 'indianred' for v in correlations.values]
        bar_y_labels = [label_map.get(idx, idx) for idx in correlations.index]
        fig.add_trace(go.Bar(
            x=correlations.values, y=bar_y_labels, orientation='h',
            text=[f'{v:.2f}' for v in correlations.values], textposition='auto',
            name=f'{col} 상관계수', marker_color=colors, visible=(i == 0)
        ))
    # 드롭다운 메뉴
    buttons = []
    for i, col in enumerate(corr_matrix.columns):
        visibility = [False] * len(corr_matrix.columns)
        visibility[i] = True
        button = dict(
            label=label_map.get(col, col), method='update', args=[{'visible': visibility}]
        )
        buttons.append(button)
    fig.update_layout(
        title_text="상관계수 드롭다운 바만 (히트맵 없음)", height=700, width=700, showlegend=False,
        updatemenus=[dict(
            buttons=buttons, direction="down", showactive=True,
            x=0.0, xanchor="left", y=1.1, yanchor="top"
        )],
        xaxis_title="상관계수", yaxis=dict(autorange='reversed'),
        margin=dict(l=100, r=50, t=100, b=50)
    )
    return fig

# ===============================
# 6. 메인 파이프라인
# ===============================
if __name__ == '__main__':
    # WARNING 이상은 stderr로 출력
    logging.basicConfig(level=logging.WARNING, format='[%(levelname)s] %(message)s')

    collections_for_analysis = [
        'USD', 'EUR', 'JPY', 'CNY', 
        'CRUDE_OIL', 'GOLD', 'SP500',
        'KOR_BASE_RATE', 'export_import_price_index', 'news_sentiment'
    ]
    raw_df = get_currency_data(collections_for_analysis)

    if raw_df.empty:
        logging.warning("MongoDB에서 데이터를 가져오지 못했습니다. 프로그램을 종료합니다.")
    else:
        results_dir = os.environ.get("RESULTS_DIR", "results")
        currency_dir = os.path.join(results_dir, "currency")
        os.makedirs(currency_dir, exist_ok=True)

        # 1. 드롭다운 없는 히트맵
        heatmap_fig = plot_correlation_heatmap(raw_df)
        heatmap_fig.write_html(os.path.join(currency_dir, "correlation_heatmap_basic.html"))
        try:
            heatmap_fig.write_image(os.path.join(currency_dir, "correlation_heatmap_basic.png"), scale=2)
        except Exception as e:
            print(f"[경고] heatmap png 저장 실패: {e}")

        # 2. 드롭다운 바만 (히트맵 없음)
        dropdown_bar_fig = plot_correlation_dropdown_bar(raw_df)
        dropdown_bar_fig.write_html(os.path.join(currency_dir, "correlation_heatmap_dropdown_only.html"))
        try:
            dropdown_bar_fig.write_image(os.path.join(currency_dir, "correlation_heatmap_dropdown_only.png"), scale=2)
        except Exception as e:
            print(f"[경고] dropdown_bar png 저장 실패: {e}")

        model_df = raw_df[(raw_df['date'] >= '2016-01-01') & (raw_df['date'] <= '2025-12-31')].copy()
        currencies_to_model = ["USD", "EUR", "JPY", "CNY"]
        model_cols = ['date'] + currencies_to_model
        existing_model_cols = [c for c in model_df.columns if c.upper() in [mc.upper() for mc in model_cols]]
        currency_only_df = model_df[existing_model_cols].dropna()

        all_results_for_plotting = {}
        summary_data = []

        for currency in currencies_to_model:
            print(f"\n--- {currency} 모델링 시작 ---")
            processed_df = prepare_data(currency_only_df.copy(), currency)
            results, best_split = evaluate_models_with_split_optimization(processed_df, currency)
            if results:
                all_results_for_plotting[currency] = (results, best_split)
                for model_name, model_info in results.items():
                    optimizer = "N/A"
                    if 'LSTM' in model_name:
                        optimizer = model_name.split('_')[1]
                    summary_data.append({
                        'Currency': currency, 'Model': model_name,
                        'R2 Score': f"{model_info['R2']:.4f}", 'RMSE': f"{model_info['RMSE']:.2f}",
                        'Train/Test Split': f"{int(best_split*100)}:{int((1-best_split)*100)}", 'Optimizer': optimizer
                    })

        if summary_data:
            predictions_fig = plot_predictions(all_results_for_plotting, currency_only_df)
            summary_table_fig = plot_summary_table(summary_data)
            performance_bar_fig = plot_performance_bars(summary_data)

            predictions_fig.write_html(os.path.join(currency_dir, "allcurrencies_predictions.html"))
            try:
                predictions_fig.write_image(os.path.join(currency_dir, "allcurrencies_predictions.png"), scale=2)
            except Exception as e:
                print(f"[경고] predictions png 저장 실패: {e}")

            summary_table_fig.write_html(os.path.join(currency_dir, "allcurrencies_summary_table.html"))
            try:
                summary_table_fig.write_image(os.path.join(currency_dir, "allcurrencies_summary_table.png"), scale=2)
            except Exception as e:
                print(f"[경고] summary_table png 저장 실패: {e}")

            performance_bar_fig.write_html(os.path.join(currency_dir, "allcurrencies_performance_bar.html"))
            try:
                performance_bar_fig.write_image(os.path.join(currency_dir, "allcurrencies_performance_bar.png"), scale=2)
            except Exception as e:
                print(f"[경고] performance_bar png 저장 실패: {e}")
        else:
            print("모델링 결과가 없어 추가 시각화를 진행하지 않습니다.")