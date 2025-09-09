import pandas as pd
from sqlalchemy import create_engine
from sklearn.decomposition import PCA

# DB 접속 정보 하드코딩
PG_HOST = "64.110.115.12"
PG_DB = "exchange"
PG_USER = "exchange_admin"
PG_PASSWORD = "exchange_password"
engine = create_engine(f"postgresql+psycopg2://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:5432/{PG_DB}")

# 1년치 데이터 로드 (stock 테이블)
query = """
SELECT date, sp500, dow_jones, nasdaq, kospi, kosdaq
FROM stock
WHERE date >= (SELECT MAX(date) FROM stock) - INTERVAL '365 days'
ORDER BY date
"""
df = pd.read_sql(query, engine)

# 결측치 보간 및 정렬
all_cols = ['sp500', 'dow_jones', 'nasdaq', 'kospi', 'kosdaq']
df = df.sort_values('date').reset_index(drop=True)
df[all_cols] = df[all_cols].interpolate(method='linear')
df[all_cols] = df[all_cols].fillna(method='ffill')

# 1. 전체 주가지수 PCA (주성분 1개)
pca_all = PCA(n_components=1)
df['stock_pca'] = pca_all.fit_transform(df[all_cols])[:,0]

# 2. 미국 주가지수 PCA (sp500, dow_jones, nasdaq)
us_cols = ['sp500', 'dow_jones', 'nasdaq']
pca_us = PCA(n_components=1)
df['us_stock_pca'] = pca_us.fit_transform(df[us_cols])[:,0]

# 3. 한국 주가지수 PCA (kospi, kosdaq)
kr_cols = ['kospi', 'kosdaq']
pca_kr = PCA(n_components=1)
df['kr_stock_pca'] = pca_kr.fit_transform(df[kr_cols])[:,0]

# 결과 확인
print(df[['date','stock_pca','us_stock_pca','kr_stock_pca']].tail())

# 필요시 csv로 저장
# df.to_csv('stock_pca_result.csv', index=False)
