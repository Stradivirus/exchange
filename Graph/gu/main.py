# ==========================================================================
# 메인 실행 로직 (Main Execution Logic)  
# ==========================================================================

import pandas as pd
from config import PROJECTS_TO_RUN, PROJECT_CONFIGS
from data_processor import prepare_data
from models.standard_models import analyze_and_visualize_standard_models
from models.time_series_models import run_prophet_pipeline, run_arima_pipeline
from models.deep_learning_models import run_recurrent_nn_pipeline
from report_generator import generate_final_report

def run_single_project(project_name):
    """
    단일 프로젝트를 실행합니다.
    """
    print(f"\n{'='*80}")
    print(f"🚀 프로젝트 시작: {project_name.upper()}")
    print(f"📊 {PROJECT_CONFIGS[project_name]['description']}")
    print(f"{'='*80}")
    
    # 1단계: 데이터 준비
    data_package = prepare_data(project_name)
    if data_package[0] is None:
        print(f"❌ {project_name} 데이터 준비 실패")
        return None
    
    df_raw, X, y, target_col, forecast_days = data_package
    
    # 2단계: 모든 모델 실행
    all_results, all_predictions, y_train, y_test = run_all_models(
        df_raw, X, y, target_col, forecast_days, project_name
    )
    
    # 3단계: 최종 리포트 생성
    try:
        generate_final_report(all_results, all_predictions, y_train, y_test, target_col, project_name)
    except Exception as e:
        print(f"⚠️  최종 리포트 생성 중 오류: {e}")
        print("   다른 모델 결과는 정상적으로 저장되었습니다.")
    
    print(f"✅ {project_name.upper()} 분석 완료!")
    return {
        'project': project_name,
        'results': all_results,
        'target': target_col
    }

def run_all_models(df_raw, X, y, target_col, forecast_days, project_name):
    """
    모든 모델링 파이프라인을 실행합니다.
    """
    # 표준 머신러닝 모델
    std_results, std_preds, y_train, y_test = analyze_and_visualize_standard_models(df_raw, X, y, target_col, project_name)
    
    # 딥러닝 모델
    lstm_results, lstm_pred = run_recurrent_nn_pipeline(df_raw, target_col, forecast_days, project_name, model_type='LSTM')
    gru_results, gru_pred = run_recurrent_nn_pipeline(df_raw, target_col, forecast_days, project_name, model_type='GRU')
    
    # 시계열 모델 (프로젝트별 조건부 실행)
    prophet_results, prophet_pred = {}, pd.Series()
    if project_name == 'sp500':
        try:
            prophet_results, prophet_pred = run_prophet_pipeline(df_raw, target_col, project_name)
        except Exception as e:
            print(f"⚠️  Prophet 모델 실행 중 오류: {e}")
            prophet_results, prophet_pred = {'Prophet': {'R2': np.nan, 'RMSE': np.nan, 'MAE': np.nan, 'MAPE': np.nan}}, pd.Series()
    
    arima_results, arima_pred = {}, pd.Series()
    if project_name == 'crude_oil':
        try:
            arima_results, arima_pred = run_arima_pipeline(df_raw, target_col, project_name)
        except Exception as e:
            print(f"⚠️  ARIMA 모델 실행 중 오류: {e}")
            arima_results, arima_pred = {'ARIMA': {'R2': np.nan, 'RMSE': np.nan, 'MAE': np.nan,'MAPE': np.nan}}, pd.Series()
    
    # 결과 통합
    all_results = {**std_results, **prophet_results, **arima_results, **lstm_results, **gru_results}
    all_predictions = {**std_preds, 'LSTM': lstm_pred, 'GRU': gru_pred}
    
    if not prophet_pred.empty:
        all_predictions['Prophet'] = prophet_pred
    if not arima_pred.empty:
        all_predictions['ARIMA'] = arima_pred
    
    return all_results, all_predictions, y_train, y_test

def main():
    """
    여러 프로젝트를 순차적으로 실행하는 메인 함수입니다.
    """
    print("🏁 금융 데이터 예측 모델링 시작...")
    print(f"📋 실행할 프로젝트: {', '.join(PROJECTS_TO_RUN)}")
    
    all_project_results = []
    
    # 각 프로젝트를 순차적으로 실행
    for project_name in PROJECTS_TO_RUN:
        try:
            result = run_single_project(project_name)
            if result:
                all_project_results.append(result)
        except Exception as e:
            print(f"❌ {project_name} 실행 중 오류: {e}")
            continue
    
    # 전체 결과 요약
    print(f"\n{'='*80}")
    print("📊 전체 프로젝트 결과 요약")
    print(f"{'='*80}")
    
    for result in all_project_results:
        project = result['project']
        # NaN이 아닌 결과만 필터링
        valid_results = {k: v for k, v in result['results'].items() if not pd.isna(v['R2'])}
        
        if valid_results:
            best_model = max(valid_results.items(), key=lambda x: x[1]['R2'])[0]
            best_r2 = valid_results[best_model]['R2']
            print(f"🎯 {project.upper()}: 최고 성능 모델 = {best_model} (R² = {best_r2:.3f})")
        else:
            print(f"⚠️  {project.upper()}: 유효한 결과 없음")
    
    print(f"\n🎉 모든 분석 완료! 총 {len(all_project_results)}개 프로젝트 실행됨")

if __name__ == "__main__":
    main()
