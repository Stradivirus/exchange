# ==========================================================================
# 시계열 모델 (Time Series Models)
# ==========================================================================

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from prophet import Prophet
import pmdarima as pm
import datetime

from visualization import get_global_chart_events, save_chart

def calculate_mape(y_true, y_pred):
    """0을 제외하고 MAPE를 계산하는 함수"""
    y_true, y_pred = np.array(y_true), np.array(y_pred)
    non_zero_mask = y_true != 0
    if np.sum(non_zero_mask) == 0:
        return np.nan
    return np.mean(np.abs((y_true[non_zero_mask] - y_pred[non_zero_mask]) / y_true[non_zero_mask])) * 100


def run_prophet_pipeline(df_raw, target_col, project_name):
    """
    Prophet 모델을 이용한 시계열 예측 파이프라인을 실행합니다.
    """
    print("🔮 Prophet 모델 분석 시작...")

    try:
        # 데이터 준비 - 인덱스 리셋하고 target_col만 선택
        df_prophet = df_raw.reset_index()
        df_prophet = df_prophet[['date', target_col]].copy()
        df_prophet.columns = ['ds', 'y']

        # NaN 값 제거
        df_prophet = df_prophet.dropna()

        if len(df_prophet) < 100:
            print("❌ Prophet 모델을 위한 충분한 데이터가 없습니다.")
            return {'Prophet': {'R2': np.nan, 'RMSE': np.nan, 'MAE': np.nan, 'MAPE': np.nan}}, pd.Series()

        train_size = int(len(df_prophet) * 0.8)
        train_df, test_df = df_prophet.iloc[:train_size].copy(), df_prophet.iloc[train_size:].copy()
        train_end_date = train_df['ds'].iloc[-1]

        # Prophet 모델 생성 및 학습
        model = Prophet(
            daily_seasonality=False,
            weekly_seasonality=False,
            yearly_seasonality=True,
            changepoint_prior_scale=0.05,
            interval_width=0.95
        )
        model.fit(train_df)

        # 예측 수행
        future = test_df[['ds']].copy()
        forecast = model.predict(future)

        # 결과 검증
        if len(forecast) != len(test_df):
            print(f"❌ 예측 결과 길이 불일치: 예상 {len(test_df)}, 실제 {len(forecast)}")
            return {'Prophet': {'R2': np.nan, 'RMSE': np.nan, 'MAE': np.nan, 'MAPE': np.nan}}, pd.Series()

        y_true, y_pred = test_df['y'].values, forecast['yhat'].values

        # 성능 계산
        results = {
            'Prophet': {
                'R2': r2_score(y_true, y_pred),
                'RMSE': np.sqrt(mean_squared_error(y_true, y_pred)),
                'MAE': mean_absolute_error(y_true, y_pred),
                'MAPE': calculate_mape(y_true, y_pred)
            }
        }

        # 예측 결과를 datetime 인덱스로 생성 (첫 번째 코드와 동일하게)
        test_dates = pd.to_datetime(test_df['ds'])
        prediction = pd.Series(y_pred, index=test_dates)

        print(f"📊 생성 중: {target_col} - Prophet 모델 예측")

        # 훈련/테스트 데이터 분할 (첫 번째 코드 방식과 동일하게)
        train_end_idx = len(df_raw) - len(test_dates)
        train_actual = df_raw[target_col].iloc[:train_end_idx]
        test_actual = pd.Series(y_true, index=test_dates)

        fig = go.Figure()

        # 훈련 데이터 - datetime 인덱스 사용
        fig.add_trace(go.Scatter(
            x=train_actual.index.to_pydatetime(), y=train_actual, mode='lines', name='훈련 데이터',
            line=dict(color='slategrey')
        ))

        # 테스트 실제값 - datetime 인덱스 사용
        fig.add_trace(go.Scatter(
            x=test_actual.index.to_pydatetime(), y=test_actual, mode='lines', name=f'{target_col} 실제값',
            line=dict(color='royalblue')
        ))

        # Prophet 예측값 - datetime 인덱스 사용
        fig.add_trace(go.Scatter(
            x=prediction.index.to_pydatetime(), y=prediction, mode='lines', name='Prophet 예측',
            line=dict(color='limegreen', dash='dot')
        ))

        # 이벤트 표시
        events = get_global_chart_events()
        for event in events:
            if event['type'] == 'line':
                event_date = datetime.datetime.strptime(event['date'], '%Y-%m-%d')
                fig.add_vline(x=event_date, line_width=1, line_dash="dot",
                              line_color=event['color'], opacity=0.7)
            elif event['type'] == 'span':
                start_date = datetime.datetime.strptime(event['start'], '%Y-%m-%d')
                end_date = datetime.datetime.strptime(event['end'], '%Y-%m-%d')
                fig.add_vrect(x0=start_date, x1=end_date, fillcolor=event['color'],
                              opacity=0.15, line_width=0, layer="below")

        # 훈련/테스트 분할점 표시 (첫 번째 코드와 동일)
        fig.add_vline(x=train_end_date, line_width=2, line_dash="dash", line_color="green")
        fig.add_annotation(x=train_end_date, y=test_actual.min(), text="훈련/테스트<br>분할점",
                           showarrow=True, arrowhead=1, ax=0, ay=-40)

        # R² Score 표시 (첫 번째 코드와 동일한 형식)
        fig.add_annotation(xref="paper", yref="paper", x=0.98, y=0.98,
                           text=f"<b>모델 설명력 (R² Score)</b><br>{results['Prophet']['R2']:.3f}",
                           showarrow=False, font=dict(size=14), align="right",
                           bgcolor="rgba(255, 255, 255, 0.8)", bordercolor="black", borderwidth=1)

        fig.update_layout(
            title=dict(text=f"{target_col} - Prophet 모델 예측", x=0.5),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )

        save_chart(fig, project_name, f"{target_col}_Prophet_prediction", f"{target_col} - Prophet 모델 예측")

        print("✅ Prophet 모델 분석 완료")
        return results, prediction

    except Exception as e:
        print(f"❌ Prophet 모델 실행 중 오류: {e}")
        return {'Prophet': {'R2': np.nan, 'RMSE': np.nan, 'MAE': np.nan, 'MAPE': np.nan}}, pd.Series()

def run_arima_pipeline(df_raw, target_col, project_name):
    """
    ARIMA 모델을 이용한 시계열 예측 파이프라인을 실행합니다.
    """
    print("📈 ARIMA 모델 분석 시작...")
    
    try:
        data = df_raw[target_col].pct_change().dropna()
        
        if len(data) < 50:
            print("❌ ARIMA 모델을 위한 충분한 데이터가 없습니다.")
            return {'ARIMA': {'R2': np.nan, 'RMSE': np.nan, 'MAE': np.nan, 'MAPE': np.nan}}, pd.Series()
        
        train_size = int(len(data) * 0.8)
        train_data, test_data = data.iloc[:train_size], data.iloc[train_size:]
        train_end_date = train_data.index[-1]
        
        model = pm.auto_arima(train_data, start_p=1, start_q=1, test='adf',
                             max_p=5, max_q=5, m=1, d=0, seasonal=False,
                             trace=False, error_action='raise', suppress_warnings=True,
                             stepwise=True, with_intercept='auto')
        
        # 수익률 예측 후 가격으로 변환
        predicted_returns = model.predict(n_periods=len(test_data))
        last_train_price = df_raw[target_col].loc[train_end_date]
        
        predicted_prices = [last_train_price]
        for r in predicted_returns:
            next_price = predicted_prices[-1] * (1 + r)
            predicted_prices.append(next_price)
        
        prediction_series = pd.Series(predicted_prices[1:], index=test_data.index)
        actual_prices_test = df_raw.loc[prediction_series.index, target_col]
        
        if len(actual_prices_test) != len(prediction_series):
            min_len = min(len(actual_prices_test), len(prediction_series))
            actual_prices_test = actual_prices_test.iloc[:min_len]
            prediction_series = prediction_series.iloc[:min_len]
        
        results = {
            'ARIMA': {
                'R2': r2_score(actual_prices_test, prediction_series),
                'RMSE': np.sqrt(mean_squared_error(actual_prices_test, prediction_series)),
                'MAE': mean_absolute_error(actual_prices_test, prediction_series),
                'MAPE': calculate_mape(actual_prices_test, prediction_series)
            }
        }
        
        original_train_data = df_raw[target_col].loc[:train_end_date]
        original_test_data = actual_prices_test
        
        print(f"📊 생성 중: {target_col} - ARIMA 모델 예측")
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
        x=original_train_data.index.to_pydatetime(), y=original_train_data, mode='lines', name='훈련 데이터',
        line=dict(color='slategrey')
        ))
        
        fig.add_trace(go.Scatter(
        x=original_test_data.index.to_pydatetime(), y=original_test_data, mode='lines', name=f'{target_col} 실제값',
        line=dict(color='royalblue')
        ))
        
        fig.add_trace(go.Scatter(
        x=prediction_series.index.to_pydatetime(), y=prediction_series, mode='lines', name='ARIMA 예측',
        line=dict(color='#00CED1', dash='dot')
        ))
        
        # 이벤트 표시
        events = get_global_chart_events()
        for event in events:
            if event['type'] == 'line':
                event_date = datetime.datetime.strptime(event['date'], '%Y-%m-%d')
                fig.add_vline(x=event_date, line_width=1, line_dash="dot", 
                             line_color=event['color'], opacity=0.7)
            elif event['type'] == 'span':
                start_date = datetime.datetime.strptime(event['start'], '%Y-%m-%d')
                end_date = datetime.datetime.strptime(event['end'], '%Y-%m-%d')
                fig.add_vrect(x0=start_date, x1=end_date, fillcolor=event['color'], 
                             opacity=0.15, line_width=0, layer="below")
        
        fig.add_vline(x=train_end_date, line_width=2, line_dash="dash", line_color="green")
        fig.add_annotation(x=train_end_date, y=original_test_data.min(), text="훈련/테스트<br>분할점",
                          showarrow=True, arrowhead=1, ax=0, ay=-40)
        
        fig.add_annotation(xref="paper", yref="paper", x=0.98, y=0.98,
                          text=f"<b>R² Score</b><br>{results['ARIMA']['R2']:.3f}",
                          showarrow=False, font=dict(size=14), align="right",
                          bgcolor="rgba(255, 255, 255, 0.8)", bordercolor="black", borderwidth=1)
        
        fig.update_layout(
            title=dict(text=f"{target_col} - ARIMA 모델 예측", x=0.5),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        save_chart(fig, project_name, f"{target_col}_ARIMA_prediction", f"{target_col} - ARIMA 모델 예측")
        
        print("✅ ARIMA 모델 분석 완료")
        return results, prediction_series
        
    except Exception as e:
        print(f"❌ ARIMA 모델 실행 중 오류: {e}")
        return {'ARIMA': {'R2': np.nan, 'RMSE': np.nan, 'MAE': np.nan, 'MAPE': np.nan}}, pd.Series()
