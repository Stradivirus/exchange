import pandas as pd
import numpy as np
import gc
import sys
import os

# [수정] 상위 경로 추가 (root config 인식용)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    # [수정] config -> gu_config
    from gu_config import PROJECTS_TO_RUN, PROJECT_CONFIGS
    from data_processor import prepare_data
    from models.standard_models import analyze_and_visualize_standard_models
    from models.time_series_models import run_prophet_pipeline, run_arima_pipeline
    from models.deep_learning_models import run_recurrent_nn_pipeline
    from report_generator import generate_final_report
except ImportError as e:
    print(f"❌ 모듈 임포트 실패: {e}")
    sys.exit(1)

def run_single_project(project_name):
    print(f"\n{'='*60}")
    print(f"🚀 프로젝트 시작: {project_name.upper()}")
    
    if project_name not in PROJECT_CONFIGS:
        return None

    print(f"📊 {PROJECT_CONFIGS[project_name]['description']}")
    
    data_package = prepare_data(project_name)
    if data_package is None or data_package[0] is None:
        print(f"❌ {project_name}: 데이터 준비 실패")
        return None
    
    df_raw, X, y, target_col, forecast_days = data_package
    
    try:
        all_results, all_predictions, y_train, y_test = run_all_models(
            df_raw, X, y, target_col, forecast_days, project_name
        )
    except Exception as e:
        print(f"❌ {project_name}: 모델링 오류: {e}")
        return None
    
    try:
        generate_final_report(all_results, all_predictions, y_train, y_test, target_col, project_name)
    except Exception as e:
        print(f"⚠️ {project_name}: 리포트 생성 오류: {e}")
    
    print(f"✅ {project_name.upper()} 완료!")
    return {
        'project': project_name, 'results': all_results, 'target': target_col
    }

def run_all_models(df_raw, X, y, target_col, forecast_days, project_name):
    # 1. 머신러닝
    std_results, std_preds, y_train, y_test = analyze_and_visualize_standard_models(
        df_raw, X, y, target_col, project_name
    )
    
    # 2. 딥러닝
    lstm_results, lstm_pred = run_recurrent_nn_pipeline(df_raw, target_col, forecast_days, project_name, 'LSTM')
    gru_results, gru_pred = run_recurrent_nn_pipeline(df_raw, target_col, forecast_days, project_name, 'GRU')
    
    # 3. 시계열
    prophet_results, prophet_pred = {}, pd.Series(dtype='float64')
    arima_results, arima_pred = {}, pd.Series(dtype='float64')
    
    if project_name in ['sp500', 'usd_krw']: 
        prophet_results, prophet_pred = run_prophet_pipeline(df_raw, target_col, project_name)
    
    if project_name in ['crude_oil']:
        arima_results, arima_pred = run_arima_pipeline(df_raw, target_col, project_name)
    
    all_results = {**std_results, **prophet_results, **arima_results, **lstm_results, **gru_results}
    all_predictions = {**std_preds, 'LSTM': lstm_pred, 'GRU': gru_pred}
    
    if not prophet_pred.empty: all_predictions['Prophet'] = prophet_pred
    if not arima_pred.empty: all_predictions['ARIMA'] = arima_pred
    
    return all_results, all_predictions, y_train, y_test

def main():
    print("\n🏁 [GU] 분석 시작")
    all_results = []
    
    for project_name in PROJECTS_TO_RUN:
        try:
            result = run_single_project(project_name)
            if result: all_results.append(result)
        except Exception as e:
            print(f"❌ {project_name} 실패: {e}")
        finally:
            gc.collect()
            print(f"🧹 메모리 정리 ({project_name})")

    print(f"\n🎉 [GU] 종료 (성공: {len(all_results)})")

if __name__ == "__main__":
    main()