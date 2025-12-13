# ==========================================================================
# AI 트레이딩 어드바이저 (AI Trading Advisor)
# ==========================================================================

import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib import font_manager
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from visualization import save_chart 

def _setup_korean_font():
    """
    Matplotlib에서 한글을 지원하기 위한 폰트 설정을 시도합니다.
    """
    font_name = None
    # 시스템 폰트 경로 탐색
    font_paths = ["../malgun.ttf"]                   
    
    for path in font_paths:
        if os.path.exists(path):
            font_name = font_manager.FontProperties(fname=path).get_name()
            plt.rc('font', family=font_name)
            plt.rc('axes', unicode_minus=False) # 마이너스 폰트 깨짐 방지
            print(f"✅ 한글 폰트 설정 완료: {font_name}")
            return
            
    print("⚠️  한글 폰트를 찾을 수 없습니다. 기본 폰트로 설정됩니다 (한글이 깨질 수 있습니다).")
    print("   - 해결 방법: '나눔고딕'과 같은 한글 폰트를 설치해주세요.")

# advisor.py 파일의 전체 내용을 아래 코드로 교체해주세요.

import pandas as pd
import plotly.graph_objects as go

# 다른 파일에서 save_chart 함수를 가져옵니다.
from visualization import save_chart

def generate_advisor_data(all_results, all_predictions, y_test, target_col, forecast_days):
    """
    모델 분석 결과를 바탕으로 AI 어드바이저 리포트에 필요한 데이터를 생성합니다.
    """
    print("🧠 AI 어드바이저 데이터 생성 중...")
    
    summary_df = pd.DataFrame(all_results).T.rename(columns={'R2 Score': 'R2'})
    valid_summary_df = summary_df.dropna(subset=['R2']).sort_values('R2', ascending=False)
    
    if valid_summary_df.empty:
        print("❌ 유효한 모델 결과가 없어 AI 어드바이저를 생성할 수 없습니다.")
        return None
        
    best_model_name = valid_summary_df.index[0]
    best_result = valid_summary_df.iloc[0]
    best_prediction_series = all_predictions.get(best_model_name)

    if best_prediction_series is None or best_prediction_series.empty:
        print(f"❌ 최고 성능 모델({best_model_name})의 예측 데이터를 찾을 수 없습니다.")
        return None
        
    ai_score = max(0, min(100, round(best_result['R2'] * 100)))
    current_price = y_test.iloc[-1]
    target_price = best_prediction_series.iloc[-1]
    
    rmse = best_result['RMSE']
    best_price = target_price + rmse
    worst_price = target_price - rmse
    
    change_pct = (target_price - current_price) / current_price * 100
    
    if change_pct > 3: opinion = "적극 매수"
    elif 1 < change_pct <= 3: opinion = "비중 확대"
    elif -1 <= change_pct <= 1: opinion = "중립"
    elif -3 <= change_pct < -1: opinion = "비중 축소"
    else: opinion = "적극 매도"
    
    if ai_score > 75: opinion += " (강력 추천)"
    elif ai_score > 50: opinion += " (신중 접근)"
    else: opinion += " (보수적 관점)"
        
    # ========================= 1. 설명 문구 생성 =========================
    opinion_main = opinion.split(' (')[0]
    opinion_desc_map = {
        "적극 매수": f"향후 {forecast_days}일 내 유의미한 가격 상승이 예측됩니다.",
        "비중 확대": f"향후 {forecast_days}일 내 완만한 가격 상승이 예측됩니다.",
        "중립": f"향후 {forecast_days}일 내 가격 변동성이 낮거나 방향성이 불확실합니다.",
        "비중 축소": f"향후 {forecast_days}일 내 완만한 가격 하락이 예측됩니다.",
        "적극 매도": f"향후 {forecast_days}일 내 유의미한 가격 하락이 예측됩니다."
    }
    opinion_description = opinion_desc_map.get(opinion_main, "데이터 기반의 신중한 접근이 필요합니다.")
    # ===================================================================

    positive_drivers = [f"최고 성능 모델: {best_model_name} (R²: {best_result['R2']:.2f})", f"향후 {forecast_days}일 내 {change_pct:.2f}% 변동 예측"]
    negative_drivers = ["시장 변동성 확대 가능성", "예측 불확실성 상존"]
    advisor_info = {"best_model_name": best_model_name, "r2_score": best_result['R2'], "rmse": rmse}
    
    # ========================= 2. 생성된 설명 문구를 return 값에 포함 =========================
    return {
        "opinion": opinion, "ai_score": ai_score,
        "positive_drivers": positive_drivers, "negative_drivers": negative_drivers,
        "target_price": target_price, "best_price": best_price, "worst_price": worst_price,
        "current_price": current_price, "forecast_days": forecast_days, "target_col": target_col,
        "advisor_info": advisor_info,
        "opinion_description": opinion_description  # <<<< 이 부분이 중요합니다!
    }
    # =====================================================================================

def visualize_trading_advisor_plotly(advisor_data, project_name):
    """
    AI 어드바이저 데이터를 받아 Plotly를 이용해 보고서 형태의 미려한 차트로 시각화하고 파일로 저장합니다.
    """
    print("📊 생성 중: AI 트레이딩 어드바이저 리포트 (Plotly)")

    # 데이터 추출
    advisor_info = advisor_data.pop("advisor_info", None)
    opinion_description = advisor_data.pop("opinion_description", "")
    opinion, ai_score, pos_drivers, neg_drivers, target_p, best_p, worst_p, current_p, f_days, target_col = advisor_data.values()

    fig = go.Figure()

    # --- 1. 최상단 제목 ---
    opinion_full = opinion.replace(' (', ' (')
    color_map = {"적극 매수": "#008000", "비중 확대": "#2ca02c", "중립": "#7f7f7f", "비중 축소": "#ff7f0e", "적극 매도": "#d62728"}
    opinion_color = color_map.get(opinion.split(" ")[0], "black")
    fig.add_shape(type="line", x0=0, y0=0.98, x1=1, y1=0.98, line=dict(color="lightgrey", width=2), xref="paper", yref="paper")
    fig.add_annotation(text=f"<b>AI Trading Advisor ({pd.Timestamp.now().date()})</b>", xref="paper", yref="paper", x=0.5, y=0.97, showarrow=False, font=dict(size=28, color="#333"), xanchor="center")
    
    fig.add_annotation(text=f"<b>AI 최종 투자 의견: {opinion_full}</b>", xref="paper", yref="paper", x=0.5, y=0.90, showarrow=False, font=dict(size=40, color=opinion_color), xanchor="center")
    
    # ========================= 3. 전달받은 설명 문구의 위치를 조정하여 표시 =========================
    fig.add_annotation(text=opinion_description,
                    xref="paper", yref="paper", 
                    x=0.5, y=0.82,  
                    showarrow=False,
                    font=dict(size=16, color="#333333"),
                    xanchor="center")
    # =====================================================================================

    # 3. 분석 대상 (설명 아래로 이동하여 간격 확보)
    fig.add_annotation(text=f"({target_col} 시장 분석 결과)",
                    xref="paper", yref="paper", x=0.5, y=0.77, showarrow=False,
                    font=dict(size=16, color="grey"), xanchor="center")

    # --- 2. 컨텐츠 섹션 (게이지, 핵심 동력) ---
    fig.add_trace(go.Indicator(mode="gauge", value=ai_score, domain={'x': [0.1, 0.45], 'y': [0.55, 0.75]}, gauge={'shape': "angular", 'axis': {'range': [0, 100], 'visible': False}, 'bar': {'color': '#008000' if ai_score >= 50 else '#d62728', 'thickness': 1}, 'bgcolor': 'rgba(0,0,0,0.05)'}))
    fig.add_annotation(text="<b>AI 신뢰도 점수</b>", xref="paper", yref="paper", x=0.275, y=0.76, showarrow=False, font=dict(size=20), xanchor="center")
    fig.add_annotation(text=f"<b>{ai_score}</b><span style='font-size:30px;color:grey;'>/100</span>", xref="paper", yref="paper", x=0.275, y=0.64, showarrow=False, font=dict(size=60, color="black"), xanchor="center")
    drivers_text = f"<b style='color:#1f77b4;'>시장의 핵심 동력 (긍정)</b><br>" + "<br>".join([f"▲ {d}" for d in pos_drivers]) + f"<br><br><b style='color:#d62728;'>주의해야 할 위험 요인 (부정)</b><br>" + "<br>".join([f"▼ {d}" for d in neg_drivers])
    fig.add_annotation(text=drivers_text, align='left', showarrow=False, xref="paper", yref="paper", x=0.58, y=0.73, xanchor='left', yanchor='top', font=dict(size=14))

    # --- 3. 중앙 구분선 ---
    fig.add_shape(type="line", x0=0.05, y0=0.5, x1=0.95, y1=0.5, line=dict(color="lightgrey", width=1, dash="dash"), xref="paper", yref="paper")

    # --- 4. 컨텐츠 섹션 (시나리오 차트, 전략 가이드) ---
    if target_p is not None:
        dates = ['현재', f'+{f_days}일 후']
        fig.add_trace(go.Scatter(x=dates + dates[::-1], y=[current_p, best_p] + [worst_p, current_p], fill='toself', fillcolor='rgba(0,176,246,0.1)', line=dict(color='rgba(255,255,255,0)'), hoverinfo="none", showlegend=False, xaxis='x1', yaxis='y1'))
        fig.add_trace(go.Scatter(x=dates, y=[current_p, target_p], name='예상 경로', line=dict(color='royalblue', width=1.5, dash='dash'), mode='lines+markers', marker=dict(size=8, color='royalblue'), xaxis='x1', yaxis='y1', hoverinfo='text', text=[f"<b>현재가</b><br>가격: {current_p:,.0f}", f"<b>목표가</b><br>가격: {target_p:,.0f}"], hovertemplate='%{text}<extra></extra>'))
        fig.add_annotation(text=f"<b>현재가</b><br>{current_p:,.0f}", ax=0, ay=0, x=dates[0], y=current_p, yshift=-25, showarrow=False, xref='x1', yref='y1', font=dict(size=12))
        fig.add_annotation(text=f"<b>목표가</b><br>{target_p:,.0f}", ax=0, ay=0, x=dates[1], y=target_p, xshift=15, align='left', showarrow=False, font=dict(color='blue', size=12), xref='x1', yref='y1')
        fig.add_annotation(text=f"최상<br>{best_p:,.0f}", ax=0, ay=0, x=dates[1], y=best_p, xshift=15, yshift=5, align='left', showarrow=False, font=dict(color='green', size=11), xref='x1', yref='y1')
        fig.add_annotation(text=f"최악<br>{worst_p:,.0f}", ax=0, ay=0, x=dates[1], y=worst_p, xshift=15, yshift=-5, align='left', showarrow=False, font=dict(color='red', size=11), xref='x1', yref='y1')
    strategy_map = { "적극 매수": "강한 상승 추세에 동참하는 전략을 고려해볼 수 있습니다.", "비중 확대": "추세 추종 및 분할 매수 전략이 유효할 수 있습니다.", "중립": "시장 방향성이 명확해질 때까지 관망하거나, 박스권 매매를 고려할 수 있습니다.", "비중 축소": "현금 비중을 늘리고, 기술적 반등 시 비중을 줄이는 전략을 고려해볼 수 있습니다.", "적극 매도": "위험 관리(손절)가 최우선이며, 보유 자산 축소를 적극적으로 고려해야 합니다." }
    strategy_text = f"💡 <b>전략 제안:</b> {strategy_map.get(opinion.split(' ')[0], '현재 시장 상황에 맞는 신중한 접근이 필요합니다.')}<br><br>"
    if target_p is not None:
        strategy_text += f"∙ <b>목표가:</b> 향후 {f_days}일 예상 목표가는 '{target_p:,.0f}pt' 입니다.<br>"
        strategy_text += f"∙ <b>위험 관리선:</b> '{worst_p:,.0f}pt' 하회 시 추세 전환 가능성을 염두에 두어야 합니다."
    fig.add_annotation(text=strategy_text, align='left', showarrow=False, xref="paper", yref="paper", x=0.58, y=0.4, xanchor='left', yanchor='top', font=dict(size=14))

    # --- 5. 최종 레이아웃 업데이트 ---
    fig.update_layout(height=1000, showlegend=False, plot_bgcolor='white', paper_bgcolor='white', margin=dict(t=120, b=50, l=50, r=50),
                      xaxis=dict(domain=[0.05, 0.5], anchor='y1', showline=True, linecolor='lightgrey', zeroline=False),
                      yaxis=dict(domain=[0.1, 0.4], anchor='x1', showline=False, gridcolor='rgba(0,0,0,0.05)', zeroline=False, tickformat=',.0f'),
                      font=dict(family="Nanum Gothic, Malgun Gothic, sans-serif"))
    fig.add_annotation(text="<b>미래 가격 시나리오</b>", xref="paper", yref="paper", x=0.275, y=0.42, showarrow=False, font=dict(size=20), xanchor="center")
    fig.add_annotation(text="<b>구체적인 투자 전략 가이드</b>", xref="paper", yref="paper", x=0.58, y=0.42, showarrow=False, font=dict(size=20), xanchor="left")
    if advisor_info:
        info_text = f"※ 본 분석은 최고 성능 모델인 <b>{advisor_info['best_model_name']}</b>의 예측(R²: {advisor_info['r2_score']:.2f}, RMSE: {advisor_info['rmse']:,.2f})을 기반으로 생성되었습니다."
        fig.add_annotation(text=info_text, xref="paper", yref="paper", x=0.05, y=0.01, showarrow=False, xanchor='left', yanchor='bottom', font=dict(size=10, color="grey"))
        
    # 파일 저장
    clean_target_col = target_col.replace(' ', '').replace('/', '')
    save_chart(fig, project_name, f"{clean_target_col}_AI_Trading_Advisor", f"{target_col} AI Trading Advisor")


def run_advisor_pipeline(all_results, all_predictions, y_test, target_col, forecast_days, project_name):
    """
    AI 어드바이저 데이터 생성 및 시각화 파이프라인을 실행합니다.
    """
    # 1. 데이터 생성
    advisor_data = generate_advisor_data(all_results, all_predictions, y_test, target_col, forecast_days)
    
    # 2. 시각화 (데이터가 성공적으로 생성된 경우에만)
    if advisor_data:
        visualize_trading_advisor_plotly(advisor_data, project_name)