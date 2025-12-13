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
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from tensorflow.keras.optimizers import Adam, AdamW

import os
import logging
import datetime as dt


# ===============================
# 1. 데이터 가져오기
# ===============================
MONGO_URI = os.environ.get("MONGO_URI")
DB_NAME = os.environ.get("DB_NAME")


def get_currency_data(collections, db_name=DB_NAME, connection_string=MONGO_URI):
    client = MongoClient(connection_string)
    db = client[db_name]
    dfs = []
    for col_name in collections:
        col = db[col_name]
        doc = col.find_one({}, {"_id": 0, "date": 1, "rate": 1, "value": 1, "price": 1, "close": 1})
        if doc is None:
            print(f"경고: '{col_name}' 컬렉션에 데이터가 없습니다. 건너뜁니다.")
            continue
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
        df = df.rename(columns={value_field: col_name})
        df.columns = [c.lower() if c != col_name else col_name for c in df.columns]
        dfs.append(df)
    if not dfs:
        return pd.DataFrame()
    df_merged = reduce(lambda left, right: pd.merge(left, right, on='date', how='outer'), dfs)
    df_merged = df_merged.sort_values(by='date').reset_index(drop=True)
    return df_merged


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
        X_train, X_test, y_train, y_test = X.iloc[:split_idx], X.iloc[split_idx:], y.iloc[:split_idx], y.iloc[
                                                                                                       split_idx:]
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
            current_results[name] = {'R2': r2, 'RMSE': np.sqrt(mean_squared_error(y_test, y_pred)), 'model': model,
                                     'preds': (y_test.index, y_test, y_pred)}

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
            current_results[model_name] = {'R2': r2_lstm, 'RMSE': np.sqrt(mean_squared_error(y_test, y_pred_lstm)),
                                           'model': lstm_model, 'preds': (y_test.index, y_test, y_pred_lstm)}

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
    if not valid_currencies:
        return go.Figure()

    full_df.columns = full_df.columns.str.lower()
    full_df["date"] = pd.to_datetime(full_df["date"], errors="coerce")
    full_df = full_df.dropna(subset=["date"]).sort_values("date")

    fig = go.Figure()

    color_map = {
        "USD": ("#1f77b4", "#17becf"),
        "EUR": ("#2ca02c", "#98df8a"),
        "JPY": ("#ff7f0e", "#ffbb78"),
        "CNY": ("#d62728", "#ff9896"),
    }

    for currency in valid_currencies:
        results, _ = results_dict[currency]
        best_model_name = max(results, key=lambda k: results[k]["R2"])
        idx, _, y_pred = results[best_model_name]["preds"]

        if not isinstance(idx, pd.DatetimeIndex):
            x_pred = pd.to_datetime(idx, errors="coerce")
        else:
            x_pred = idx

        if currency.lower() in full_df.columns:
            actual_data = full_df[["date", currency.lower()]].dropna()
            if len(actual_data) > 0:
                fig.add_trace(go.Scatter(
                    x=actual_data["date"].dt.strftime("%Y-%m-%d"),
                    y=actual_data[currency.lower()],
                    mode="lines",
                    name=f"{currency} (Actual)",
                    line=dict(color=color_map[currency][0], width=2)
                ))

        pred_df = pd.DataFrame({"date": x_pred, "value": y_pred}).dropna()
        if len(pred_df) > 0:
            fig.add_trace(go.Scatter(
                x=pred_df["date"].dt.strftime("%Y-%m-%d"),
                y=pred_df["value"],
                mode="lines",
                name=f"{currency} (Predicted) - {best_model_name}",
                line=dict(color=color_map[currency][1], width=2)
            ))

    current_year = dt.datetime.now().year
    start_year = current_year - 5
    tickvals = [f"{year}-01-01" for year in range(start_year, current_year + 1)]
    ticktext = [str(year) for year in range(start_year, current_year + 1)]

    fig.update_layout(
        title=dict(
            text="통화별 최적 모델 예측 결과 (최근 5년, 통합 그래프)",
            x=0.5, y=0.95, xanchor="center", yanchor="top", font=dict(size=20)
        ),
        xaxis=dict(
            title="연도", tickvals=tickvals, ticktext=ticktext,
            showticklabels=True, showgrid=True, tickangle=0
        ),
        yaxis=dict(title="환율 (기준 통화: KRW)", showgrid=True),
        legend=dict(
            title="모델 및 통화 구분", orientation="h", yanchor="bottom", y=1.15,
            xanchor="center", x=0.5, bgcolor="rgba(255,255,255,0.8)",
            bordercolor="lightgray", borderwidth=1, font=dict(size=11)
        ),
        margin=dict(l=60, r=40, t=160, b=60),
        template="plotly_white",
        height=600
    )
    return fig


# ===============================
# 6. 메인 파이프라인
# ===============================
if __name__ == '__main__':
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

        today = dt.date.today()
        start_date = today - dt.timedelta(days=5 * 365)
        end_date = today

        model_df = raw_df[
            (raw_df["date"] >= pd.to_datetime(start_date)) &
            (raw_df["date"] <= pd.to_datetime(end_date))
        ].copy()
        
        currencies_to_model = ["USD", "EUR", "JPY", "CNY"]
        model_cols = ['date'] + currencies_to_model
        existing_model_cols = [c for c in model_df.columns if c.upper() in [mc.upper() for mc in model_cols]]
        currency_only_df = model_df[existing_model_cols].dropna()

        all_results_for_plotting = {}

        for currency in currencies_to_model:
            print(f"\n--- {currency} 모델링 시작 ---")
            processed_df = prepare_data(currency_only_df.copy(), currency)
            results, best_split = evaluate_models_with_split_optimization(processed_df, currency)
            if results:
                all_results_for_plotting[currency] = (results, best_split)

        if all_results_for_plotting:
            predictions_fig = plot_predictions(all_results_for_plotting, currency_only_df)
            predictions_fig.write_html(os.path.join(currency_dir, "allcurrencies_predictions1.html"))
            print(f"\n✅ 예측 결과 그래프를 '{os.path.join(currency_dir, 'allcurrencies_predictions1.html')}'에 저장했습니다.")
        else:
            print("모델링 결과가 없어 시각화를 진행하지 않습니다.")
