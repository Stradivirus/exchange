import numpy as np
import pandas as pd
import plotly.graph_objects as go
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout, GRU
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras.backend import clear_session
import gc

from data_processor import prepare_data_for_lstm
from visualization import get_global_chart_events, save_chart

try:
    tf.config.set_visible_devices([], 'GPU')
except: pass

def calculate_mape(y_true, y_pred):
    y_true, y_pred = np.array(y_true), np.array(y_pred)
    non_zero = y_true != 0
    if np.sum(non_zero) == 0: return np.nan
    return np.mean(np.abs((y_true[non_zero] - y_pred[non_zero]) / y_true[non_zero])) * 100

def run_recurrent_nn_pipeline(df_raw, target_col, forecast_days, project_name, model_type='LSTM'):
    print(f"🧠 {model_type} 모델 분석 시작...")
    clear_session()
    
    try:
        X_train, X_test, y_train, y_test, scaler, test_dates = prepare_data_for_lstm(df_raw, target_col, forecast_days)
        
        if len(X_train) == 0: return {}, pd.Series()

        model = Sequential()
        input_shape = (X_train.shape[1], X_train.shape[2])
        
        if model_type == 'LSTM':
            model.add(LSTM(30, return_sequences=True, input_shape=input_shape))
            model.add(Dropout(0.2))
            model.add(LSTM(20))
        else:
            model.add(GRU(30, return_sequences=True, input_shape=input_shape))
            model.add(Dropout(0.2))
            model.add(GRU(20))
            
        model.add(Dense(1))
        model.compile(optimizer='adam', loss='mse')
        
        early_stop = EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True)
        model.fit(X_train, y_train, epochs=20, batch_size=64, validation_split=0.1, callbacks=[early_stop], verbose=0)
        
        y_pred_scaled = model.predict(X_test, verbose=0)
        
        # 역변환 로직
        pred_temp = np.zeros((len(y_pred_scaled), X_train.shape[2]))
        pred_temp[:, 0] = y_pred_scaled.flatten()
        y_pred = scaler.inverse_transform(pred_temp)[:, 0]
        
        test_temp = np.zeros((len(y_test), X_train.shape[2]))
        test_temp[:, 0] = y_test.flatten()
        y_test_orig = scaler.inverse_transform(test_temp)[:, 0]
        
        results = {
            model_type: {
                'R2': r2_score(y_test_orig, y_pred),
                'RMSE': np.sqrt(mean_squared_error(y_test_orig, y_pred)),
                'MAE': mean_absolute_error(y_test_orig, y_pred),
                'MAPE': calculate_mape(y_test_orig, y_pred)
            }
        }
        
        prediction = pd.Series(y_pred, index=test_dates)
        
        # 시각화 (생략 - 위와 동일 패턴)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=test_dates, y=y_test_orig, name='Actual'))
        fig.add_trace(go.Scatter(x=test_dates, y=y_pred, name='Pred'))
        save_chart(fig, project_name, f"{target_col}_{model_type}_prediction", f"{model_type} 예측")
        
        print(f"✅ {model_type} 완료")
        return results, prediction

    except Exception as e:
        print(f"❌ {model_type} 오류: {e}")
        return {}, pd.Series()
    finally:
        clear_session()
        gc.collect()