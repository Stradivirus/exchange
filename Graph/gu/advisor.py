import os
import sys
import pandas as pd
import numpy as np

# [필수] 상위 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from config import OUTPUT_PATHS
except ImportError:
    OUTPUT_PATHS = {"gu": "../outputs/gu"}

def run_advisor_pipeline(df, target_col, predictions, project_name, *args, **kwargs):
    """AI 트레이딩 조언 생성 파이프라인"""
    print("🧠 AI 어드바이저 분석 중...")
    
    try:
        advice_content = generate_advice_logic(df, target_col, predictions)
        save_advice_to_html(advice_content, project_name) # 여기서 에러 났었음
        return advice_content
    except Exception as e:
        print(f"⚠️ 어드바이저 실행 중 오류: {e}")
        return "분석 실패"

def generate_advice_logic(df, target_col, predictions):
    """실제 분석 로직"""
    advice = []
    
    if df is None: return "데이터가 없습니다."
    if isinstance(df, dict): return "데이터 오류 (Dict)"
    try:
        if df.empty: return "데이터가 비어있습니다."
    except: return "데이터 오류"

    # 1. 현재 시장 동향
    try:
        last_price = df[target_col].iloc[-1]
        prev_price = df[target_col].iloc[-2]
        change = last_price - prev_price
        pct_change = (change / prev_price) * 100 if prev_price != 0 else 0
        trend_emoji = "🔺" if change > 0 else "blau" if change < 0 else "➖"
        
        advice.append(f"<h2>🤖 AI 트레이딩 어드바이저 리포트 ({project_name_to_title(target_col)})</h2>")
        advice.append(f"<h3>1. 현재 시장 동향 ({df.index[-1].strftime('%Y-%m-%d')})</h3>")
        advice.append(f"<ul><li><b>현재가:</b> {last_price:,.2f}</li><li><b>전일대비:</b> {change:+,.2f} ({pct_change:+.2f}%) {trend_emoji}</li></ul>")
    except Exception as e:
        advice.append(f"<p>현재가 정보 오류: {e}</p>")
    
    # 2. 모델별 예측 종합
    advice.append(f"<h3>2. AI 모델 예측 종합</h3><ul>")
    up_votes, total_models = 0, 0
    if not isinstance(predictions, dict): predictions = {}

    for model_name, pred_series in predictions.items():
        if pred_series is None or isinstance(pred_series, (dict, int, float, str)): continue
        try:
            if hasattr(pred_series, 'empty') and pred_series.empty: continue
            if len(pred_series) == 0: continue
            
            future_mean = np.mean(pred_series)
            if future_mean > last_price:
                direction = "상승 📈"
                up_votes += 1
            elif future_mean < last_price:
                direction = "하락 📉"
            else:
                direction = "보합 ➡️"
            
            total_models += 1
            advice.append(f"<li><b>{model_name}:</b> 향후 {direction} 예측 (평균예상가: {future_mean:,.2f})</li>")
        except: continue
    
    advice.append("</ul>")
    
    # 3. 최종 결론
    advice.append(f"<h3>3. 최종 투자 의견</h3>")
    if total_models > 0:
        bullish_ratio = up_votes / total_models
        if bullish_ratio >= 0.7:
            final_call, color = "매수 우위 (Strong Buy) 🚀", "red"
        elif bullish_ratio <= 0.3:
            final_call, color = "매도 우위 (Strong Sell) 💧", "blue"
        else:
            final_call, color = "중립/관망 (Hold) ✋", "gray"
        advice.append(f"<p>AI 모델 <b>{total_models}개 중 {up_votes}개</b> 상승 예측</p>")
        advice.append(f"<h4 style='color:{color}; border:2px solid {color}; padding:10px; display:inline-block;'>결론: {final_call}</h4>")
    else:
        advice.append("<p>결론을 내릴 수 없습니다.</p>")
        
    return "\n".join(advice)

def save_advice_to_html(content, project_name):
    """HTML 파일 저장 (파일명 안전하게 처리)"""
    try:
        # [수정] 파일명에 슬래시(/)가 있으면 언더바(_)로 교체
        safe_name = project_name.replace("/", "_")
        
        output_dir = os.path.join(OUTPUT_PATHS["gu"], safe_name)
        os.makedirs(output_dir, exist_ok=True)
        
        filename = f"{safe_name}_AI_Trading_Advisor.html"
        filepath = os.path.join(output_dir, filename)
        
        html_template = f"""<!DOCTYPE html><html><head><meta charset="UTF-8">
        <style>body {{ font-family: Arial, sans-serif; line-height: 1.6; padding: 20px; max-width: 800px; margin: 0 auto; }}
        h2 {{ border-bottom: 2px solid #333; padding-bottom: 10px; }} ul {{ background-color: #f9f9f9; padding: 15px 40px; border-radius: 5px; }}</style>
        </head><body>{content}</body></html>"""
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_template)
            
        print(f"✅ 어드바이저 리포트 저장 완료: {filename}")
        
    except Exception as e:
        print(f"⚠️ HTML 저장 실패: {e}")

def project_name_to_title(col_name):
    if 'USD' in col_name: return "원/달러 환율"
    if 'SP' in col_name: return "S&P 500"
    if 'Crude' in col_name: return "WTI 원유"
    return col_name