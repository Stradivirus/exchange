# ==========================================================================
# 시각화 헬퍼 함수 (Visualization Helper Functions)
# ==========================================================================

import plotly.graph_objects as go
import datetime
import os

def create_output_folder(project_name):
    """
    프로젝트별 출력 폴더를 생성합니다.
    """
    folder_path = f"../outputs/gu/{project_name}"
    os.makedirs(folder_path, exist_ok=True)
    return folder_path

def get_global_chart_events():
    """
    차트 시각화에 사용할 주요 글로벌 경제 및 정치 이벤트를 반환합니다.
    """
    return [
        {'date': '2016-11-08', 'label': '트럼프 당선', 'color': '#2F2F2F', 'type': 'line'},
        {'start': '2018-07-06', 'end': '2019-08-01', 'label': '미중 무역전쟁', 'color': '#FF6600', 'type': 'span'},
        {'start': '2020-02-19', 'end': '2020-04-10', 'label': '코로나19 팬데믹', 'color': '#DC143C', 'type': 'span'},
        {'start': '2020-04-11', 'end': '2022-03-15', 'label': '경기 회복', 'color': '#228B22', 'type': 'span'},
        {'start': '2022-02-24', 'end': '2022-06-17', 'label': '러시아-우크라이나 전쟁', 'color': '#9932CC', 'type': 'span'},
        {'start': '2022-03-16', 'end': '2022-12-31', 'label': '긴축 정책', 'color': '#A0522D', 'type': 'span'},
        {'start': '2023-01-01', 'end': '2024-12-31', 'label': 'AI 붐', 'color': '#008080', 'type': 'span'}
    ]

def save_chart(fig, project_name, filename, chart_title):
    """
    차트를 HTML과 PNG 파일로 저장합니다.
    """
    try:
        # 출력 폴더 생성
        output_folder = create_output_folder(project_name)
        
        # 파일명 정리 (특수문자 제거)
        clean_filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_')).rstrip()
        clean_filename = clean_filename.replace(' ', '_')
        
        # HTML 저장
        html_path = f"{output_folder}/{clean_filename}.html"
        fig.write_html(html_path)
        
        # PNG 저장 (kaleido 필요: pip install kaleido)
        try:
            png_path = f"{output_folder}/{clean_filename}.png"
            fig.write_image(png_path, width=1200, height=800, scale=2)
            print(f"✅ 저장 완료: {clean_filename}.html, {clean_filename}.png")
        except Exception as png_error:
            print(f"⚠️  PNG 저장 실패 (HTML만 저장됨): {png_error}")
            print(f"   PNG 저장을 위해서는 'pip install kaleido' 실행이 필요합니다.")
            print(f"✅ HTML 저장 완료: {clean_filename}.html")
            
    except Exception as e:
        print(f"❌ 차트 저장 실패: {e}")

def plot_macro_relationship_chart(df, main_col, main_label, main_color, sub_col, sub_label, sub_color, title, project_name=None, save_name=None):
    """
    두 개의 거시 경제 지표를 이중 축(dual-axis) 차트로 시각화하고 파일로 저장합니다.
    """
    from plotly.subplots import make_subplots
    
    print(f"📊 생성 중: {title}")
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    fig.add_trace(
        go.Scatter(x=df.index, y=df[main_col], name=main_label, 
                  line=dict(color=main_color, width=2)),
        secondary_y=False,
    )
    
    fig.add_trace(
        go.Scatter(x=df.index, y=df[sub_col], name=sub_label, 
                  line=dict(color=sub_color, width=2, dash='dash')),
        secondary_y=True,
    )
    
    # 이벤트 표시
    y_start, y_range = df[main_col].max() * 1.05, df[main_col].max() - df[main_col].min()
    y_step = y_range * 0.04
    
    events = get_global_chart_events()
    for i, event in enumerate(events):
        current_y = y_start - i * y_step
        
        if event['type'] == 'line':
            event_date = datetime.datetime.strptime(event['date'], '%Y-%m-%d')
            fig.add_vline(x=event_date, line_width=1.5, line_dash="dash", line_color=event['color'])
            fig.add_annotation(x=event_date, y=current_y, xref="x", yref="y",
                             text=event['label'], showarrow=False,
                             font=dict(color="black", size=11),
                             bgcolor="rgba(255, 255, 255, 0.75)")
        elif event['type'] == 'span':
            start_date, end_date = datetime.datetime.strptime(event['start'], '%Y-%m-%d'), datetime.datetime.strptime(event['end'], '%Y-%m-%d')
            fig.add_vrect(x0=start_date, x1=end_date, fillcolor=event['color'], opacity=0.15, line_width=0)
            mid_date = start_date + (end_date - start_date) / 2
            fig.add_annotation(x=mid_date, y=current_y, xref="x", yref="y",
                             text=event['label'], showarrow=False,
                             font=dict(color="black", size=11),
                             bgcolor="rgba(255, 255, 255, 0.75)")
    
    correlation = df[[main_col, sub_col]].corr().iloc[0, 1]
    fig.update_layout(
        title=dict(text=f"{title}<br>상관계수: {correlation:.3f}", x=0.5),
        yaxis_title=main_label,
        yaxis2_title=sub_label,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    # 파일 저장
    if project_name and save_name:
        save_chart(fig, project_name, save_name, title)
