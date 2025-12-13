import os
os.environ["OMP_NUM_THREADS"] = "1"

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
import datetime
import gc 
import sys

# [수정] 상위 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# [수정] config -> gu_config
from gu_config import MODELS
from visualization import get_global_chart_events, plot_macro_relationship_chart, save_chart

def calculate_mape(y_true, y_pred):
    y_true, y_pred = np.array(y_true), np.array(y_pred)
    non_zero_mask = y_true != 0
    if np.sum(non_zero_mask) == 0: return np.nan
    return np.mean(np.abs((y_true[non_zero_mask] - y_pred[non_zero_mask]) / y_true[non_zero_mask])) * 100

def analyze_and_visualize_standard_models(df_raw, X, y, target_col, project_name):
    print("🤖 머신러닝 모델 분석 시작...")
    
    if project_name == 'usd_krw':
        try:
            plot_macro_relationship_chart(df_raw, 'USD/KRW', '원/달러', 'red', 'CrudeOil', '원유', 'green', '환율-유가', project_name, 'usdkrw_oil')
            plot_macro_relationship_chart(df_raw, 'USD/KRW', '원/달러', 'red', 'SP 500', 'S&P500', 'blue', '환율-주가', project_name, 'usdkrw_sp500')
        except: pass
    
    try:
        corr_fig = px.imshow(df_raw.corr(), text_auto=True, aspect="auto", color_continuous_scale='RdBu_r')
        save_chart(corr_fig, project_name, 'correlation_heatmap', '상관계수 히트맵')
    except: pass
    
    train_size = int(len(X) * 0.8)
    X_train, X_test = X.iloc[:train_size], X.iloc[train_size:]
    y_train, y_test = y.iloc[:train_size], y.iloc[train_size:]
    
    results, predictions = {}, {}
    
    for name, model in MODELS.items():
        print(f"   ⚙️ {name}...")
        try:
            if hasattr(model, 'set_params'): model.set_params(n_jobs=1)
        except: pass
        
        try:
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            
            results[name] = {
                'R2': r2_score(y_test, y_pred),
                'RMSE': np.sqrt(mean_squared_error(y_test, y_pred)),
                'MAE': mean_absolute_error(y_test, y_pred),
                'MAPE': calculate_mape(y_test, y_pred)
            }
            predictions[name] = pd.Series(y_pred, index=y_test.index)
            
            # 시각화 (코드 생략 - 위와 동일)
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=y_train.index, y=y_train, mode='lines', name='Train'))
            fig.add_trace(go.Scatter(x=y_test.index, y=y_test, mode='lines', name='Test'))
            fig.add_trace(go.Scatter(x=y_test.index, y=y_pred, mode='lines', name='Pred'))
            save_chart(fig, project_name, f"{target_col}_{name}_prediction", f"{name} 예측")
            
        except Exception as e:
            print(f"⚠️ {name} 실패: {e}")
            continue
    
    gc.collect()
    return results, predictions, y_train, y_test