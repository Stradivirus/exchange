# report_generator.py 파일의 전체 내용을 아래 코드로 교체해주세요.

# ==========================================================================
# 리포트 생성 (Report Generator)
# ==========================================================================

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import datetime

# ========================= 수정된 부분: import 구문 추가 =========================
# advisor.py 파일에서 run_advisor_pipeline 함수를 가져옵니다.
from advisor import run_advisor_pipeline
# ==============================================================================

from visualization import get_global_chart_events, save_chart

def generate_final_report(all_results, all_predictions, y_train, y_test, target_col, project_name):
    """
    모든 모델의 결과를 종합하여 최종 리포트(테이블, 차트)를 생성합니다.
    """
    print("📋 최종 리포트 생성 중...")
    
    if not all_results:
        print("❌ 분석할 결과가 없습니다.")
        return
    
    # 결과 통합
    summary_df = pd.DataFrame(all_results).T.reset_index()
    summary_df.columns = ['Model', 'R2 Score', 'RMSE', 'MAE', 'MAPE']
    
    # 모델 타입 매핑
    model_type_map = {
        'GRU': '딥러닝', 'LSTM': '딥러닝', 'Prophet': '시계열', 'ARIMA': '시계열',
        'XGBoost': '머신러닝', 'RandomForest': '머신러닝', 'Linear': '머신러닝', 'Ridge': '머신러닝'
    }
    
    summary_df['Model Type'] = summary_df['Model'].map(model_type_map)
    
    # 순위 매기기
    summary_df.dropna(subset=['R2 Score'], inplace=True)
    summary_df = summary_df.sort_values('R2 Score', ascending=False).round(3).reset_index(drop=True)
    
    if summary_df.empty:
        print("❌ 유효한 결과가 없습니다.")
        return
    
    best_model_overall = summary_df.iloc[0]
    
    ranks = [f"#{i+1}" for i in range(len(summary_df))]
    summary_df['Rank Type'] = [f"{rank} {mtype}" for rank, mtype in zip(ranks, summary_df['Model Type'])]
    
    final_columns = ['Rank Type', 'Model', 'R2 Score', 'RMSE', 'MAE', 'MAPE']
    summary_df = summary_df[final_columns]
    
    colors = [['lavender'] * len(summary_df)] * len(summary_df.columns)
    if not summary_df.empty and len(colors[0]) > 0:
        for i in range(len(summary_df.columns)):
            colors[i][0] = 'lightgreen'
    
    # 최종 성능 비교 테이블
    print("📊 생성 중: 전체 모델 성능 비교표")
    summary_fig = go.Figure(data=[go.Table(
        header=dict(values=list(summary_df.columns), fill_color='paleturquoise', align='center'),
        cells=dict(values=[summary_df[c] for c in summary_df.columns],
                  fill_color=colors, align='center')
    )])
    
    summary_fig.update_layout(title=dict(text=f"{target_col} 전체 모델 성능 비교", x=0.5))
    
    clean_target_col = target_col.replace(' ', '').replace('/', '')
    save_chart(summary_fig, project_name, f"{clean_target_col}_final_performance_table", f"{target_col} 전체 모델 성능 비교")
    
    # 최고 성능 모델 예측 차트
    best_prediction = all_predictions.get(best_model_overall['Model'])
    if best_prediction is None or best_prediction.empty:
        print(f"❌ 최고 성능 모델 {best_model_overall['Model']}의 예측 데이터를 찾을 수 없습니다.")
        return
    
    train_end_date = y_train.index[-1]
    
    print(f"📊 생성 중: {target_col} - 최고 성능 모델 ({best_model_overall['Model']}) 예측")
    pred_fig = go.Figure()
    
    pred_fig.add_trace(go.Scatter(
        x=y_train.index.to_pydatetime(), y=y_train, mode='lines', name='훈련 데이터',
        line=dict(color='slategrey')
    ))
    
    pred_fig.add_trace(go.Scatter(
        x=y_test.index.to_pydatetime(), y=y_test, mode='lines', name=f'{target_col} 실제값',
        line=dict(color='royalblue')
    ))
    
    pred_fig.add_trace(go.Scatter(
        x=best_prediction.index.to_pydatetime(), y=best_prediction, mode='lines', 
        name=f'{best_model_overall["Model"]} 예측',
        line=dict(color='crimson', dash='dot')
    ))
    
    events = get_global_chart_events()
    for event in events:
        if event['type'] == 'line':
            event_date = datetime.datetime.strptime(event['date'], '%Y-%m-%d')
            pred_fig.add_vline(x=event_date, line_width=1, line_dash="dot", 
                              line_color=event['color'], opacity=0.7)
        elif event['type'] == 'span':
            start_date = datetime.datetime.strptime(event['start'], '%Y-%m-%d')
            end_date = datetime.datetime.strptime(event['end'], '%Y-%m-%d')
            pred_fig.add_vrect(x0=start_date, x1=end_date, fillcolor=event['color'], 
                              opacity=0.15, line_width=0, layer="below")
    
    pred_fig.add_vline(x=train_end_date, line_width=2, line_dash="dash", line_color="green")
    pred_fig.add_annotation(x=train_end_date, y=y_test.min(), text="훈련/테스트<br>분할점",
                           showarrow=True, arrowhead=1, ax=0, ay=-40)
    
    pred_fig.add_annotation(xref="paper", yref="paper", x=0.98, y=0.98,
                           text=f"<b>모델 설명력 (R² Score)</b><br>{best_model_overall['R2 Score']:.3f}",
                           showarrow=False, font=dict(size=14), align="right",
                           bgcolor="rgba(255, 255, 255, 0.8)", bordercolor="black", borderwidth=1)
    
    pred_fig.update_layout(
        title=dict(text=f"'{target_col}' 예측 결과 (최고 성능 모델: {best_model_overall['Model']})", x=0.5),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    save_chart(pred_fig, project_name, f"{clean_target_col}_best_model_prediction", f"{target_col} - 최고 성능 모델 예측")
    
    print("✅ 최종 리포트 생성 완료")
    
    # AI 트레이딩 어드바이저 실행
    try:
        from config import PROJECT_CONFIGS
        forecast_days = PROJECT_CONFIGS[project_name]['forecast_days']
        
        run_advisor_pipeline(all_results, all_predictions, y_test, target_col, forecast_days, project_name)
    except Exception as e:
        print(f"❌ AI 어드바이저 실행 중 오류 발생: {e}")