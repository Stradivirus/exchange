import os
import warnings
warnings.filterwarnings('ignore')

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import base64
from io import BytesIO
from matplotlib.font_manager import FontProperties

# 머신러닝 라이브러리
from sklearn.model_selection import train_test_split, TimeSeriesSplit, GridSearchCV
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, ExtraTreesRegressor
from sklearn.linear_model import LinearRegression, Ridge, Lasso, ElasticNet
from sklearn.svm import SVR
from sklearn.neural_network import MLPRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score, median_absolute_error
from sklearn.feature_selection import SelectKBest, f_regression

# 고급 모델들 (선택적)
try:
    import xgboost as xgb
    import lightgbm as lgb
    ADVANCED_MODELS = True
except ImportError:
    print("⚠️ XGBoost 또는 LightGBM이 설치되지 않았습니다.")
    ADVANCED_MODELS = False

# 시계열 분석
try:
    from statsmodels.tsa.arima.model import ARIMA
    from statsmodels.tsa.statespace.sarimax import SARIMAX
    from statsmodels.tsa.holtwinters import ExponentialSmoothing
    from statsmodels.tsa.vector_ar.var_model import VAR
    from statsmodels.tsa.stattools import adfuller, kpss
    import scipy.stats as stats
    import statsmodels.api as sm
    STATS_MODELS = True
except ImportError:
    print("⚠️ Statsmodels가 설치되지 않았습니다.")
    STATS_MODELS = False

# MongoDB 연결 (선택적)
try:
    from pymongo import MongoClient
    MONGO_AVAILABLE = True
except ImportError:
    print("⚠️ MongoDB 연결 불가. 테스트 데이터를 사용합니다.")
    MONGO_AVAILABLE = False

# 딥러닝 (선택적)
try:
    import tensorflow as tf
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import Dense, LSTM, GRU, Dropout
    from tensorflow.keras.optimizers import Adam
    KERAS_AVAILABLE = True
except ImportError:
    print("⚠️ TensorFlow/Keras가 설치되지 않았습니다.")
    KERAS_AVAILABLE = False

# 한글 폰트 prop 설정 (이미 있음)
malgun_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'malgun.ttf'))
if os.path.exists(malgun_path):
    fontprop = FontProperties(fname=malgun_path)
else:
    fontprop = None

def apply_korean_font(ax):
    """모든 축에 한글 폰트 적용"""
    if fontprop is not None:
        for label in (ax.get_xticklabels() + ax.get_yticklabels()):
            label.set_fontproperties(fontprop)
        if ax.title:
            ax.title.set_fontproperties(fontprop)
        if ax.xaxis.label:
            ax.xaxis.label.set_fontproperties(fontprop)
        if ax.yaxis.label:
            ax.yaxis.label.set_fontproperties(fontprop)
        legend = ax.get_legend()
        if legend:
            for text in legend.get_texts():
                text.set_fontproperties(fontprop)

# 차트 및 HTML 저장 함수
def save_chart_and_html(fig, filename, title=None):
    """차트를 PNG로 저장하고, 같은 이미지를 포함한 HTML도 저장 (한글 폰트 적용)"""
    OUTPUT_DIR = "../outputs/kim/gold"
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    png_path = os.path.join(OUTPUT_DIR, f"{filename}.png")
    html_path = os.path.join(OUTPUT_DIR, f"{filename}.html")

    # 폰트 prop 적용
    if fontprop is not None:
        for ax in fig.get_axes():
            apply_korean_font(ax)

    fig.savefig(png_path, dpi=300, bbox_inches='tight')
    buffer = BytesIO()
    fig.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.read()).decode()
    plt.close(fig)

    # HTML에 malgun.ttf 폰트 적용
    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>{title or filename}</title>
        <style>
            @font-face {{
                font-family: 'Malgun Gothic';
                src: url('malgun.ttf');
            }}
            body {{ font-family: 'Malgun Gothic', Arial, sans-serif; margin: 40px; }}
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

# 출력 디렉토리 설정
OUTPUT_DIR = "../outputs/kim/gold"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 귀금속 관련 주요 이벤트 리스트
precious_metals_events = [
    {'date': '2008-09-15', 'label': 'Lehman Crisis', 'color': '#8B0000', 'type': 'line', 'y_pos_factor': 0.85,
     'impact': '리먼브라더스 파산으로 안전자산 선호'},
    {'date': '2010-05-02', 'label': 'Greek Crisis', 'color': '#A52A2A', 'type': 'line', 'y_pos_factor': 0.2,
     'impact': '유럽 재정위기로 금 수요 급증'},
    {'date': '2011-08-05', 'label': 'US Credit Downgrade', 'color': '#B22222', 'type': 'line', 'y_pos_factor': 0.9,
     'impact': '미국 신용등급 하락으로 달러약세'},
    {'date': '2013-04-12', 'label': 'Gold Flash Crash', 'color': '#FFD700', 'type': 'line', 'y_pos_factor': 0.3,
     'impact': '금값 대폭락 (-9.3% in 2 days)'},
    {'start': '2020-02-19', 'end': '2020-04-10', 'label': 'COVID-19 Panic', 'color': '#DC143C', 'type': 'span',
     'y_pos_factor': 0.4, 'impact': '팬데믹 초기 현금 확보 위한 금 매도'},
    {'start': '2020-04-11', 'end': '2020-08-31', 'label': 'Gold Bull Run', 'color': '#FFD700', 'type': 'span',
     'y_pos_factor': 0.95, 'impact': '초저금리와 양적완화로 금값 사상최고가'},
    {'start': '2022-02-24', 'end': '2022-06-17', 'label': 'Russia-Ukraine War', 'color': '#9932CC', 'type': 'span',
     'y_pos_factor': 0.8, 'impact': '지정학적 리스크로 금 급등'},
]

# HTML 보고서 관리 클래스
class GoldAnalysisReporter:
    def __init__(self):
        self.content = []
        self.charts = []
        self.model_results = []
    
    def add_text(self, text):
        """텍스트 추가"""
        self.content.append(f"<p>{text}</p>")
        print(text)
    
    def add_header(self, text, level=2):
        """헤더 추가"""
        self.content.append(f"<h{level}>{text}</h{level}>")
        print(f"\n{'='*60}")
        print(text)
        print(f"{'='*60}")
    
    def add_table(self, df, caption=""):
        """테이블 추가 (HTML)"""
        if caption:
            self.content.append(f"<h4>{caption}</h4>")
        self.content.append(df.to_html(classes="table table-striped", escape=False))
        print(f"\n{caption}")
        print(df.to_string())
    
    def add_chart(self, fig, filename):
        """차트를 PNG로 저장하고 HTML에 추가 (한글 폰트 적용)"""
        if fontprop is not None:
            for ax in fig.get_axes():
                apply_korean_font(ax)
        png_path = os.path.join(OUTPUT_DIR, f"{filename}.png")
        fig.savefig(png_path, dpi=300, bbox_inches='tight', facecolor='white')
        save_chart_and_html(fig, filename, title=filename.replace("_", " ").title())
        self.charts.append(png_path)
        plt.close(fig)
        self.add_text(f"📊 차트 저장: {png_path}")

# 전역 리포터 객체
reporter = GoldAnalysisReporter()

# MongoDB 데이터 로드 함수
def load_precious_metals_data():
    """MongoDB에서 금, 은, USD/CNY/EUR/JPY-KRW 데이터를 로드하고 병합"""
    if not MONGO_AVAILABLE:
        return create_test_data()
    
    MONGO_URI = "mongodb+srv://stradivirus:1q2w3e4r6218@cluster0.e7rvfpz.mongodb.net/exchange_all?retryWrites=true&w=majority&appName=Cluster0"
    DB_NAME = "exchange_all"
    
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    
    try:
        reporter.add_text("🔗 MongoDB 연결 성공")
        collections = db.list_collection_names()
        
        # 금 데이터
        gold_df = pd.DataFrame()
        if "GOLD" in collections:
            gold_cursor = db["GOLD"].find({}, {"_id": 0, "date": 1, "price": 1})
            temp_df = pd.DataFrame(list(gold_cursor))
            if not temp_df.empty:
                temp_df["date"] = pd.to_datetime(temp_df["date"])
                gold_df = temp_df.rename(columns={"price": "GOLD"}).set_index("date")
                reporter.add_text(f"✅ 금 데이터 {len(gold_df)}건 로드")
        
        # 은 데이터
        silver_df = pd.DataFrame()
        if "SILVER" in collections:
            silver_cursor = db["SILVER"].find({}, {"_id": 0, "date": 1, "price": 1})
            temp_df = pd.DataFrame(list(silver_cursor))
            if not temp_df.empty:
                temp_df["date"] = pd.to_datetime(temp_df["date"])
                silver_df = temp_df.rename(columns={"price": "SILVER"}).set_index("date")
                reporter.add_text(f"✅ 은 데이터 {len(silver_df)}건 로드")
        
        # 환율 데이터
        fx_data = {}
        for fx in ["USD", "CNY", "EUR", "JPY"]:
            if fx in collections:
                fx_cursor = db[fx].find({}, {"_id": 0, "date": 1, "rate": 1})
                temp_df = pd.DataFrame(list(fx_cursor))
                if not temp_df.empty:
                    temp_df["date"] = pd.to_datetime(temp_df["date"])
                    fx_data[f"{fx}_KRW"] = temp_df.rename(columns={"rate": f"{fx}_KRW"}).set_index("date")
                    reporter.add_text(f"✅ {fx}/KRW 데이터 {len(fx_data[f'{fx}_KRW'])}건 로드")
        
        # 데이터 병합
        all_dfs = [df for df in [gold_df, silver_df] + list(fx_data.values()) if not df.empty]
        if all_dfs:
            merged_df = pd.concat(all_dfs, axis=1, join='outer').sort_index()
            merged_df = merged_df.ffill()  # Forward fill
            
            for col in merged_df.columns:
                merged_df[col] = pd.to_numeric(merged_df[col], errors='coerce')
            
            reporter.add_text(f"✅ 데이터 병합 완료: {merged_df.shape}")
            client.close()
            return merged_df
        
        client.close()
        return create_test_data()
        
    except Exception as e:
        reporter.add_text(f"❌ 데이터 로드 오류: {e}")
        client.close()
        return create_test_data()

# 테스트 데이터 생성
def create_test_data():
    """현실적인 금가격과 환율 테스트 데이터 생성"""
    np.random.seed(42)
    
    dates = pd.date_range(start='2018-01-01', end='2024-09-01', freq='D')
    n_days = len(dates)
    
    # 금가격 생성 (USD/oz)
    gold_base = 1300
    gold_trend = 300 * np.cumsum(np.random.normal(0, 0.001, n_days))
    gold_volatility = np.random.normal(0, 30, n_days)
    
    # COVID-19 효과 (2020년)
    covid_start = (pd.to_datetime('2020-03-01') - dates[0]).days
    covid_peak = (pd.to_datetime('2020-08-01') - dates[0]).days
    covid_effect = np.zeros(n_days)
    covid_effect[covid_start:covid_peak] = 500 * np.exp(-(np.arange(covid_peak - covid_start) / 150))
    
    gold_price = gold_base + gold_trend + gold_volatility + covid_effect
    gold_price = np.clip(gold_price, 1000, 2500)
    
    # 은가격 (금가격과 연동)
    silver_ratio = 75 + 10 * np.sin(np.arange(n_days) * 2 * np.pi / 365) + np.random.normal(0, 5, n_days)
    silver_price = gold_price / silver_ratio
    
    # USD/KRW 환율
    usd_base = 1200
    usd_trend = 150 * np.cumsum(np.random.normal(0, 0.0005, n_days))
    usd_volatility = np.random.normal(0, 10, n_days)
    usd_krw = usd_base + usd_trend + usd_volatility
    usd_krw = np.clip(usd_krw, 1000, 1600)
    
    # 기타 환율 (USD/KRW 기준)
    cny_krw = usd_krw * 0.14 + np.random.normal(0, 5, n_days)  # 대략 180원
    eur_krw = usd_krw * 1.1 + np.random.normal(0, 15, n_days)  # 대략 1320원
    jpy_krw = usd_krw * 0.009 + np.random.normal(0, 0.5, n_days)  # 대략 10.8원
    
    test_df = pd.DataFrame({
        'GOLD': gold_price,
        'SILVER': silver_price,
        'USD_KRW': usd_krw,
        'CNY_KRW': cny_krw,
        'EUR_KRW': eur_krw,
        'JPY_KRW': jpy_krw
    }, index=dates)
    
    return test_df

# 피처 엔지니어링
def create_features(df, target_col="GOLD"):
    """금 가격 예측을 위한 피처 생성"""
    if df.empty or target_col not in df.columns:
        reporter.add_text("⚠️ 피처 생성 불가: 데이터 부족")
        return df
    
    feature_df = df.copy()
    
    # 1. 타겟 관련 피처
    feature_df[f"{target_col}_return"] = np.log(feature_df[target_col] / feature_df[target_col].shift(1))
    
    # 이동평균 & 변동성
    for w in [5, 10, 20, 50]:
        feature_df[f"{target_col}_ma_{w}"] = feature_df[target_col].rolling(w).mean()
        feature_df[f"{target_col}_vol_{w}"] = feature_df[f"{target_col}_return"].rolling(w).std()
    
    # RSI (14일)
    delta = feature_df[target_col].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    feature_df[f"{target_col}_RSI"] = 100 - (100 / (1 + rs))
    
    # Bollinger Bands
    bb_period = 20
    ma20 = feature_df[target_col].rolling(bb_period).mean()
    std20 = feature_df[target_col].rolling(bb_period).std()
    feature_df[f"{target_col}_bb_upper"] = ma20 + 2 * std20
    feature_df[f"{target_col}_bb_lower"] = ma20 - 2 * std20
    feature_df[f"{target_col}_bb_pos"] = (feature_df[target_col] - feature_df[f"{target_col}_bb_lower"]) / (
        feature_df[f"{target_col}_bb_upper"] - feature_df[f"{target_col}_bb_lower"]
    )
    
    # 2. 은 관련 피처
    if "SILVER" in feature_df.columns:
        feature_df["SILVER_return"] = np.log(feature_df["SILVER"] / feature_df["SILVER"].shift(1))
        feature_df["GOLD_SILVER_ratio"] = feature_df[target_col] / feature_df["SILVER"]
        feature_df["GOLD_SILVER_corr20"] = feature_df[f"{target_col}_return"].rolling(20).corr(
            feature_df["SILVER_return"]
        )
    
    # 3. 환율 관련 피처
    for fx in ["USD_KRW", "CNY_KRW", "EUR_KRW", "JPY_KRW"]:
        if fx in feature_df.columns:
            feature_df[f"{fx}_return"] = np.log(feature_df[fx] / feature_df[fx].shift(1))
            feature_df[f"{fx}_ma_20"] = feature_df[fx].rolling(20).mean()
            feature_df[f"{fx}_vol_20"] = feature_df[f"{fx}_return"].rolling(20).std()
            feature_df[f"{target_col}_{fx}_corr20"] = feature_df[f"{target_col}_return"].rolling(20).corr(
                feature_df[f"{fx}_return"]
            )
    
    # 4. 시간 피처
    feature_df["month"] = feature_df.index.month
    feature_df["quarter"] = feature_df.index.quarter
    feature_df["day_of_year"] = feature_df.index.dayofyear
    feature_df["day_of_week"] = feature_df.index.dayofweek
    feature_df["is_month_end"] = feature_df.index.is_month_end.astype(int)
    
    # 5. VIX Proxy
    feature_df["VIX_proxy"] = feature_df[f"{target_col}_vol_20"] * 100
    
    # NaN 제거
    feature_df = feature_df.dropna()
    return feature_df

# 모델 평가 함수
def evaluate_model(y_true, y_pred, model_name="model"):
    """모델 성능 평가"""
    mse = mean_squared_error(y_true, y_pred)
    rmse = np.sqrt(mse)
    mae = mean_absolute_error(y_true, y_pred)
    medae = median_absolute_error(y_true, y_pred)
    r2 = r2_score(y_true, y_pred)
    
    # MAPE
    mape = np.mean(np.abs((y_true - y_pred) / np.where(y_true == 0, np.nan, y_true))) * 100
    
    # 방향성 정확도
    y_true_diff = np.sign(np.diff(y_true))
    y_pred_diff = np.sign(np.diff(y_pred))
    direction_accuracy = np.mean(y_true_diff == y_pred_diff) * 100
    
    return {
        "model": model_name,
        "RMSE": rmse,
        "MAE": mae,
        "MedAE": medae,
        "R2": r2,
        "MAPE": mape,
        "Direction_Accuracy": direction_accuracy,
    }

# 머신러닝 모델 클래스
class GoldPredictionModels:
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.feature_names = None
        self.results = []
    
    def prepare_data(self, df, target_col='GOLD', test_size=0.2, forecast_days=1):
        """데이터 준비 및 피처 생성"""
        reporter.add_text("🔧 데이터 준비 시작...")
        
        # 피처 생성
        feature_df = create_features(df, target_col=target_col)
        
        # 타겟 변수 생성
        if forecast_days == 1:
            feature_df['target'] = feature_df[target_col].shift(-1)
        else:
            feature_df['target'] = feature_df[target_col].shift(-forecast_days)
        
        # 결측치 제거
        feature_df = feature_df.dropna()
        
        if len(feature_df) < 100:
            raise ValueError("⚠️ 충분한 데이터가 없습니다.")
        
        # 피처와 타겟 분리
        exclude_cols = ['GOLD', 'SILVER', 'USD_KRW', 'CNY_KRW', 'EUR_KRW', 'JPY_KRW', 'target']
        feature_cols = [col for col in feature_df.columns if col not in exclude_cols]
        X = feature_df[feature_cols].values
        y = feature_df['target'].values
        
        self.feature_names = feature_cols
        
        # 시계열 분할
        split_idx = int(len(X) * (1 - test_size))
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        
        reporter.add_text(f"✅ 데이터 준비 완료: 학습 {len(X_train)}개, 테스트 {len(X_test)}개")
        return X_train, X_test, y_train, y_test, feature_df
    
    def train_models(self, X_train, y_train, X_test, y_test):
        """다양한 머신러닝 모델 훈련"""
        self.results = []
        reporter.add_text("🚀 머신러닝 모델 훈련 시작...")
        
        # 1. 선형 모델들
        linear_models = [
            ("Linear_Regression", LinearRegression()),
            ("Ridge", Ridge(alpha=1.0)),
            ("Lasso", Lasso(alpha=0.1)),
            ("ElasticNet", ElasticNet(alpha=0.1, l1_ratio=0.5))
        ]
        
        for name, model in linear_models:
            try:
                model.fit(X_train, y_train)
                pred = model.predict(X_test)
                self.models[name] = model
                self.results.append(evaluate_model(y_test, pred, name))
                reporter.add_text(f"✅ {name} 훈련 완료")
            except Exception as e:
                reporter.add_text(f"❌ {name} 훈련 실패: {e}")
        
        # 2. 트리 기반 모델들
        tree_models = [
            ("Random_Forest", RandomForestRegressor(n_estimators=200, max_depth=10, random_state=42, n_jobs=-1)),
            ("Extra_Trees", ExtraTreesRegressor(n_estimators=200, max_depth=10, random_state=42, n_jobs=-1)),
            ("Gradient_Boosting", GradientBoostingRegressor(n_estimators=200, max_depth=6, learning_rate=0.05, random_state=42))
        ]
        
        # XGBoost, LightGBM (가능한 경우)
        if ADVANCED_MODELS:
            try:
                tree_models.append(("XGBoost", xgb.XGBRegressor(n_estimators=200, max_depth=6, learning_rate=0.05, random_state=42, n_jobs=-1)))
                tree_models.append(("LightGBM", lgb.LGBMRegressor(n_estimators=200, max_depth=6, learning_rate=0.05, random_state=42, verbose=-1)))
            except:
                pass
        
        for name, model in tree_models:
            try:
                model.fit(X_train, y_train)
                pred = model.predict(X_test)
                self.models[name] = model
                self.results.append(evaluate_model(y_test, pred, name))
                reporter.add_text(f"✅ {name} 훈련 완료")
            except Exception as e:
                reporter.add_text(f"❌ {name} 훈련 실패: {e}")
        
        # 3. SVM (스케일링 적용)
        try:
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            self.scalers['SVM'] = scaler
            
            svm = SVR(kernel='rbf', C=100, gamma='scale')
            svm.fit(X_train_scaled, y_train)
            pred = svm.predict(X_test_scaled)
            self.models['SVM'] = svm
            self.results.append(evaluate_model(y_test, pred, 'SVM'))
            reporter.add_text("✅ SVM 훈련 완료")
        except Exception as e:
            reporter.add_text(f"❌ SVM 훈련 실패: {e}")
        
        # 4. Neural Network
        try:
            scaler_nn = StandardScaler()
            X_train_nn = scaler_nn.fit_transform(X_train)
            X_test_nn = scaler_nn.transform(X_test)
            self.scalers['MLP'] = scaler_nn
            
            mlp = MLPRegressor(hidden_layer_sizes=(128, 64), max_iter=800, random_state=42)
            mlp.fit(X_train_nn, y_train)
            pred = mlp.predict(X_test_nn)
            self.models['MLP'] = mlp
            self.results.append(evaluate_model(y_test, pred, 'MLP'))
            reporter.add_text("✅ Neural Network 훈련 완료")
        except Exception as e:
            reporter.add_text(f"❌ Neural Network 훈련 실패: {e}")
        
        reporter.add_text(f"🎯 총 {len(self.results)}개 모델 훈련 완료")
    
    def get_best_models(self, top_k=3, metric="R2"):
        """상위 K개 모델 반환"""
        if not self.results:
            return []
        sorted_results = sorted(self.results, key=lambda x: x[metric], reverse=True)
        return sorted_results[:top_k]
    
    def plot_model_comparison(self):
        """모델 성능 비교 시각화"""
        if not self.results:
            reporter.add_text("⚠️ 시각화할 결과가 없습니다.")
            return
        
        results_df = pd.DataFrame(self.results)
        
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        
        metrics = [("R2", "R² Score"), ("RMSE", "RMSE"), ("MAE", "MAE"), ("Direction_Accuracy", "Direction Accuracy (%)")]
        colors = ['skyblue', 'lightcoral', 'lightgreen', 'gold']
        
        for ax, (col, title), color in zip(axes.flatten(), metrics, colors):
            bars = results_df.plot(x='model', y=col, kind='bar', ax=ax, color=color, legend=False)
            ax.set_title(title, fontweight='bold', fontsize=12)
            ax.set_xlabel('Models')
            ax.tick_params(axis='x', rotation=45)
            
            # 값 표시
            for i, bar in enumerate(ax.patches):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{height:.3f}' if col != 'Direction_Accuracy' else f'{height:.1f}%',
                       ha='center', va='bottom', fontsize=9)
        
        plt.tight_layout()
        reporter.add_chart(fig, "model_comparison")
        
        # 결과 테이블 추가
        reporter.add_table(results_df.round(4), "모델 성능 비교 결과")

    def plot_feature_importance(self, model_name='Random_Forest', top_k=5):
        """피처 중요도 시각화 (상위 5개, 한글화)"""
        if model_name not in self.models:
            reporter.add_text(f"⚠️ {model_name} 모델이 없습니다.")
            return
        
        model = self.models[model_name]
        if hasattr(model, 'feature_importances_'):
            importance = model.feature_importances_
            fi_df = pd.DataFrame({'feature': self.feature_names, 'importance': importance})
            fi_df = fi_df.sort_values('importance', ascending=False).head(top_k)
            
            fig, ax = plt.subplots(figsize=(12, 8))
            bars = ax.barh(fi_df['feature'], fi_df['importance'], color='steelblue')
            ax.set_xlabel('피처 중요도', fontweight='bold', fontproperties=fontprop)
            ax.set_title(f'랜덤포레스트 - 상위 5개 중요 피처', fontweight='bold', fontsize=14, fontproperties=fontprop)
            ax.invert_yaxis()
            for bar in bars:
                ax.text(bar.get_width(), bar.get_y() + bar.get_height()/2, f"{bar.get_width():.3f}",
                        va='center', ha='left', fontsize=10, fontproperties=fontprop)
            for label in (ax.get_xticklabels() + ax.get_yticklabels()):
                label.set_fontproperties(fontprop)
            reporter.add_chart(fig, "feature_importance")
        else:
            reporter.add_text("⚠️ 피처 중요도 지원 안함")

# 시각화 함수들 한글화 예시
def plot_data_overview(df):
    """데이터 개요 시각화"""
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    # 금가격 시계열
    if 'GOLD' in df.columns:
        axes[0, 0].plot(df.index, df['GOLD'], color='#FFD700', linewidth=2, label='금 가격')
        axes[0, 0].set_title('금 가격 추이', fontweight='bold', fontproperties=fontprop)
        axes[0, 0].set_ylabel('가격 (USD/oz)', fontproperties=fontprop)
        axes[0, 0].grid(True, alpha=0.3)
        axes[0, 0].legend(prop=fontprop)
    # 환율 시계열
    fx_cols = [col for col in ['USD_KRW', 'EUR_KRW', 'CNY_KRW', 'JPY_KRW'] if col in df.columns]
    if fx_cols:
        colors = ['red', 'blue', 'green', 'purple']
        for i, col in enumerate(fx_cols[:4]):
            axes[0, 1].plot(df.index, df[col], color=colors[i], linewidth=1.5, label=col.replace('_', '/'))
        axes[0, 1].set_title('환율 추이', fontweight='bold', fontproperties=fontprop)
        axes[0, 1].set_ylabel('환율 (KRW)', fontproperties=fontprop)
        axes[0, 1].grid(True, alpha=0.3)
        axes[0, 1].legend(prop=fontprop)
    # 상관관계 히트맵
    corr_matrix = df.corr()
    im = axes[1, 0].imshow(corr_matrix, cmap='RdYlBu_r', aspect='auto')
    axes[1, 0].set_xticks(range(len(corr_matrix.columns)))
    axes[1, 0].set_yticks(range(len(corr_matrix.columns)))
    axes[1, 0].set_xticklabels(corr_matrix.columns, rotation=45, ha='right', fontproperties=fontprop)
    axes[1, 0].set_yticklabels(corr_matrix.columns, fontproperties=fontprop)
    axes[1, 0].set_title('상관관계 행렬', fontweight='bold', fontproperties=fontprop)
    # 금가격 분포
    if 'GOLD' in df.columns:
        axes[1, 1].hist(df['GOLD'], bins=50, alpha=0.7, color='gold', edgecolor='black')
        axes[1, 1].set_title('금 가격 분포', fontweight='bold', fontproperties=fontprop)
        axes[1, 1].set_xlabel('가격 (USD/oz)', fontproperties=fontprop)
        axes[1, 1].set_ylabel('빈도', fontproperties=fontprop)
        axes[1, 1].grid(True, alpha=0.3)
    plt.tight_layout()
    reporter.add_chart(fig, "data_overview")

def plot_predictions_timeline(df, y_test, best_pred, test_index, model_name):
    """시계열 예측 결과 시각화"""
    fig, ax = plt.subplots(figsize=(16, 8))

    # 전체 데이터 (회색)
    ax.plot(df.index, df['GOLD'], color='lightgray', alpha=0.5, label='과거 데이터')

    # 실제 테스트 데이터 (파란색)
    # test_index가 정수라면 df.index에서 해당 구간의 날짜로 변환
    if not isinstance(test_index, pd.DatetimeIndex):
        # test_index가 정수 인덱스라면
        test_dates = df.index[-len(test_index):]
    else:
        test_dates = test_index

    ax.plot(test_dates, y_test, color='blue', linewidth=2, label='실제 테스트 데이터')

    # 예측 데이터 (빨간색)
    ax.plot(test_dates, best_pred, color='red', linewidth=2, label=f'{model_name} 예측')

    ax.set_xlabel('날짜', fontproperties=fontprop)
    ax.set_ylabel('금 가격 (USD/oz)', fontproperties=fontprop)
    ax.set_title(f'금 가격 예측 결과 - {model_name} 모델', fontweight='bold', fontsize=14, fontproperties=fontprop)
    ax.legend(prop=fontprop)
    ax.grid(True, alpha=0.3)

    # 날짜 축 포맷
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    plt.setp(ax.get_xticklabels(), rotation=45, ha='right', fontproperties=fontprop)

    plt.tight_layout()
    reporter.add_chart(fig, "predictions_timeline")

def plot_residual_analysis(y_true, y_pred, model_name):
    """잔차 분석 시각화 (한글화)"""
    residuals = y_true - y_pred

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # 1. 잔차 vs 예측값
    axes[0, 0].scatter(y_pred, residuals, alpha=0.6, color='blue')
    axes[0, 0].axhline(y=0, color="red", linestyle="--")
    axes[0, 0].set_xlabel('예측값', fontproperties=fontprop)
    axes[0, 0].set_ylabel('잔차', fontproperties=fontprop)
    axes[0, 0].set_title("잔차 vs 예측값", fontweight='bold', fontproperties=fontprop)
    axes[0, 0].grid(True, alpha=0.3)

    # 2. 잔차 히스토그램
    axes[0, 1].hist(residuals, bins=20, alpha=0.7, color="skyblue", edgecolor="black")
    axes[0, 1].set_xlabel('잔차', fontproperties=fontprop)
    axes[0, 1].set_ylabel('빈도', fontproperties=fontprop)
    axes[0, 1].set_title("잔차 분포", fontweight='bold', fontproperties=fontprop)
    axes[0, 1].grid(True, alpha=0.3)

    # 3. Q-Q plot
    from scipy import stats
    stats.probplot(residuals, dist="norm", plot=axes[1, 0])
    axes[1, 0].set_title("Q-Q 플롯", fontweight='bold', fontproperties=fontprop)
    axes[1, 0].set_xlabel('이론적 분위수', fontproperties=fontprop)
    axes[1, 0].set_ylabel('관측값', fontproperties=fontprop)
    axes[1, 0].grid(True, alpha=0.3)

    # 4. 시간에 따른 잔차
    axes[1, 1].plot(residuals, alpha=0.7, color='green')
    axes[1, 1].axhline(y=0, color="red", linestyle="--")
    axes[1, 1].set_xlabel('시간 인덱스', fontproperties=fontprop)
    axes[1, 1].set_ylabel('잔차', fontproperties=fontprop)
    axes[1, 1].set_title("시간에 따른 잔차", fontweight='bold', fontproperties=fontprop)
    axes[1, 1].grid(True, alpha=0.3)

    plt.suptitle(f"{model_name} - 잔차 분석", fontsize=14, fontweight="bold", fontproperties=fontprop)
    plt.tight_layout()
    reporter.add_chart(fig, f"residual_analysis_{model_name}")

# 모델 성능 테이블 저장 함수
def save_model_performance_table(df, filename="model_performance_table", title="모델별 성능 비교"):
    """모델별 성능 DataFrame을 표 이미지로 저장"""
    OUTPUT_DIR = "../outputs/kim/gold"
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    png_path = os.path.join(OUTPUT_DIR, f"{filename}.png")
    html_path = os.path.join(OUTPUT_DIR, f"{filename}.html")

    fig, ax = plt.subplots(figsize=(12, 0.6 + 0.4 * len(df)))
    ax.axis('off')
    table = ax.table(
        cellText=df.values,
        colLabels=df.columns,
        cellLoc='center',
        loc='center'
    )
    table.auto_set_font_size(False)
    table.set_fontsize(12)
    table.scale(1.2, 1.2)
    if title:
        plt.title(title, fontproperties=fontprop, fontsize=16, pad=20)
    plt.tight_layout()
    fig.savefig(png_path, dpi=300, bbox_inches='tight')
    plt.close(fig)

    # HTML 저장도 같이
    df.to_html(html_path, index=False)
    print(f"📊 표 저장: {png_path}")
    print(f"📝 HTML 저장: {html_path}")

# 사용 예시 (main 함수 등에서)
# results_df = pd.DataFrame(self.results)  # 이미 모델별 성능 결과 DataFrame이 있음
# save_model_performance_table(results_df, filename="model_performance_table", title="모델별 성능 비교")

# 메인 실행 함수
def main():
    """메인 실행 함수"""
    reporter.add_header("🚀 금가격 예측 최적모델링 시스템", 1)
    
    # 1. 데이터 로드
    reporter.add_header("1️⃣ 데이터 로딩")
    df = load_precious_metals_data()
    
    if df.empty:
        reporter.add_text("❌ 데이터 로드 실패")
        return
    
    reporter.add_text(f"📊 데이터 로드 완료: {df.shape}")
    reporter.add_text(f"📅 분석 기간: {df.index.min().strftime('%Y-%m-%d')} ~ {df.index.max().strftime('%Y-%m-%d')}")
    
    # 기본 통계
    if 'GOLD' in df.columns:
        gold_mean = df['GOLD'].mean()
        gold_std = df['GOLD'].std()
        gold_min = df['GOLD'].min()
        gold_max = df['GOLD'].max()
        
        reporter.add_text(f"📈 금가격 통계:")
        reporter.add_text(f" • 평균: ${gold_mean:.2f}")
        reporter.add_text(f" • 표준편차: ${gold_std:.2f}")
        reporter.add_text(f" • 최저가: ${gold_min:.2f}")
        reporter.add_text(f" • 최고가: ${gold_max:.2f}")
    
    # 데이터 개요 시각화
    plot_data_overview(df)
    
    # 2. 머신러닝 모델 훈련
    reporter.add_header("2️⃣ 머신러닝 모델 훈련")
    ml_models = GoldPredictionModels()
    
    try:
        X_train, X_test, y_train, y_test, feature_df = ml_models.prepare_data(df)
        ml_models.train_models(X_train, y_train, X_test, y_test)
        
        # 모델 비교 시각화
        ml_models.plot_model_comparison()
        
        # 상위 모델 선택
        best_models = ml_models.get_best_models(top_k=3)
        if best_models:
            reporter.add_text(f"\n🏆 상위 3개 모델:")
            for i, model in enumerate(best_models, 1):
                reporter.add_text(f"{i}. {model['model']}: R²={model['R2']:.4f}, RMSE={model['RMSE']:.2f}")
            
            # 최고 모델로 예측 시각화
            best_model_name = best_models[0]['model']
            if best_model_name in ml_models.models:
                try:
                    if best_model_name in ml_models.scalers:
                        X_test_scaled = ml_models.scalers[best_model_name].transform(X_test)
                        best_pred = ml_models.models[best_model_name].predict(X_test_scaled)
                    else:
                        best_pred = ml_models.models[best_model_name].predict(X_test)
                    
                    plot_predictions_timeline(df, y_test, best_pred, X_test.index if hasattr(X_test, 'index') else range(len(y_test)), best_model_name)
                    plot_residual_analysis(y_test, best_pred, best_model_name)
                    
                except Exception as e:
                    reporter.add_text(f"❌ 예측 시각화 실패: {e}")
            
            # 피처 중요도 (Random Forest가 있는 경우)
            if "Random_Forest" in ml_models.models:
                ml_models.plot_feature_importance("Random_Forest")
        
    except Exception as e:
        reporter.add_text(f"❌ 머신러닝 모델 훈련 실패: {e}")
        return
    
    # 3. 분석 결과 요약
    reporter.add_header("3️⃣ 분석 결과 요약")
    if best_models:
        best_model = best_models[0]
        reporter.add_text(f"🥇 최고 성능 모델: {best_model['model']}")
        reporter.add_text(f"• R² Score: {best_model['R2']:.4f}")
        reporter.add_text(f"• RMSE: {best_model['RMSE']:.2f}")
        reporter.add_text(f"• MAE: {best_model['MAE']:.2f}")
        reporter.add_text(f"• 방향 예측 정확도: {best_model['Direction_Accuracy']:.1f}%")
    
    reporter.add_text(f"\n✅ 분석 완료!")
    reporter.add_text(f"📊 생성된 차트: {len(reporter.charts)}개")
    
    return {
        'best_models': best_models,
        'charts': reporter.charts,
        'ml_models': ml_models
    }

# 실행부
if __name__ == "__main__":
    try:
        result = main()
        if result:
            print(f"\n🎯 최종 결과:")
            if result['best_models']:
                print(f" 최고 모델: {result['best_models'][0]['model']}")
            print(f" 차트 파일: {len(result['charts'])}개")
    except Exception as e:
        print(f"\n❌ 실행 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
