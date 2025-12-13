import os
import warnings
warnings.filterwarnings('ignore')

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.dates as mdates
from datetime import datetime
import base64
from io import BytesIO
import matplotlib.font_manager as fm  # 추가
from matplotlib.font_manager import FontProperties

# 머신러닝 라이브러리
from sklearn.model_selection import train_test_split, TimeSeriesSplit, GridSearchCV, cross_val_score
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score, mean_absolute_percentage_error
from sklearn.linear_model import LinearRegression, Ridge, Lasso, ElasticNet
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, AdaBoostRegressor
from sklearn.svm import SVR
from sklearn.tree import DecisionTreeRegressor
from sklearn.neighbors import KNeighborsRegressor

# 시계열 특화 모델
try:
    from sklearn.ensemble import HistGradientBoostingRegressor
    import xgboost as xgb
    import lightgbm as lgb
    ADVANCED_MODELS = True
except ImportError:
    print("⚠️ XGBoost 또는 LightGBM이 설치되지 않았습니다. 기본 모델만 사용합니다.")
    ADVANCED_MODELS = False

try:
    from pymongo import MongoClient
    MONGO_AVAILABLE = True
except ImportError:
    print("⚠️ MongoDB 연결 불가. 테스트 데이터를 사용합니다.")
    MONGO_AVAILABLE = False

from scipy import stats
from scipy.stats import jarque_bera, shapiro
import itertools

# 폰트 설정
malgun_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'malgun.ttf'))
if os.path.exists(malgun_path):
    fontprop = FontProperties(fname=malgun_path)
else:
    fontprop = None

plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['font.size'] = 10

# 출력 디렉토리 설정
OUTPUT_DIR = "../outputs/kim/news"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- 차트 저장 및 HTML 생성 함수 추가 ---
def save_chart_and_html(fig, filename, title=None):
    """차트를 PNG로 저장하고, 같은 이미지를 포함한 HTML도 저장"""
    png_path = os.path.join(OUTPUT_DIR, f"{filename}.png")
    html_path = os.path.join(OUTPUT_DIR, f"{filename}.html")

    # 폰트 prop 적용
    if fontprop is not None:
        for ax in fig.get_axes():
            for label in (ax.get_xticklabels() + ax.get_yticklabels()):
                label.set_fontproperties(fontprop)
            ax.title.set_fontproperties(fontprop)
            ax.xaxis.label.set_fontproperties(fontprop)
            ax.yaxis.label.set_fontproperties(fontprop)

    fig.savefig(png_path, dpi=300, bbox_inches='tight')
    buffer = BytesIO()
    fig.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.read()).decode()
    plt.close(fig)

    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>{title or filename}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            img {{ display: block; margin: 20px auto; max-width: 100%; height: auto; }}
        </style>
    </head>
    <body>
        <h2>{title or filename}</h2>
        <img src="data:image/png;base64,{image_base64}" alt="{filename}">
    </body>
    </html>
    """
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_template)
    print(f"📊 차트 저장: {png_path}")
    print(f"📝 HTML 저장: {html_path}")

# MongoDB 데이터 로드 함수
def load_news_sentiment_data():
    """MongoDB에서 뉴스심리지수와 환율 데이터를 로드하고 병합"""
    if not MONGO_AVAILABLE:
        return create_test_data()
    
    MONGO_URI = "mongodb+srv://stradivirus:1q2w3e4r6218@cluster0.e7rvfpz.mongodb.net/exchange_all?retryWrites=true&w=majority&appName=Cluster0"
    DB_NAME = "exchange_all"
    
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    
    try:
        print("🔗 MongoDB 연결 성공")
        collections = db.list_collection_names()
        
        sentiment_df = pd.DataFrame()
        
        # 뉴스심리지수 데이터 로드
        if "news_sentiment" in collections:
            cursor = db["news_sentiment"].find({'item_name': '뉴스심리지수'}, {"_id": 0, "date": 1, "value": 1})
            temp_df = pd.DataFrame(list(cursor))
            if not temp_df.empty:
                temp_df["date"] = pd.to_datetime(temp_df["date"])
                sentiment_df = temp_df.rename(columns={"value": "SENTIMENT"}).set_index("date")
                print(f"✅ 뉴스심리지수 {len(sentiment_df)}건 로드 성공!")
        
        # USD/KRW 환율 데이터 로드
        usd_df = pd.DataFrame()
        possible_usd_collections = ["USD", "usd", "USD_KRW", "USDKRW"]
        
        for collection_name in possible_usd_collections:
            if collection_name in collections:
                sample = db[collection_name].find_one()
                if sample:
                    date_fields = [k for k in sample.keys() if 'date' in k.lower()]
                    rate_fields = [k for k in sample.keys() if any(word in k.lower() for word in ['rate', 'price', 'value', 'close'])]
                    
                    if date_fields and rate_fields:
                        cursor = db[collection_name].find({}, {"_id": 0, date_fields[0]: 1, rate_fields[0]: 1})
                        temp_df = pd.DataFrame(list(cursor))
                        if not temp_df.empty:
                            temp_df["date"] = pd.to_datetime(temp_df[date_fields[0]])
                            usd_df = temp_df.rename(columns={rate_fields[0]: "USD_KRW"}).set_index("date")
                            break
        
        # 데이터 병합
        if not sentiment_df.empty and not usd_df.empty:
            merged_df = pd.concat([sentiment_df, usd_df], axis=1, join='inner')
            merged_df = merged_df.sort_index()
            
            for col in merged_df.columns:
                merged_df[col] = pd.to_numeric(merged_df[col], errors='coerce')
            
            merged_df = merged_df.dropna()
            print(f"✅ 데이터 병합 완료: {merged_df.shape}")
            client.close()
            return merged_df
        else:
            print("❌ 필요한 데이터를 찾을 수 없습니다. 테스트 데이터를 생성합니다.")
            client.close()
            return create_test_data()
    
    except Exception as e:
        print(f"❌ 데이터 로드 중 오류 발생: {e}. 테스트 데이터를 생성합니다.")
        client.close()
        return create_test_data()

# 테스트 데이터 생성 함수
def create_test_data():
    """현실적인 뉴스심리지수와 환율 테스트 데이터 생성"""
    np.random.seed(42)
    
    dates = pd.date_range(start='2020-01-01', end='2024-09-01', freq='D')
    n_days = len(dates)
    
    # 뉴스심리지수 생성 (0-100 범위)
    sentiment_trend = 50 + 10 * np.sin(np.arange(n_days) * 2 * np.pi / 365.25)
    sentiment_cycle = 5 * np.sin(np.arange(n_days) * 2 * np.pi / 30)
    sentiment_noise = np.random.normal(0, 8, n_days)
    
    # COVID-19 특수 상황
    covid_effect = np.zeros(n_days)
    covid_start = (pd.to_datetime('2020-03-01') - dates[0]).days
    covid_end = (pd.to_datetime('2020-12-31') - dates[0]).days
    covid_effect[covid_start:covid_end] = -20 * np.exp(-(np.arange(covid_end - covid_start) / 100))
    
    sentiment = sentiment_trend + sentiment_cycle + sentiment_noise + covid_effect
    sentiment = np.clip(sentiment, 0, 100)
    
    # USD/KRW 환율 생성 (심리지수와 역상관)
    usd_base = 1200
    usd_trend = 100 * np.cumsum(np.random.normal(0, 0.001, n_days))
    usd_sentiment_effect = -1.5 * (sentiment - 50)
    usd_noise = np.random.normal(0, 15, n_days)
    
    # COVID-19 환율 급등 효과
    covid_fx_effect = np.zeros(n_days)
    covid_fx_effect[covid_start:covid_start + 60] = 150 * np.exp(-(np.arange(60) / 30))
    
    usd_krw = usd_base + usd_trend + usd_sentiment_effect + usd_noise + covid_fx_effect
    usd_krw = np.clip(usd_krw, 1000, 1600)
    
    test_df = pd.DataFrame({
        'SENTIMENT': sentiment,
        'USD_KRW': usd_krw
    }, index=dates)
    
    return test_df

# 피처 엔지니어링 함수
def create_features(df, target_col='USD_KRW', sentiment_col='SENTIMENT'):
    """고급 피처 엔지니어링"""
    print("🔧 피처 엔지니어링 시작...")
    
    feature_df = df.copy()
    
    # 1. 기본 통계 피처
    for col in [sentiment_col, target_col]:
        if col in feature_df.columns:
            # 이동평균
            for window in [3, 5, 7, 10, 20]:
                feature_df[f'{col}_MA{window}'] = feature_df[col].rolling(window=window).mean()
            
            # 이동표준편차
            for window in [5, 10, 20]:
                feature_df[f'{col}_STD{window}'] = feature_df[col].rolling(window=window).std()
            
            # 변화율
            for lag in [1, 2, 3, 5]:
                feature_df[f'{col}_PCT{lag}'] = feature_df[col].pct_change(lag)
    
    # 2. 상호작용 피처
    if sentiment_col in feature_df.columns and target_col in feature_df.columns:
        feature_df['SENTIMENT_FX_RATIO'] = feature_df[sentiment_col] / feature_df[target_col]
        feature_df['SENTIMENT_FX_PRODUCT'] = feature_df[sentiment_col] * feature_df[target_col]
    
    # 3. 기술적 지표
    if target_col in feature_df.columns:
        # RSI
        delta = feature_df[target_col].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        feature_df['RSI'] = 100 - (100 / (1 + rs))
    
    # 4. 시간 피처
    feature_df['MONTH'] = feature_df.index.month
    feature_df['QUARTER'] = feature_df.index.quarter
    feature_df['DAY_OF_WEEK'] = feature_df.index.dayofweek
    
    # 결측치 제거
    feature_df = feature_df.dropna()
    
    print(f"✅ 피처 엔지니어링 완료: {feature_df.shape[1]}개 피처, {len(feature_df)}개 샘플")
    return feature_df

# 모델 정의
def get_models():
    """사용할 모델들과 하이퍼파라미터 정의"""
    models = {}
    
    # 선형 모델들
    models['Ridge'] = {
        'model': Ridge(),
        'params': {'alpha': [0.1, 1.0, 10.0, 100.0]}
    }
    
    models['RandomForest'] = {
        'model': RandomForestRegressor(random_state=42, n_jobs=-1),
        'params': {
            'n_estimators': [100, 200],
            'max_depth': [5, 10, None],
            'min_samples_split': [2, 5]
        }
    }
    
    models['GradientBoosting'] = {
        'model': GradientBoostingRegressor(random_state=42),
        'params': {
            'n_estimators': [100, 200],
            'learning_rate': [0.05, 0.1, 0.2],
            'max_depth': [3, 5]
        }
    }
    
    # 고급 모델들 (사용 가능한 경우)
    if ADVANCED_MODELS:
        try:
            models['XGBoost'] = {
                'model': xgb.XGBRegressor(random_state=42, eval_metric='rmse'),
                'params': {
                    'n_estimators': [100, 200],
                    'learning_rate': [0.05, 0.1],
                    'max_depth': [3, 5]
                }
            }
        except:
            pass
        
        try:
            models['LightGBM'] = {
                'model': lgb.LGBMRegressor(random_state=42, verbosity=-1),
                'params': {
                    'n_estimators': [100, 200],
                    'learning_rate': [0.05, 0.1],
                    'max_depth': [3, 5]
                }
            }
        except:
            pass
    
    return models

# 모델 학습 및 평가
def train_and_evaluate_models(X_train, X_test, y_train, y_test, models):
    """모든 모델을 학습하고 평가"""
    print("🚀 모델 학습 및 평가 시작...")
    
    results = []
    trained_models = {}
    tscv = TimeSeriesSplit(n_splits=3)
    
    for name, model_info in models.items():
        print(f" 📈 {name} 학습 중...")
        
        try:
            # 하이퍼파라미터 튜닝
            grid_search = GridSearchCV(
                model_info['model'], 
                model_info['params'], 
                cv=tscv, 
                scoring='neg_mean_squared_error',
                n_jobs=-1
            )
            
            grid_search.fit(X_train, y_train)
            best_model = grid_search.best_estimator_
            
            # 예측
            y_pred_test = best_model.predict(X_test)
            
            # 평가
            rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))
            mae = mean_absolute_error(y_test, y_pred_test)
            r2 = r2_score(y_test, y_pred_test)
            mape = mean_absolute_percentage_error(y_test, y_pred_test) * 100
            
            results.append({
                'Model': name,
                'RMSE': rmse,
                'MAE': mae,
                'R2': r2,
                'MAPE': mape
            })
            
            trained_models[name] = {
                'model': best_model,
                'predictions': y_pred_test
            }
            
        except Exception as e:
            print(f" ⚠️ {name} 학습 중 오류: {e}")
            continue
    
    results_df = pd.DataFrame(results)
    results_df = results_df.sort_values('RMSE').reset_index(drop=True)
    
    print("✅ 모델 학습 및 평가 완료")
    return results_df, trained_models

# 시각화 함수들
def plot_data_overview(df):
    """데이터 개요 시각화"""
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # 시계열 플롯
    axes[0, 0].plot(df.index, df['SENTIMENT'], label='뉴스심리지수', alpha=0.7)
    axes[0, 0].set_title('뉴스심리지수 시계열', fontweight='bold')
    axes[0, 0].set_ylabel('심리지수')
    axes[0, 0].grid(True, alpha=0.3)
    
    axes[0, 1].plot(df.index, df['USD_KRW'], label='USD/KRW', color='red', alpha=0.7)
    axes[0, 1].set_title('USD/KRW 환율 시계열', fontweight='bold')
    axes[0, 1].set_ylabel('환율 (원)')
    axes[0, 1].grid(True, alpha=0.3)
    
    # 상관관계 산점도
    axes[1, 0].scatter(df['SENTIMENT'], df['USD_KRW'], alpha=0.6)
    axes[1, 0].set_xlabel('뉴스심리지수')
    axes[1, 0].set_ylabel('USD/KRW')
    axes[1, 0].set_title(f'상관관계 (r={df["SENTIMENT"].corr(df["USD_KRW"]):.3f})', fontweight='bold')
    
    # 분포 히스토그램
    axes[1, 1].hist(df['SENTIMENT'], bins=30, alpha=0.7, label='뉴스심리지수')
    axes[1, 1].set_xlabel('뉴스심리지수')
    axes[1, 1].set_ylabel('빈도')
    axes[1, 1].set_title('뉴스심리지수 분포', fontweight='bold')
    
    plt.tight_layout()
    save_chart_and_html(fig, "data_overview", "데이터 개요")

def plot_model_comparison(results_df, trained_models, y_test):
    """모델 비교 시각화"""
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # 1. 모델별 성능 비교 (RMSE)
    top_models = results_df.head(6)
    bars = axes[0, 0].bar(range(len(top_models)), top_models['RMSE'],
                         color=plt.cm.viridis(np.linspace(0, 1, len(top_models))))
    axes[0, 0].set_xlabel('모델')
    axes[0, 0].set_ylabel('Test RMSE')
    axes[0, 0].set_title('모델별 테스트 RMSE 비교', fontweight='bold')
    axes[0, 0].set_xticks(range(len(top_models)))
    axes[0, 0].set_xticklabels(top_models['Model'], rotation=45, ha='right')
    
    # 값 표시
    for i, bar in enumerate(bars):
        height = bar.get_height()
        axes[0, 0].text(bar.get_x() + bar.get_width() / 2., height,
                       f'{height:.2f}', ha='center', va='bottom', fontsize=9)
    
    # 2. R² 점수 비교
    bars = axes[0, 1].bar(range(len(top_models)), top_models['R2'],
                         color=plt.cm.plasma(np.linspace(0, 1, len(top_models))))
    axes[0, 1].set_xlabel('모델')
    axes[0, 1].set_ylabel('Test R²')
    axes[0, 1].set_title('모델별 테스트 R² 비교', fontweight='bold')
    axes[0, 1].set_xticks(range(len(top_models)))
    axes[0, 1].set_xticklabels(top_models['Model'], rotation=45, ha='right')
    
    for i, bar in enumerate(bars):
        height = bar.get_height()
        axes[0, 1].text(bar.get_x() + bar.get_width() / 2., height,
                       f'{height:.3f}', ha='center', va='bottom', fontsize=9)
    
    # 3. 최고 모델 예측 vs 실제
    best_model_name = results_df.iloc[0]['Model']
    best_model_pred = trained_models[best_model_name]['predictions']
    
    axes[1, 0].scatter(y_test, best_model_pred, alpha=0.6, color='blue')
    min_val = min(y_test.min(), best_model_pred.min())
    max_val = max(y_test.max(), best_model_pred.max())
    axes[1, 0].plot([min_val, max_val], [min_val, max_val], 'r--', linewidth=2)
    axes[1, 0].set_xlabel('실제값')
    axes[1, 0].set_ylabel('예측값')
    axes[1, 0].set_title(f'최고 모델({best_model_name}) 예측 vs 실제', fontweight='bold')
    
    r2_score_val = results_df.iloc[0]['R2']
    axes[1, 0].text(0.05, 0.95, f'R² = {r2_score_val:.3f}',
                   transform=axes[1, 0].transAxes, fontsize=12,
                   bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.7))
    
    # 4. 잔차 플롯
    residuals = y_test - best_model_pred
    axes[1, 1].scatter(best_model_pred, residuals, alpha=0.6, color='green')
    axes[1, 1].axhline(y=0, color='red', linestyle='--', linewidth=2)
    axes[1, 1].set_xlabel('예측값')
    axes[1, 1].set_ylabel('잔차 (실제 - 예측)')
    axes[1, 1].set_title(f'최고 모델({best_model_name}) 잔차 플롯', fontweight='bold')
    
    plt.tight_layout()
    save_chart_and_html(fig, "model_comparison", "모델 비교")

def plot_predictions_timeline(df, y_test, best_pred, test_index, model_name):
    """시계열 예측 결과 시각화"""
    fig, ax = plt.subplots(figsize=(16, 8))
    
    # 전체 데이터 (회색)
    ax.plot(df.index, df['USD_KRW'], color='lightgray', alpha=0.5, label='전체 데이터')
    
    # 실제 테스트 데이터 (파란색)
    ax.plot(test_index, y_test, color='blue', linewidth=2, label='실제 테스트 데이터')
    
    # 예측 데이터 (빨간색)
    ax.plot(test_index, best_pred, color='red', linewidth=2, label=f'{model_name} 예측')
    
    ax.set_xlabel('날짜')
    ax.set_ylabel('USD/KRW 환율')
    ax.set_title(f'환율 예측 결과 - {model_name} 모델', fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # 날짜 축 포맷
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
    
    plt.tight_layout()
    save_chart_and_html(fig, "predictions_timeline", f"환율 예측 결과 - {model_name} 모델")

# 메인 실행 함수
def main():
    """메인 실행 함수"""
    print("🚀 뉴스심리지수-환율 예측 최적모델링")
    
    # 1. 데이터 로드
    print("1️⃣ 데이터 로딩")
    df = load_news_sentiment_data()
    
    if df.empty:
        print("❌ 데이터 로드 실패")
        return
    
    print(f"📊 데이터 로드 완료: {df.shape}")
    print(f"📅 분석 기간: {df.index.min().strftime('%Y-%m-%d')} ~ {df.index.max().strftime('%Y-%m-%d')}")
    print(f"📈 뉴스심리지수 평균: {df['SENTIMENT'].mean():.2f}")
    print(f"💰 USD/KRW 평균: {df['USD_KRW'].mean():.2f}원")
    print(f"🔗 상관계수: {df['SENTIMENT'].corr(df['USD_KRW']):.3f}")
    
    plot_data_overview(df)
    
    # 2. 피처 엔지니어링
    print("2️⃣ 피처 엔지니어링")
    feature_df = create_features(df)
    
    if feature_df.empty:
        print("❌ 피처 엔지니어링 실패")
        return
    
    # 타겟 변수와 피처 분리
    target_col = 'USD_KRW'
    feature_cols = [col for col in feature_df.columns if col != target_col]
    X = feature_df[feature_cols]
    y = feature_df[target_col]
    
    # 3. 데이터 분할
    print("3️⃣ 데이터 분할")
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
    
    print(f" 학습 데이터: {len(X_train)}개")
    print(f" 테스트 데이터: {len(X_test)}개")
    
    # 4. 데이터 스케일링
    print("4️⃣ 데이터 스케일링")
    scaler = StandardScaler()
    X_train_scaled = pd.DataFrame(scaler.fit_transform(X_train), columns=X_train.columns, index=X_train.index)
    X_test_scaled = pd.DataFrame(scaler.transform(X_test), columns=X_test.columns, index=X_test.index)
    
    # 5. 모델 학습 및 평가
    print("5️⃣ 모델 학습 및 평가")
    models = get_models()
    print(f" 사용할 모델: {list(models.keys())}")
    
    results_df, trained_models = train_and_evaluate_models(
        X_train_scaled, X_test_scaled, y_train, y_test, models
    )
    
    # 6. 결과 분석
    print("6️⃣ 결과 분석")
    print("🏆 최종 모델 성능 순위:")
    
    for _, row in results_df.iterrows():
        print(f" {row['Model']}: RMSE={row['RMSE']:.4f}, R²={row['R2']:.4f}, MAPE={row['MAPE']:.2f}%")
    
    # 최고 모델 선택
    best_model_name = results_df.iloc[0]['Model']
    best_pred = trained_models[best_model_name]['predictions']
    
    print(f"\n🥇 최고 성능 모델: {best_model_name}")
    print(f" Test RMSE: {results_df.iloc[0]['RMSE']:.4f}")
    print(f" Test R²: {results_df.iloc[0]['R2']:.4f}")
    print(f" Test MAPE: {results_df.iloc[0]['MAPE']:.2f}%")
    
    # 7. 시각화
    print("7️⃣ 결과 시각화")
    plot_model_comparison(results_df, trained_models, y_test)
    plot_predictions_timeline(df, y_test, best_pred, X_test.index, best_model_name)
    
    # 8. 상세 분석 결과
    print("8️⃣ 상세 분석 결과")
    residuals = y_test - best_pred
    
    print(f"잔차 통계:")
    print(f" 평균: {residuals.mean():.4f}")
    print(f" 표준편차: {residuals.std():.4f}")
    print(f" 최대 오차: {abs(residuals).max():.4f}")
    
    actual_direction = np.sign(y_test.diff().dropna())
    pred_direction = np.sign(pd.Series(best_pred, index=y_test.index).diff().dropna())
    direction_accuracy = (actual_direction == pred_direction).mean()
    print(f" 방향성 예측 정확도: {direction_accuracy:.2%}")
    
    print("\n✅ 분석 완료!")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ 실행 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
