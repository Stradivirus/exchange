# =========================================================
# 0) 환경 설정 (CONFIG)
# =========================================================
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio
from sqlalchemy import create_engine
from datetime import datetime, timedelta
import os
import warnings

# --- 경고 메시지 억제 ---
warnings.filterwarnings('ignore', category=UserWarning)

# --- 폰트 설정 (gu_oil_common.py 방식 적용) ---
FONT_PATH = 'malgun.ttf'
fm.fontManager.addfont(FONT_PATH)
korean_font = fm.FontProperties(fname=FONT_PATH)

# matplotlib 폰트 설정
plt.rcParams['font.family'] = korean_font.get_name()
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['font.size'] = 10
plt.style.use('seaborn-v0_8-whitegrid')

PG_HOST = '64.110.115.12'
PG_DB   = 'exchange'
PG_USER = 'exchange_admin'
PG_PW   = 'exchange_password'

YEARS_BACK = 10  # 최근 N년

# 색상 설정 (gu_oil_common.py 방식 적용)
COLORS = {
    'grain_index': '#2E7D32',    # 진한 녹색 (곡물지수)
    'usd_krw': '#D84315',        # 진한 주황색 (환율)
    'corn': '#FF9800',           # 주황색 (옥수수)
    'rice': '#4CAF50',           # 녹색 (쌀)
    'wheat': '#795548',          # 갈색 (밀)
    'event_covid': '#F44336',    # 빨간색 (COVID-19)
    'event_fed': '#2196F3',      # 파란색 (Fed 금리)
    'event_trade': '#FF9800',    # 주황색 (무역전쟁)
    'event_war': '#9C27B0'       # 보라색 (러-우 전쟁)
}

# 차트 설정
CHART_CONFIG = {
    'figure_sizes': {'large': (16, 8), 'medium': (12, 6), 'small': (8, 5)},
    'dpi': 300,
    'font_sizes': {
        'title': 18,
        'label': 14,
        'text': 12,
        'annotation': 11,
        'legend': 12
    }
}

# 출력 디렉토리 설정
OUTPUT_DIR = './output'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 이벤트 설정 (gu_oil_common.py 방식 적용)
MAJOR_EVENTS = [
    {
        'start': '2020-02-19', 'end': '2020-04-10', 
        'label': 'COVID-19 팬데믹', 
        'color': COLORS['event_covid'], 
        'type': 'span'
    },
    {
        'start': '2022-03-16', 'end': '2022-12-31', 
        'label': '미국 금리 인상', 
        'color': COLORS['event_fed'], 
        'type': 'span'
    },
    {
        'start': '2018-07-06', 'end': '2019-08-01', 
        'label': '미중 무역전쟁', 
        'color': COLORS['event_trade'], 
        'type': 'span'
    },
    {
        'start': '2022-02-24', 'end': '2022-06-17', 
        'label': '러시아-우크라이나 전쟁', 
        'color': COLORS['event_war'], 
        'type': 'span'
    },
]



# =========================================================
# 1) 데이터 로드 (LOAD)
#   - grains: corn, rice, wheat
#   - exchange: usd -> usd_krw
# =========================================================
def get_engine():
    uri = f"postgresql+psycopg2://{PG_USER}:{PG_PW}@{PG_HOST}/{PG_DB}"
    return create_engine(uri)

def load_data(years_back=YEARS_BACK):
    engine = get_engine()
    since = (datetime.now() - timedelta(days=365*years_back)).strftime('%Y-%m-%d')

    q_grains = f"""
        SELECT date, corn, rice, wheat
        FROM grains
        WHERE date >= '{since}'
        ORDER BY date
    """
    q_fx = f"""
        SELECT date, usd AS usd_krw
        FROM exchange
        WHERE date >= '{since}'
        ORDER BY date
    """

    grains = pd.read_sql(q_grains, engine, parse_dates=['date']).set_index('date')
    fx     = pd.read_sql(q_fx,     engine, parse_dates=['date']).set_index('date')

    # 공통 날짜 기준 병합
    df = grains.join(fx, how='inner')
    return df


# =========================================================
# 2) 전처리 (PREPROCESS)
#   - 숫자형 변환, 결측 제거
#   - 합성 곡물지수(grain_index) 생성(동일가중 성과지수 평균)
# =========================================================
def preprocess(df: pd.DataFrame):
    # 숫자형 보정 & 결측 제거
    df = df.copy()  # 복사본 생성하여 warning 방지
    for c in df.columns:
        df[c] = pd.to_numeric(df[c], errors='coerce')
    df = df.dropna()

    # 성과지수(각 곡물 시작=100) -> 동일가중 평균 = grain_index
    grain_cols = ['corn', 'rice', 'wheat']
    perf = df[grain_cols] / df[grain_cols].iloc[0] * 100.0
    df['grain_index'] = perf.mean(axis=1)
    return df


# =========================================================
# 3) 분석 (ANALYZE)
#   - 레벨 상관, 일간 수익률 상관
# =========================================================
def analyze(df: pd.DataFrame):
    cols = ['usd_krw', 'corn', 'rice', 'wheat', 'grain_index']
    corr_level = df[cols].corr()
    ret = df[cols].pct_change().dropna()
    corr_ret = ret.corr()
    print("\n[상관행렬 - 레벨]")
    print(corr_level)
    print("\n[상관행렬 - 일간 수익률]")
    print(corr_ret)

    # 간단 요약
    print("\n[요약 해석]")
    for g in ['corn','rice','wheat','grain_index']:
        print(f" USD/KRW ↔ {g:11s} (레벨):   {corr_level.loc['usd_krw', g]: .3f}")
    for g in ['corn','rice','wheat','grain_index']:
        print(f" USD/KRW ↔ {g:11s} (수익률): {corr_ret.loc['usd_krw', g]: .3f}")
    return corr_level, corr_ret


# =========================================================
# 4) 시각화 (VISUALIZE)
#   - HTML + PNG 출력 지원
#   - (A) 합성 곡물지수 vs 환율(이벤트 강조)
#   - (B) 개별 곡물 레벨
#   - (C) Performance(시작=100) 비교
#   - (D) 히트맵(레벨/수익률)
#   - (E) 산점도 USD/KRW vs 곡물
# =========================================================

def create_html_timeseries_with_events(df: pd.DataFrame, events=MAJOR_EVENTS):
    """곡물지수 vs 환율 시계열 (HTML)"""
    grain_perf = df['grain_index'] / df['grain_index'].iloc[0] * 100
    
    fig = make_subplots(
        rows=1, cols=1,
        specs=[[{"secondary_y": True}]],
        subplot_titles=['곡물지수 vs 원/달러 환율 (주요 이벤트 표시)']
    )
    
    # 곡물지수 플롯
    fig.add_trace(
        go.Scatter(
            x=df.index, 
            y=grain_perf,
            mode='lines',
            name='곡물지수 (성과=100)',
            line=dict(color='green', width=2)
        ),
        secondary_y=False
    )
    
    # 환율 플롯
    fig.add_trace(
        go.Scatter(
            x=df.index, 
            y=df['usd_krw'],
            mode='lines',
            name='USD/KRW',
            line=dict(color='tomato', width=2)
        ),
        secondary_y=True
    )
    
    # 이벤트 영역 표시
    for ev in events:
        fig.add_vrect(
            x0=ev['start'], x1=ev['end'],
            fillcolor=ev['color'], opacity=0.15,
            layer="below", line_width=0,
            annotation_text=ev['label'],
            annotation_position="top left"
        )
    
    fig.update_yaxes(title_text="곡물지수 (성과=100)", secondary_y=False, title_font_color="green")
    fig.update_yaxes(title_text="USD/KRW", secondary_y=True, title_font_color="tomato")
    fig.update_xaxes(title_text="날짜")
    
    fig.update_layout(
        title="곡물지수 vs 원/달러 환율 (주요 이벤트 표시)",
        height=600,
        hovermode='x unified'
    )
    
    return fig

def create_html_grain_levels(df: pd.DataFrame):
    """개별 곡물 가격 레벨 (HTML)"""
    fig = go.Figure()
    
    colors = ['blue', 'orange', 'red']
    grains = ['corn', 'rice', 'wheat']
    grain_names = ['옥수수', '쌀', '밀']
    
    for grain, name, color in zip(grains, grain_names, colors):
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df[grain],
                mode='lines',
                name=name,
                line=dict(color=color, width=2)
            )
        )
    
    fig.update_layout(
        title="개별 곡물 가격 추이",
        xaxis_title="날짜",
        yaxis_title="가격",
        height=500,
        hovermode='x unified'
    )
    
    return fig

def create_html_performance(df: pd.DataFrame):
    """성과 비교 차트 (HTML)"""
    perf_data = {
        '곡물지수': df['grain_index'] / df['grain_index'].iloc[0] * 100,
        'USD/KRW': df['usd_krw'] / df['usd_krw'].iloc[0] * 100
    }
    
    fig = go.Figure()
    
    for name, data in perf_data.items():
        color = 'green' if name == '곡물지수' else 'tomato'
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=data,
                mode='lines',
                name=name,
                line=dict(color=color, width=2)
            )
        )
    
    fig.add_hline(y=100, line_dash="dash", line_color="gray", 
                  annotation_text="시작점 (100)")
    
    fig.update_layout(
        title="성과 비교 (시작점 = 100)",
        xaxis_title="날짜",
        yaxis_title="지수",
        height=500,
        hovermode='x unified'
    )
    
    return fig

def create_html_correlation_heatmap(corr_level: pd.DataFrame, corr_ret: pd.DataFrame):
    """통합 상관관계 히트맵 (HTML) - 2x3 서브플롯"""
    from plotly.subplots import make_subplots
    
    # 한글 컬럼명 매핑
    name_mapping = {
        'usd_krw': 'USD/KRW',
        'corn': '옥수수',
        'rice': '쌀',
        'wheat': '밀',
        'grain_index': '곡물지수'
    }
    
    # 서브플롯 생성
    fig = make_subplots(
        rows=2, cols=3,
        subplot_titles=[
            '전체 상관관계 (레벨)', '개별: USD/KRW vs 곡물지수', '개별: USD/KRW vs 옥수수',
            '전체 상관관계 (수익률)', '개별: USD/KRW vs 쌀', '개별: USD/KRW vs 밀'
        ],
        specs=[[{"secondary_y": False}, {"secondary_y": False}, {"secondary_y": False}],
               [{"secondary_y": False}, {"secondary_y": False}, {"secondary_y": False}]]
    )
    
    # 1. 전체 상관관계 (레벨) - (1,1)
    corr_level_kr = corr_level.copy()
    corr_level_kr.index = [name_mapping.get(idx, idx) for idx in corr_level_kr.index]
    corr_level_kr.columns = [name_mapping.get(col, col) for col in corr_level_kr.columns]
    
    fig.add_trace(
        go.Heatmap(
            z=corr_level_kr.values,
            x=corr_level_kr.columns,
            y=corr_level_kr.index,
            colorscale='RdBu',
            zmid=0, zmin=-1, zmax=1,
            text=corr_level_kr.round(3).values,
            texttemplate="%{text}",
            showscale=False
        ),
        row=1, col=1
    )
    
    # 2. 전체 상관관계 (수익률) - (2,1)
    corr_ret_kr = corr_ret.copy()
    corr_ret_kr.index = [name_mapping.get(idx, idx) for idx in corr_ret_kr.index]
    corr_ret_kr.columns = [name_mapping.get(col, col) for col in corr_ret_kr.columns]
    
    fig.add_trace(
        go.Heatmap(
            z=corr_ret_kr.values,
            x=corr_ret_kr.columns,
            y=corr_ret_kr.index,
            colorscale='RdBu',
            zmid=0, zmin=-1, zmax=1,
            text=corr_ret_kr.round(3).values,
            texttemplate="%{text}",
            showscale=False
        ),
        row=2, col=1
    )
    
    # 3-6. 개별 상관관계
    targets = ['grain_index', 'corn', 'rice', 'wheat']
    positions = [(1, 2), (1, 3), (2, 2), (2, 3)]
    
    for target, pos in zip(targets, positions):
        sub_corr = corr_level.loc[['usd_krw', target], ['usd_krw', target]]
        sub_corr_kr = sub_corr.copy()
        sub_corr_kr.index = [name_mapping.get(idx, idx) for idx in sub_corr_kr.index]
        sub_corr_kr.columns = [name_mapping.get(col, col) for col in sub_corr_kr.columns]
        
        fig.add_trace(
            go.Heatmap(
                z=sub_corr_kr.values,
                x=sub_corr_kr.columns,
                y=sub_corr_kr.index,
                colorscale='RdBu',
                zmid=0, zmin=-1, zmax=1,
                text=sub_corr_kr.round(3).values,
                texttemplate="%{text}",
                showscale=True if pos == (2, 3) else False  # 마지막에만 컬러바 표시
            ),
            row=pos[0], col=pos[1]
        )
    
    fig.update_layout(
        title="상관관계 종합 분석",
        height=800,
        showlegend=False
    )
    
    return fig

def create_html_scatter_combined(df: pd.DataFrame):
    """통합 산점도 (HTML) - 2x2 서브플롯"""
    from plotly.subplots import make_subplots
    
    grain_names = {'corn': '옥수수', 'rice': '쌀', 'wheat': '밀', 'grain_index': '곡물지수'}
    grain_colors = ['#FF9800', '#4CAF50', '#795548', '#2E7D32']  # 옥수수, 쌀, 밀, 곡물지수
    
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=[
            'USD/KRW vs 옥수수', 'USD/KRW vs 쌀',
            'USD/KRW vs 밀', 'USD/KRW vs 곡물지수'
        ]
    )
    
    grains = ['corn', 'rice', 'wheat', 'grain_index']
    positions = [(1, 1), (1, 2), (2, 1), (2, 2)]
    
    for i, (grain, pos) in enumerate(zip(grains, positions)):
        # 상관계수 계산
        corr_val = df['usd_krw'].corr(df[grain])
        
        fig.add_trace(
            go.Scatter(
                x=df['usd_krw'],
                y=df[grain],
                mode='markers',
                name=f'{grain_names[grain]} (r={corr_val:.3f})',
                marker=dict(
                    size=6,
                    color=grain_colors[i],
                    opacity=0.6,
                    line=dict(width=0.5, color='white')
                ),
                showlegend=False
            ),
            row=pos[0], col=pos[1]
        )
        
        # 축 레이블 설정
        fig.update_xaxes(title_text="USD/KRW", row=pos[0], col=pos[1])
        fig.update_yaxes(title_text=grain_names[grain], row=pos[0], col=pos[1])
    
    fig.update_layout(
        title="USD/KRW vs 곡물 산점도 종합 분석",
        height=800,
        showlegend=False
    )
    
    return fig
def plot_timeseries_with_events(df: pd.DataFrame, events=MAJOR_EVENTS, save_png=True):
    fig, ax1 = plt.subplots(figsize=CHART_CONFIG['figure_sizes']['large'])
    ax1.set_title('곡물지수 vs USD/KRW (주요 이벤트 표시)', 
                  fontproperties=korean_font, fontsize=CHART_CONFIG['font_sizes']['title'], pad=20)
    ax1.set_xlabel('날짜', fontproperties=korean_font, fontsize=CHART_CONFIG['font_sizes']['label'])

    grain_perf = df['grain_index'] / df['grain_index'].iloc[0] * 100
    ax1.set_ylabel('곡물지수 (성과=100)', fontproperties=korean_font, 
                   color=COLORS['grain_index'], fontsize=CHART_CONFIG['font_sizes']['label'])
    p1, = ax1.plot(df.index, grain_perf, color=COLORS['grain_index'], 
                   label='곡물지수 (성과)', linewidth=2)

    ax2 = ax1.twinx()
    ax2.set_ylabel('USD/KRW (레벨)', fontproperties=korean_font, 
                   color=COLORS['usd_krw'], fontsize=CHART_CONFIG['font_sizes']['label'])
    p2, = ax2.plot(df.index, df['usd_krw'], color=COLORS['usd_krw'], 
                   label='USD/KRW', linewidth=2, alpha=0.9)

    # 범례에 한글 폰트 적용
    ax1.legend(handles=[p1, p2], loc='upper left', prop=korean_font, 
               fontsize=CHART_CONFIG['font_sizes']['legend'])

    y_max = grain_perf.max()
    y_positions = [y_max*0.9, y_max*0.8, y_max*0.7, y_max*0.6]
    for i, ev in enumerate(events):
        s, e = pd.to_datetime(ev['start']), pd.to_datetime(ev['end'])
        ax1.axvspan(s, e, color=ev['color'], alpha=0.15)
        ax1.text(s, y_positions[i % len(y_positions)], f"  {ev['label']}",
                 fontproperties=korean_font, fontsize=CHART_CONFIG['font_sizes']['annotation'], 
                 color='black', backgroundcolor='white', ha='left', va='center')
    
    plt.tight_layout()
    if save_png:
        plt.savefig(f'{OUTPUT_DIR}/grain_timeseries_events.png', dpi=CHART_CONFIG['dpi'], bbox_inches='tight')
    plt.show()


def plot_grain_levels(df: pd.DataFrame, save_png=True):
    plt.figure(figsize=CHART_CONFIG['figure_sizes']['large'])
    grain_names = {'corn': '옥수수', 'rice': '쌀', 'wheat': '밀'}
    grain_colors = {'corn': COLORS['corn'], 'rice': COLORS['rice'], 'wheat': COLORS['wheat']}
    
    for c in ['corn','rice','wheat']:
        plt.plot(df.index, df[c], label=grain_names[c], 
                color=grain_colors[c], linewidth=2)
    
    plt.title('개별 곡물 가격 추이 (레벨)', fontproperties=korean_font, 
              fontsize=CHART_CONFIG['font_sizes']['title'], pad=12)
    plt.xlabel('날짜', fontproperties=korean_font, fontsize=CHART_CONFIG['font_sizes']['label'])
    plt.ylabel('가격', fontproperties=korean_font, fontsize=CHART_CONFIG['font_sizes']['label'])
    plt.legend(prop=korean_font, fontsize=CHART_CONFIG['font_sizes']['legend'])
    plt.tight_layout()
    if save_png:
        plt.savefig(f'{OUTPUT_DIR}/grain_levels.png', dpi=CHART_CONFIG['dpi'], bbox_inches='tight')
    plt.show()


def plot_performance(df: pd.DataFrame, save_png=True):
    perf = pd.DataFrame({
        '곡물지수_성과': df['grain_index'] / df['grain_index'].iloc[0] * 100,
        'USD_KRW_성과':  df['usd_krw']     / df['usd_krw'].iloc[0]     * 100
    })
    plt.figure(figsize=CHART_CONFIG['figure_sizes']['large'])
    
    colors = [COLORS['grain_index'], COLORS['usd_krw']]
    for i, c in enumerate(perf.columns):
        plt.plot(perf.index, perf[c], label=c, linewidth=2, color=colors[i])
    
    plt.title('성과 비교 (시작점 = 100, 곡물지수 vs USD/KRW)', 
              fontproperties=korean_font, fontsize=CHART_CONFIG['font_sizes']['title'], pad=12)
    plt.xlabel('날짜', fontproperties=korean_font, fontsize=CHART_CONFIG['font_sizes']['label'])
    plt.ylabel('지수', fontproperties=korean_font, fontsize=CHART_CONFIG['font_sizes']['label'])
    plt.axhline(100, linestyle='--', linewidth=1, color='gray')
    plt.legend(prop=korean_font, fontsize=CHART_CONFIG['font_sizes']['legend'])
    plt.tight_layout()
    if save_png:
        plt.savefig(f'{OUTPUT_DIR}/performance_comparison.png', dpi=CHART_CONFIG['dpi'], bbox_inches='tight')
    plt.show()


def plot_heatmaps(corr_level: pd.DataFrame, corr_ret: pd.DataFrame, save_png=True):
    # 한글 이름 매핑
    name_mapping = {
        'usd_krw': 'USD/KRW',
        'corn': '옥수수',
        'rice': '쌀',
        'wheat': '밀',
        'grain_index': '곡물지수'
    }
    
    # 통합 상관관계 차트 (2x3 서브플롯)
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    fig.suptitle('상관관계 종합 분석', fontproperties=korean_font, 
                 fontsize=CHART_CONFIG['font_sizes']['title'] + 4, y=0.95)
    
    # 1. 전체 상관관계 (레벨) - 좌상단
    corr_level_kr = corr_level.copy()
    corr_level_kr.index = [name_mapping.get(idx, idx) for idx in corr_level_kr.index]
    corr_level_kr.columns = [name_mapping.get(col, col) for col in corr_level_kr.columns]
    
    sns.heatmap(corr_level_kr, annot=True, cmap='coolwarm', fmt='.2f', 
                ax=axes[0, 0], cbar_kws={'shrink': 0.8})
    axes[0, 0].set_title('전체 상관관계 (레벨)', fontproperties=korean_font, 
                        fontsize=CHART_CONFIG['font_sizes']['text'])
    axes[0, 0].tick_params(axis='both', labelsize=9)
    
    # 2. 전체 상관관계 (수익률) - 좌하단
    corr_ret_kr = corr_ret.copy()
    corr_ret_kr.index = [name_mapping.get(idx, idx) for idx in corr_ret_kr.index]
    corr_ret_kr.columns = [name_mapping.get(col, col) for col in corr_ret_kr.columns]
    
    sns.heatmap(corr_ret_kr, annot=True, cmap='coolwarm', fmt='.2f', 
                ax=axes[1, 0], cbar_kws={'shrink': 0.8})
    axes[1, 0].set_title('전체 상관관계 (일간 수익률)', fontproperties=korean_font, 
                        fontsize=CHART_CONFIG['font_sizes']['text'])
    axes[1, 0].tick_params(axis='both', labelsize=9)
    
    # 3-6. 개별 상관관계 (USD/KRW vs 각 곡물)
    targets = ['grain_index', 'corn', 'rice', 'wheat']
    target_names = ['곡물지수', '옥수수', '쌀', '밀']
    positions = [(0, 1), (0, 2), (1, 1), (1, 2)]  # 우상단, 우상단2, 우하단, 우하단2
    
    for i, (col, name, pos) in enumerate(zip(targets, target_names, positions)):
        sub_corr = corr_level.loc[['usd_krw', col], ['usd_krw', col]]
        sub_corr_kr = sub_corr.copy()
        sub_corr_kr.index = [name_mapping.get(idx, idx) for idx in sub_corr_kr.index]
        sub_corr_kr.columns = [name_mapping.get(col_name, col_name) for col_name in sub_corr_kr.columns]
        
        sns.heatmap(sub_corr_kr, annot=True, cmap='coolwarm', vmin=-1, vmax=1, fmt=".2f",
                    ax=axes[pos[0], pos[1]], cbar_kws={'shrink': 0.8})
        axes[pos[0], pos[1]].set_title(f'USD/KRW vs {name}', fontproperties=korean_font, 
                                      fontsize=CHART_CONFIG['font_sizes']['text'])
        axes[pos[0], pos[1]].tick_params(axis='both', labelsize=9)
    
    # 모든 축의 레이블에 한글 폰트 적용
    for ax in axes.flat:
        for label in ax.get_xticklabels() + ax.get_yticklabels():
            label.set_fontproperties(korean_font)
    
    plt.tight_layout()
    if save_png:
        plt.savefig(f'{OUTPUT_DIR}/correlation_heatmap_combined.png', dpi=CHART_CONFIG['dpi'], bbox_inches='tight')
    plt.show()


def plot_scatter(df: pd.DataFrame, save_png=True):
    grain_names = {'corn': '옥수수', 'rice': '쌀', 'wheat': '밀', 'grain_index': '곡물지수'}
    grain_colors = {
        'corn': COLORS['corn'], 'rice': COLORS['rice'], 
        'wheat': COLORS['wheat'], 'grain_index': COLORS['grain_index']
    }
    
    # 통합 산점도 차트 (2x2 서브플롯)
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('USD/KRW vs 곡물 산점도 종합 분석', fontproperties=korean_font, 
                 fontsize=CHART_CONFIG['font_sizes']['title'] + 2, y=0.95)
    
    grains = ['corn', 'rice', 'wheat', 'grain_index']
    positions = [(0, 0), (0, 1), (1, 0), (1, 1)]  # 좌상, 우상, 좌하, 우하
    
    for grain, pos in zip(grains, positions):
        ax = axes[pos[0], pos[1]]
        
        # 산점도 그리기
        scatter = ax.scatter(df['usd_krw'], df[grain], 
                           s=25, alpha=0.6, color=grain_colors[grain], 
                           edgecolors='white', linewidth=0.5)
        
        # 제목과 축 레이블
        ax.set_title(f'USD/KRW vs {grain_names[grain]}', 
                    fontproperties=korean_font, 
                    fontsize=CHART_CONFIG['font_sizes']['label'],
                    pad=15)
        ax.set_xlabel('USD/KRW', fontproperties=korean_font, 
                     fontsize=CHART_CONFIG['font_sizes']['text'])
        ax.set_ylabel(grain_names[grain], fontproperties=korean_font, 
                     fontsize=CHART_CONFIG['font_sizes']['text'])
        
        # 그리드 추가
        ax.grid(True, alpha=0.3, linestyle='--')
        
        # 상관계수 표시
        corr_val = df['usd_krw'].corr(df[grain])
        ax.text(0.05, 0.95, f'상관계수: {corr_val:.3f}', 
               transform=ax.transAxes, fontproperties=korean_font,
               fontsize=11, bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        # 축 레이블 폰트 설정
        for label in ax.get_xticklabels() + ax.get_yticklabels():
            label.set_fontsize(10)
    
    plt.tight_layout()
    if save_png:
        plt.savefig(f'{OUTPUT_DIR}/scatter_combined.png', dpi=CHART_CONFIG['dpi'], bbox_inches='tight')
    plt.show()


# =========================================================
# 5) HTML 리포트 생성 (GENERATE HTML REPORT)
# =========================================================
def generate_html_report(df: pd.DataFrame, corr_level: pd.DataFrame, corr_ret: pd.DataFrame):
    """모든 차트를 포함한 통합 HTML 리포트 생성"""
    
    # 개별 HTML 차트 생성
    fig1 = create_html_timeseries_with_events(df)
    fig2 = create_html_grain_levels(df)
    fig3 = create_html_performance(df)
    fig4 = create_html_correlation_heatmap(corr_level, corr_ret)  # 통합 상관관계
    fig5 = create_html_scatter_combined(df)  # 통합 산점도
    
    # HTML 파일들 저장
    fig1.write_html(f"{OUTPUT_DIR}/grain_timeseries_events.html")
    fig2.write_html(f"{OUTPUT_DIR}/grain_levels.html")
    fig3.write_html(f"{OUTPUT_DIR}/performance_comparison.html")
    fig4.write_html(f"{OUTPUT_DIR}/correlation_heatmap_combined.html")
    fig5.write_html(f"{OUTPUT_DIR}/scatter_combined.html")
    
    # 통합 HTML 리포트 생성
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>곡물 가격 vs 원/달러 환율 분석 리포트</title>
        <meta charset="utf-8">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            h1 {{ color: #2E4A88; text-align: center; }}
            h2 {{ color: #4A90A4; margin-top: 40px; }}
            .summary {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
            .chart-container {{ margin: 30px 0; }}
            .correlation-summary {{ background-color: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0; }}
            table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: right; }}
            th {{ background-color: #f2f2f2; }}
        </style>
    </head>
    <body>
        <h1>곡물 가격 vs 원/달러 환율 분석 리포트</h1>
        
        <div class="summary">
            <h2>📊 분석 개요</h2>
            <p><strong>분석 기간:</strong> {df.index.min().strftime('%Y-%m-%d')} ~ {df.index.max().strftime('%Y-%m-%d')}</p>
            <p><strong>데이터 포인트:</strong> {len(df):,}개</p>
            <p><strong>분석 대상:</strong> 옥수수, 쌀, 밀 가격 vs USD/KRW 환율</p>
            <p><strong>주요 분석:</strong> 가격 상관관계, 성과 비교, 이벤트 영향 분석</p>
        </div>

        <div class="correlation-summary">
            <h3>🔍 주요 상관관계 (레벨)</h3>
            <ul>
                <li>USD/KRW ↔ 옥수수: {corr_level.loc['usd_krw', 'corn']:.3f}</li>
                <li>USD/KRW ↔ 쌀: {corr_level.loc['usd_krw', 'rice']:.3f}</li>
                <li>USD/KRW ↔ 밀: {corr_level.loc['usd_krw', 'wheat']:.3f}</li>
                <li>USD/KRW ↔ 곡물지수: {corr_level.loc['usd_krw', 'grain_index']:.3f}</li>
            </ul>
        </div>

        <div class="chart-container">
            <h2>1. 곡물지수 vs 환율 (이벤트 표시)</h2>
            {fig1.to_html(include_plotlyjs=True, div_id="chart1")}
        </div>

        <div class="chart-container">
            <h2>2. 개별 곡물 가격 추이</h2>
            {fig2.to_html(include_plotlyjs=False, div_id="chart2")}
        </div>

        <div class="chart-container">
            <h2>3. 성과 비교 (시작점 = 100)</h2>
            {fig3.to_html(include_plotlyjs=False, div_id="chart3")}
        </div>

        <div class="chart-container">
            <h2>4. 상관관계 종합 분석</h2>
            {fig4.to_html(include_plotlyjs=False, div_id="chart4")}
        </div>

        <div class="chart-container">
            <h2>5. 산점도 종합 분석</h2>
            {fig5.to_html(include_plotlyjs=False, div_id="chart5")}
        </div>

        <div class="summary">
            <h2>📈 분석 결과 요약</h2>
            <p>이 리포트는 곡물 가격(옥수수, 쌀, 밀)과 원/달러 환율 간의 관계를 다각도로 분석합니다.</p>
            <p>주요 경제 이벤트(COVID-19, 미국 금리 인상, 미중 무역전쟁, 러-우 전쟁)가 시장에 미친 영향을 시각화하여 보여줍니다.</p>
            <p>상관관계 분석을 통해 각 곡물과 환율 간의 연관성을 정량적으로 파악할 수 있습니다.</p>
            <p><strong>개선사항:</strong> 상관관계와 산점도 분석을 통합하여 더 효율적인 시각화를 제공합니다.</p>
        </div>

        <footer style="margin-top: 50px; text-align: center; color: #666;">
            <p>Generated on """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """</p>
        </footer>
    </body>
    </html>
    """
    
    # 통합 리포트 저장
    with open(f"{OUTPUT_DIR}/grain_analysis_report.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"\n✅ HTML 리포트가 생성되었습니다: {OUTPUT_DIR}/grain_analysis_report.html")
    return html_content

# =========================================================
# 6) 실행 (RUN)
# =========================================================
if __name__ == "__main__":
    print("=" * 60)
    print("📊 곡물 가격 vs 원/달러 환율 분석 시작")
    print("=" * 60)
    
    # (1) LOAD
    print("\n🔄 데이터 로딩 중...")
    raw = load_data()

    if raw.empty:
        raise SystemExit("❌ 데이터가 없습니다. 스키마/기간을 확인하세요.")

    print(f"✅ 데이터 로드 완료: {len(raw):,}개 데이터 포인트")
    print("\n--- 로드된 데이터 (최근 5행) ---")
    print(raw.tail())

    # (2) PREPROCESS
    print("\n🔄 데이터 전처리 중...")
    df = preprocess(raw)
    print(f"✅ 전처리 완료: {len(df):,}개 데이터 포인트 (결측치 제거 후)")

    # (3) ANALYZE
    print("\n🔄 상관관계 분석 중...")
    corr_level, corr_ret = analyze(df)

    # (4) GENERATE HTML REPORT
    print("\n🔄 HTML 리포트 생성 중...")
    generate_html_report(df, corr_level, corr_ret)

    # (5) GENERATE PNG CHARTS
    print("\n🔄 PNG 차트 생성 중...")
    print("📈 시계열 차트 (이벤트 표시)...")
    plot_timeseries_with_events(df)
    
    print("📈 개별 곡물 가격 차트...")
    plot_grain_levels(df)
    
    print("📈 성과 비교 차트...")
    plot_performance(df)
    
    print("📈 상관관계 히트맵...")
    plot_heatmaps(corr_level, corr_ret)
    
    print("📈 산점도 차트...")
    plot_scatter(df)

    print("\n" + "=" * 60)
    print("✅ 모든 분석 완료!")
    print(f"📁 결과 파일 위치: {OUTPUT_DIR}/")
    print("📄 HTML 리포트: grain_analysis_report.html")
    print("🖼️  PNG 차트들:")
    print("   - grain_timeseries_events.png (시계열)")
    print("   - grain_levels.png (개별 곡물)")
    print("   - performance_comparison.png (성과 비교)")
    print("   - correlation_heatmap_combined.png (상관관계 통합)")
    print("   - scatter_combined.png (산점도 통합)")
    print("=" * 60)
