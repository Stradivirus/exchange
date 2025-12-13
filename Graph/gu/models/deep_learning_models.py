# ==========================================================================
# 딥러닝 모델 (Deep Learning Models)
# ==========================================================================

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout, GRU
from tensorflow.keras.callbacks import EarlyStopping
import datetime

from data_processor import prepare_data_for_lstm
from visualization import get_global_chart_events, save_chart

def calculate_mape(y_true, y_pred):
    """0을 제외하고 MAPE를 계산하는 함수"""
    y_true, y_pred = np.array(y_true), np.array(y_pred)
    non_zero_mask = y_true != 0
    if np.sum(non_zero_mask) == 0:
        return np.nan
    return np.mean(np.abs((y_true[non_zero_mask] - y_pred[non_zero_mask]) / y_true[non_zero_mask])) * 100

def run_recurrent_nn_pipeline(df_raw, target_col, forecast_days, project_name, model_type='LSTM'):
    """
    순환 신경망(RNN) 계열 딥러닝 모델의 분석 파이프라인을 실행합니다.
    """
    print(f"🧠 {model_type} 모델 분석 시작...")
    
    time_steps = 60
    X_train, X_test, y_train, y_test, scaler, test_dates = prepare_data_for_lstm(
        df_raw, target_col, forecast_days, time_steps
    )
    
    model = Sequential()
    
    if model_type == 'LSTM':
        model.add(LSTM(units=50, return_sequences=True, input_shape=(X_train.shape[1], X_train.shape[2])))
        model.add(Dropout(0.2))
        model.add(LSTM(units=50))
    elif model_type == 'GRU':
        model.add(GRU(units=50, return_sequences=True, input_shape=(X_train.shape[1], X_train.shape[2])))
        model.add(Dropout(0.2))
        model.add(GRU(units=50))
    
    model.add(Dropout(0.2))
    model.add(Dense(units=25, activation='relu'))
    model.add(Dense(units=1))
    
    model.compile(optimizer='adam', loss='mean_squared_error')
    
    early_stopping = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)
    
    model.fit(X_train, y_train, epochs=50, batch_size=32, validation_split=0.1,
             callbacks=[early_stopping], verbose=0)  # verbose=0으로 설정하여 학습 로그 숨김
    
    y_pred_scaled = model.predict(X_test, verbose=0)
    
    # 스케일 역변환
    n_features = X_train.shape[2]
    pred_temp = np.zeros((len(y_pred_scaled), n_features))
    pred_temp[:, 0] = y_pred_scaled.flatten()
    y_pred = scaler.inverse_transform(pred_temp)[:, 0]
    
    test_temp = np.zeros((len(y_test), n_features))
    test_temp[:, 0] = y_test.flatten()
    y_test_original = scaler.inverse_transform(test_temp)[:, 0]
    
    results = {
        model_type: {
            'R2': r2_score(y_test_original, y_pred),
            'RMSE': np.sqrt(mean_squared_error(y_test_original, y_pred)),
            'MAE': mean_absolute_error(y_test_original, y_pred),
            'MAPE': calculate_mape(y_test_original, y_pred)
        }
    }
    
    prediction = pd.Series(y_pred, index=test_dates)
    
    print(f"📊 생성 중: {target_col} - {model_type} 모델 예측")
    train_end_idx = len(df_raw) - len(test_dates)
    train_end_date = df_raw.index[train_end_idx - 1]
    
    train_actual, test_actual = df_raw[target_col].iloc[:train_end_idx], pd.Series(y_test_original, index=test_dates)
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=train_actual.index.to_pydatetime(), y=train_actual, mode='lines', name='훈련 데이터',
        line=dict(color='slategrey')
    ))
    
    fig.add_trace(go.Scatter(
        x=test_actual.index.to_pydatetime(), y=test_actual, mode='lines', name=f'{target_col} 실제값',
        line=dict(color='royalblue')
    ))
    
    fig.add_trace(go.Scatter(
        x=prediction.index.to_pydatetime(), y=prediction, mode='lines', name=f'{model_type} 예측',
        line=dict(color='orange' if model_type == 'LSTM' else 'purple', dash='dot')
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
    fig.add_annotation(x=train_end_date, y=test_actual.min(), text="훈련/테스트<br>분할점",
                      showarrow=True, arrowhead=1, ax=0, ay=-40)
    
    fig.add_annotation(xref="paper", yref="paper", x=0.98, y=0.98,
                      text=f"<b>모델 설명력 (R² Score)</b><br>{results[model_type]['R2']:.3f}",
                      showarrow=False, font=dict(size=14), align="right",
                      bgcolor="rgba(255, 255, 255, 0.8)", bordercolor="black", borderwidth=1)
    
    fig.update_layout(
        title=dict(text=f"{target_col} - {model_type} 모델 예측", x=0.5),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    save_chart(fig, project_name, f"{target_col}_{model_type}_prediction", f"{target_col} - {model_type} 모델 예측")
    
    print(f"✅ {model_type} 모델 분석 완료")
    return results, prediction
