import os
import sys
import warnings
warnings.filterwarnings('ignore')

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import base64
from io import BytesIO
from matplotlib.font_manager import FontProperties

from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor, ExtraTreesRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

# [핵심] 상위 폴더(Graph)의 config.py 불러오기
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import MONGO_URI, DB_NAME, SYSTEM_CONFIG, OUTPUT_PATHS

# [설정] Config 파일 값 적용
N_JOBS_LIMIT = int(SYSTEM_CONFIG["N_JOBS_LIMIT"])
os.environ["OMP_NUM_THREADS"] = SYSTEM_CONFIG["OMP_NUM_THREADS"]

# 고급 모델 로드 시도
try:
    import xgboost as xgb
    import lightgbm as lgb
    ADVANCED_MODELS = True
except ImportError:
    ADVANCED_MODELS = False

try:
    from pymongo import MongoClient
    MONGO_AVAILABLE = True
except ImportError:
    MONGO_AVAILABLE = False

# 폰트 설정
malgun_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'malgun.ttf'))
fontprop = FontProperties(fname=malgun_path) if os.path.exists(malgun_path) else None

# 출력 경로 설정 (Config 참조)
OUTPUT_DIR = os.path.join(OUTPUT_PATHS["kim"], "gold")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def apply_korean_font(ax):
    if fontprop is not None:
        for label in (ax.get_xticklabels() + ax.get_yticklabels()):
            label.set_fontproperties(fontprop)
        ax.title.set_fontproperties(fontprop)
        ax.xaxis.label.set_fontproperties(fontprop)
        ax.yaxis.label.set_fontproperties(fontprop)
        if ax.get_legend():
            for text in ax.get_legend().get_texts():
                text.set_fontproperties(fontprop)

def save_chart_and_html(fig, filename, title=None):
    png_path = os.path.join(OUTPUT_DIR, f"{filename}.png")
    html_path = os.path.join(OUTPUT_DIR, f"{filename}.html")

    if fontprop is not None:
        for ax in fig.get_axes():
            apply_korean_font(ax)

    fig.savefig(png_path, dpi=100, bbox_inches='tight')
    buffer = BytesIO()
    fig.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.read()).decode()
    plt.close(fig)

    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"><title>{title or filename}</title>
    <style>body {{ font-family: 'Malgun Gothic', Arial, sans-serif; margin: 40px; }} img {{ display: block; margin: 20px auto; max-width: 100%; height: auto; }}</style>
    </head><body><h2>{title or filename}</h2><img src="data:image/png;base64,{image_base64}" alt="{filename}"></body></html>
    """
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_template)
    print(f"📊 차트 저장: {filename}.png")

class GoldAnalysisReporter:
    def __init__(self): self.content = []
    def add_text(self, text): print(text)
    def add_header(self, text, level=2): print(f"\n{'='*60}\n{text}\n{'='*60}")
    def add_chart(self, fig, filename):
        if fontprop: 
            for ax in fig.get_axes(): apply_korean_font(ax)
        fig.savefig(os.path.join(OUTPUT_DIR, f"{filename}.png"), dpi=100, bbox_inches='tight')
        save_chart_and_html(fig, filename, filename)
        plt.close(fig)

reporter = GoldAnalysisReporter()

def load_precious_metals_data():
    if not MONGO_AVAILABLE or not MONGO_URI: return create_test_data()
    
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    
    try:
        reporter.add_text("🔗 MongoDB 연결 성공")
        collections = db.list_collection_names()
        
        # 데이터 조회 (최근 5년)
        cutoff_date = pd.Timestamp.now() - pd.DateOffset(years=5)
        
        def get_df(col_name, val_field):
            if col_name not in collections: return pd.DataFrame()
            data = list(db[col_name].find({}, {"_id": 0, "date": 1, val_field: 1}).sort("date", 1))
            if not data: return pd.DataFrame()
            df = pd.DataFrame(data)
            df['date'] = pd.to_datetime(df['date'])
            return df[df['date'] >= cutoff_date].set_index('date')

        gold_df = get_df("GOLD", "price")
        if not gold_df.empty: gold_df = gold_df.rename(columns={"price": "GOLD"})
        
        silver_df = get_df("SILVER", "price")
        if not silver_df.empty: silver_df = silver_df.rename(columns={"price": "SILVER"})
        
        fx_dfs = []
        for fx in ["USD", "CNY", "EUR", "JPY"]:
            df = get_df(fx, "rate")
            if not df.empty: fx_dfs.append(df.rename(columns={"rate": f"{fx}_KRW"}))
            
        client.close()
        
        all_dfs = [gold_df, silver_df] + fx_dfs
        all_dfs = [df for df in all_dfs if not df.empty]
        
        if all_dfs:
            merged = pd.concat(all_dfs, axis=1, join='outer').sort_index().ffill()
            for col in merged.columns: merged[col] = pd.to_numeric(merged[col], errors='coerce')
            reporter.add_text(f"✅ 데이터 병합 완료: {merged.shape}")
            return merged
            
        return create_test_data()
        
    except Exception as e:
        reporter.add_text(f"❌ 데이터 로드 오류: {e}")
        client.close()
        return create_test_data()

def create_test_data():
    np.random.seed(42)
    dates = pd.date_range(start='2020-01-01', end='2024-09-01', freq='D')
    return pd.DataFrame({'GOLD': 1800 + np.cumsum(np.random.normal(0, 5, len(dates)))}, index=dates)

def create_features(df, target_col="GOLD"):
    if df.empty or target_col not in df.columns: return df
    feature_df = df.copy()
    feature_df[f"{target_col}_return"] = np.log(feature_df[target_col] / feature_df[target_col].shift(1))
    for w in [5, 20]:
        feature_df[f"{target_col}_ma_{w}"] = feature_df[target_col].rolling(w).mean()
    return feature_df.dropna()

def evaluate_model(y_true, y_pred, model_name="model"):
    mse = mean_squared_error(y_true, y_pred)
    return {"model": model_name, "RMSE": np.sqrt(mse), "R2": r2_score(y_true, y_pred)}

class GoldPredictionModels:
    def __init__(self):
        self.models = {}
        self.results = []
        self.feature_names = None
    
    def prepare_data(self, df, target_col='GOLD'):
        df = create_features(df, target_col)
        df['target'] = df[target_col].shift(-1)
        df = df.dropna()
        if len(df) < 50: raise ValueError("데이터 부족")
        
        feature_cols = [c for c in df.columns if c != 'target']
        self.feature_names = feature_cols
        X = df[feature_cols].values
        y = df['target'].values
        
        split = int(len(X) * 0.8)
        return X[:split], X[split:], y[:split], y[split:], df

    def train_models(self, X_train, y_train, X_test, y_test):
        reporter.add_text("🚀 모델 훈련 시작 (Light Mode)...")
        
        # Linear
        lr = LinearRegression()
        lr.fit(X_train, y_train)
        self.models["Linear"] = lr
        self.results.append(evaluate_model(y_test, lr.predict(X_test), "Linear"))
        
        # RF (n_jobs 제한)
        rf = RandomForestRegressor(n_estimators=100, max_depth=10, n_jobs=N_JOBS_LIMIT, random_state=42)
        rf.fit(X_train, y_train)
        self.models["RandomForest"] = rf
        self.results.append(evaluate_model(y_test, rf.predict(X_test), "RandomForest"))
        
        if ADVANCED_MODELS:
            try:
                xgb_model = xgb.XGBRegressor(n_estimators=100, max_depth=5, n_jobs=N_JOBS_LIMIT, random_state=42)
                xgb_model.fit(X_train, y_train)
                self.models["XGBoost"] = xgb_model
                self.results.append(evaluate_model(y_test, xgb_model.predict(X_test), "XGBoost"))
            except: pass
            
        reporter.add_text(f"🎯 {len(self.results)}개 모델 완료")

    def get_best_model(self):
        return sorted(self.results, key=lambda x: x["R2"], reverse=True)[0] if self.results else None

    def plot_feature_importance(self, model_name='RandomForest'):
        if model_name not in self.models: return
        model = self.models[model_name]
        if hasattr(model, 'feature_importances_'):
            imp = model.feature_importances_
            idx = np.argsort(imp)[::-1][:5]
            
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.barh([self.feature_names[i] for i in idx], imp[idx], color='steelblue')
            ax.set_title(f'{model_name} 중요 피처', fontproperties=fontprop)
            reporter.add_chart(fig, "feature_importance")

def plot_predictions(y_test, pred, model_name, index):
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(index, y_test, label='Actual', color='blue')
    ax.plot(index, pred, label='Predicted', color='red', linestyle='--')
    ax.set_title(f'금값 예측 ({model_name})', fontproperties=fontprop)
    ax.legend(prop=fontprop)
    reporter.add_chart(fig, "predictions_timeline")

def main():
    reporter.add_header("🚀 금가격 예측 (Light Ver.)", 1)
    df = load_precious_metals_data()
    if df.empty: return

    ml = GoldPredictionModels()
    try:
        X_train, X_test, y_train, y_test, f_df = ml.prepare_data(df)
        ml.train_models(X_train, y_train, X_test, y_test)
        
        best = ml.get_best_model()
        if best:
            reporter.add_text(f"🥇 Best: {best['model']} (R2={best['R2']:.3f})")
            pred = ml.models[best['model']].predict(X_test)
            plot_predictions(y_test, pred, best['model'], f_df.index[-len(y_test):])
            
            if "RandomForest" in ml.models:
                ml.plot_feature_importance("RandomForest")
    except Exception as e:
        reporter.add_text(f"❌ 오류: {e}")

if __name__ == "__main__":
    main()