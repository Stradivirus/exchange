import os
import sys
import warnings
warnings.filterwarnings('ignore')
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import base64
from io import BytesIO
from matplotlib.font_manager import FontProperties
import gc 

from sklearn.model_selection import TimeSeriesSplit, GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor

# [핵심] 상위 폴더(Graph)의 config.py 불러오기
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import MONGO_URI, DB_NAME, SYSTEM_CONFIG, OUTPUT_PATHS

# [설정] Config 적용
N_JOBS_LIMIT = int(SYSTEM_CONFIG["N_JOBS_LIMIT"])
os.environ["OMP_NUM_THREADS"] = SYSTEM_CONFIG["OMP_NUM_THREADS"]

try:
    import xgboost as xgb
    ADVANCED_MODELS = True
except: ADVANCED_MODELS = False

try:
    from pymongo import MongoClient
    MONGO_AVAILABLE = True
except: MONGO_AVAILABLE = False

malgun_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'malgun.ttf'))
fontprop = FontProperties(fname=malgun_path) if os.path.exists(malgun_path) else None

# 출력 디렉토리 설정
OUTPUT_DIR = os.path.join(OUTPUT_PATHS["kim"], "news")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def save_chart(fig, filename):
    png_path = os.path.join(OUTPUT_DIR, f"{filename}.png")
    html_path = os.path.join(OUTPUT_DIR, f"{filename}.html")
    
    if fontprop:
        for ax in fig.get_axes():
            ax.set_title(ax.get_title(), fontproperties=fontprop)
            
    fig.savefig(png_path, dpi=100, bbox_inches='tight')
    buffer = BytesIO()
    fig.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
    img_b64 = base64.b64encode(buffer.read()).decode()
    plt.close(fig)
    
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(f"<html><body><img src='data:image/png;base64,{img_b64}'></body></html>")
    print(f"📊 차트 저장: {filename}.html")

def load_data():
    if not MONGO_AVAILABLE or not MONGO_URI: return None
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    try:
        print("🔗 [News] MongoDB 연결")
        start = pd.Timestamp('2016-01-01')
        
        # 뉴스심리지수
        cur = db["news_sentiment"].find({'item_name': '뉴스심리지수', 'date': {'$gte': start}}, {"_id": 0, "date": 1, "value": 1})
        sent = pd.DataFrame(list(cur))
        if sent.empty: return None
        
        # [수정] 인덱스 설정 로직 단순화 (에러 원인 제거)
        sent['date'] = pd.to_datetime(sent['date'])
        sent = sent.rename(columns={"value": "SENTIMENT"}).set_index("date")
        sent = sent[['SENTIMENT']] # 필요한 컬럼만 유지

        # 환율
        usd = pd.DataFrame()
        # 컬렉션 이름 후보군 (대소문자 포함)
        possible_cols = ["USD", "USD_KRW", "usd"]
        
        for col in possible_cols:
            if col in db.list_collection_names():
                cur = db[col].find({'date': {'$gte': start}}, {"_id": 0, "date": 1, "rate": 1, "value": 1})
                usd = pd.DataFrame(list(cur))
                if not usd.empty:
                    rate_col = 'value' if 'value' in usd.columns else 'rate'
                    usd['date'] = pd.to_datetime(usd['date'])
                    usd = usd.rename(columns={rate_col: "USD_KRW"}).set_index("date")[["USD_KRW"]]
                    break
        
        client.close()
        
        if sent.empty or usd.empty:
            print("❌ 뉴스 또는 환율 데이터가 비어있습니다.")
            return None
            
        # 교집합 데이터만 사용
        return pd.concat([sent, usd], axis=1, join='inner').sort_index().dropna()
        
    except Exception as e:
        print(f"❌ 데이터 로드 실패: {e}")
        return None
    
def create_features(df):
    print("🔧 피처 엔지니어링...")
    f_df = df.copy()
    for col in df.columns:
        for w in [5, 20]:
            f_df[f'{col}_ma{w}'] = f_df[col].rolling(w).mean()
    return f_df.dropna()

def train_models(X_train, y_train, X_test, y_test):
    print("🚀 모델 학습 시작...")
    models = {
        'Ridge': (Ridge(), {'alpha': [1.0, 10.0]}),
        'RandomForest': (RandomForestRegressor(n_jobs=N_JOBS_LIMIT, random_state=42), {'n_estimators': [50, 100]}),
        'GradientBoosting': (GradientBoostingRegressor(random_state=42), {'n_estimators': [50]})
    }
    if ADVANCED_MODELS:
        models['XGBoost'] = (xgb.XGBRegressor(n_jobs=N_JOBS_LIMIT, random_state=42), {'n_estimators': [50]})

    results = []
    trained = {}
    tscv = TimeSeriesSplit(n_splits=2)

    for name, (model, params) in models.items():
        print(f" ⏳ {name}...")
        try:
            gs = GridSearchCV(model, params, cv=tscv, n_jobs=N_JOBS_LIMIT)
            gs.fit(X_train, y_train)
            best = gs.best_estimator_
            pred = best.predict(X_test)
            results.append({'Model': name, 'R2': r2_score(y_test, pred)})
            trained[name] = {'model': best, 'pred': pred}
        except: pass
        
    return pd.DataFrame(results).sort_values('R2', ascending=False), trained

def plot_res(y_test, pred, title):
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(y_test.index, y_test, label='Actual')
    ax.plot(y_test.index, pred, label='Predicted', linestyle='--')
    ax.set_title(title, fontproperties=fontprop)
    ax.legend()
    save_chart(fig, "predictions_timeline")

def main():
    print("🚀 뉴스심리지수 분석 (Light Mode)")
    df = load_data()
    if df is None: 
        print("❌ 데이터 없음")
        return

    # 시각화
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(df.index, df['SENTIMENT'], label='Sentiment')
    save_chart(fig, "data_overview")

    df = create_features(df)
    X = df.drop(columns=['USD_KRW'])
    y = df['USD_KRW']
    
    scaler = StandardScaler()
    X_scaled = pd.DataFrame(scaler.fit_transform(X), index=X.index, columns=X.columns)
    
    split = int(len(X) * 0.8)
    X_train, X_test = X_scaled.iloc[:split], X_scaled.iloc[split:]
    y_train, y_test = y.iloc[:split], y.iloc[split:]
    
    res_df, trained = train_models(X_train, y_train, X_test, y_test)
    
    if not res_df.empty:
        best_name = res_df.iloc[0]['Model']
        print(f"🏆 Best Model: {best_name} (R2={res_df.iloc[0]['R2']:.3f})")
        plot_res(y_test, trained[best_name]['pred'], f"{best_name} 예측")
        
    print("✅ [News] 분석 완료")
    gc.collect()

if __name__ == "__main__":
    main()