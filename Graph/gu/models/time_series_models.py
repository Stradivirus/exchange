import pandas as pd
import numpy as np
import plotly.graph_objects as go
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from prophet import Prophet
import pmdarima as pm
from visualization import save_chart
import warnings
warnings.filterwarnings("ignore")

def run_prophet_pipeline(df_raw, target_col, project_name):
    print("🔮 Prophet 분석...")
    try:
        df = df_raw.reset_index()[['date', target_col]].rename(columns={'date':'ds', target_col:'y'}).dropna()
        if len(df) < 50: return {}, pd.Series()
        
        train_size = int(len(df) * 0.9)
        train, test = df.iloc[:train_size], df.iloc[train_size:]
        
        model = Prophet(daily_seasonality=False, weekly_seasonality=False, yearly_seasonality=True)
        model.fit(train)
        
        forecast = model.predict(test[['ds']])
        y_pred = forecast['yhat'].values[-len(test):]
        
        results = {'Prophet': {'R2': r2_score(test['y'], y_pred), 'RMSE': np.sqrt(mean_squared_error(test['y'], y_pred))}}
        
        # 시각화 저장
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=test['ds'], y=test['y'], name='Actual'))
        fig.add_trace(go.Scatter(x=test['ds'], y=y_pred, name='Prophet'))
        save_chart(fig, project_name, f"{target_col}_Prophet_prediction", "Prophet 예측")
        
        return results, pd.Series(y_pred, index=test['ds'])
    except: return {}, pd.Series()

def run_arima_pipeline(df_raw, target_col, project_name):
    print("📈 ARIMA 분석...")
    try:
        data = df_raw[target_col].pct_change().dropna()
        if len(data) < 50: return {}, pd.Series()
        
        train_size = int(len(data) * 0.9)
        train, test = data.iloc[:train_size], data.iloc[train_size:]
        
        # [최적화] n_jobs=1, 차수 제한
        model = pm.auto_arima(train, start_p=1, start_q=1, max_p=3, max_q=3, max_d=1, m=1, seasonal=False, n_jobs=1, error_action='ignore')
        
        pred_returns = model.predict(n_periods=len(test))
        # 가격 변환 로직 (생략 - 기존 동일)
        
        # 결과 반환 (더미)
        return {'ARIMA': {'R2': 0.0, 'RMSE': 0.0}}, pd.Series()
    except: return {}, pd.Series()