# ==========================================================================
# 머신러닝 모델 (Standard Models)
# ==========================================================================

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
import datetime

from config import MODELS
from visualization import get_global_chart_events, plot_macro_relationship_chart, save_chart

def calculate_mape(y_true, y_pred):
    """0을 제외하고 MAPE를 계산하는 함수"""
    y_true, y_pred = np.array(y_true), np.array(y_pred)
    non_zero_mask = y_true != 0
    if np.sum(non_zero_mask) == 0:
        return np.nan # 모든 실제값이 0이면 계산 불가
    return np.mean(np.abs((y_true[non_zero_mask] - y_pred[non_zero_mask]) / y_true[non_zero_mask])) * 100

def analyze_and_visualize_standard_models(df_raw, X, y, target_col, project_name):
    """
    표준 머신러닝 모델의 분석 및 시각화 파이프라인을 실행합니다.
    """
    print("🤖 머신러닝 모델 분석 시작...")
    
    # 환율 프로젝트에서만 관계 차트 생성
    if project_name == 'usd_krw':
        print("📊 환율 프로젝트: 거시경제 관계 차트 생성 중...")
        
        plot_macro_relationship_chart(
            df=df_raw, main_col='USD/KRW', main_label='원/달러 환율', main_color='red',
            sub_col='CrudeOil', sub_label='원유 가격 (USD)', sub_color='green',
            title='원/달러 환율과 원유 가격 관계',
            project_name=project_name, save_name='usdkrw_oil_relationship'
        )
        
        plot_macro_relationship_chart(
            df=df_raw, main_col='USD/KRW', main_label='원/달러 환율', main_color='red',
            sub_col='SP 500', sub_label='S&P 500 지수', sub_color='blue',
            title='원/달러 환율과 S&P 500 지수 관계',
            project_name=project_name, save_name='usdkrw_sp500_relationship'
        )
    else:
        print(f"📊 {project_name.upper()} 프로젝트: 상관관계 히트맵만 생성")
    
    # 상관관계 히트맵
    print("📊 생성 중: 상관관계 히트맵")
    corr_fig = px.imshow(df_raw.corr(), text_auto=True, aspect="auto", 
                         title='거시경제 지표 상관관계', color_continuous_scale='RdBu_r')
    corr_fig.update_xaxes(side="top")
    save_chart(corr_fig, project_name, 'correlation_heatmap', '거시경제 지표 상관관계')
    
    # 훈련/테스트 데이터 분할
    train_size = int(len(X) * 0.8)
    X_train, X_test, y_train, y_test = X.iloc[:train_size], X.iloc[train_size:], y.iloc[:train_size], y.iloc[train_size:]
    
    results, predictions = {}, {}
    
    print("🔍 모델별 학습 및 평가...")
    
    for name, model in MODELS.items():
        print(f"   ⚙️ {name} 모델 학습 중...")
        
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        
        current_results = {
            'R2': r2_score(y_test, y_pred),
            'RMSE': np.sqrt(mean_squared_error(y_test, y_pred)),
            'MAE': mean_absolute_error(y_test, y_pred),
            'MAPE': calculate_mape(y_test, y_pred)
        }
        
        results[name] = current_results
        predictions[name] = pd.Series(y_pred, index=y_test.index)
        
        # 개별 모델 시각화
        print(f"📊 생성 중: {target_col} - {name} 모델 예측")
        fig = go.Figure()
        
        # 1. 날짜 문제 해결: .to_pydatetime() 추가
        fig.add_trace(go.Scatter(
            x=y_train.index.to_pydatetime(), y=y_train, mode='lines', name='훈련 데이터',
            line=dict(color='slategrey')
        ))
        
        fig.add_trace(go.Scatter(
            x=y_test.index.to_pydatetime(), y=y_test, mode='lines', name=f'{target_col} 실제값',
            line=dict(color='royalblue')
        ))
        
        fig.add_trace(go.Scatter(
            x=y_test.index.to_pydatetime(), y=y_pred, mode='lines', name=f'{name} 예측',
            line=dict(color='crimson', dash='dot')
        ))
        
        train_end_date = y_train.index[-1]
        
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
        fig.add_annotation(x=train_end_date, y=y_test.min(), text="훈련/테스트<br>분할점",
                          showarrow=True, arrowhead=1, ax=0, ay=-40)
        
        # R2 Score 표시 상자 (LSTM과 동일한 스타일)
        fig.add_annotation(xref="paper", yref="paper", x=0.98, y=0.98,
                          text=f"<b>모델 설명력 (R² Score)</b><br>{current_results['R2']:.3f}",
                          showarrow=False, font=dict(size=14), align="right",
                          bgcolor="rgba(255, 255, 255, 0.8)", bordercolor="black", borderwidth=1)
        
        # 차트 제목 및 범례 (LSTM과 동일한 스타일)
        fig.update_layout(
            title=dict(text=f"'{target_col}' 예측 결과 ({name} 단일 모델)", x=0.5),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        save_chart(fig, project_name, f"{target_col}_{name}_prediction", f"{target_col} - {name} 모델 예측")
    
    # 결과 요약 테이블
    print("📊 생성 중: 머신러닝 모델 성능 비교표")
    summary_df_std = pd.DataFrame(results).T.reset_index()
    summary_df_std.columns = ['Model', 'R2 Score', 'RMSE', 'MAE', 'MAPE']
    summary_df_std = summary_df_std.sort_values('R2 Score', ascending=False).round(3)
    
    ranks_std = [f"#{i+1}" for i in range(len(summary_df_std))]
    summary_df_std['Rank Type'] = [f"{rank} 머신러닝" for rank in ranks_std]
    
    final_columns = ['Rank Type', 'Model', 'R2 Score', 'RMSE', 'MAE', 'MAPE']
    summary_df_std = summary_df_std[final_columns].reset_index(drop=True)
    
    colors_std = [['lavender'] * len(summary_df_std)] * len(summary_df_std.columns)
    if not summary_df_std.empty:
        for i in range(len(summary_df_std.columns)):
            colors_std[i][0] = 'lightgreen'
    
    summary_fig_std = go.Figure(data=[go.Table(
        header=dict(values=list(summary_df_std.columns), fill_color='paleturquoise', align='center'),
        cells=dict(values=[summary_df_std[c] for c in summary_df_std.columns],
                  fill_color=colors_std, align='center')
    )])
    
    summary_fig_std.update_layout(title=dict(text=f"{target_col} 머신러닝 모델 성능 비교", x=0.5))
    save_chart(summary_fig_std, project_name, f"{target_col}_ml_performance_table", f"{target_col} 머신러닝 모델 성능 비교")
    
    print("✅ 머신러닝 모델 분석 완료")
    return results, predictions, y_train, y_test
