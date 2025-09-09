
import pandas as pd
from sqlalchemy import create_engine
from sklearn.decomposition import PCA

# DB 접속 정보 하드코딩
PG_HOST = "64.110.115.12"
PG_DB = "exchange"
PG_USER = "exchange_admin"
PG_PASSWORD = "exchange_password"
engine = create_engine(f"postgresql+psycopg2://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:5432/{PG_DB}")



# 1년치 데이터 로드 (commodities 테이블: 금속/오일)
query_commod = """
SELECT date, gold, silver, copper, crude_oil, brent_oil
FROM commodities
WHERE date >= (SELECT MAX(date) FROM commodities) - INTERVAL '365 days'
ORDER BY date
"""
df_commod = pd.read_sql(query_commod, engine)

# 1년치 데이터 로드 (grains 테이블: 곡물/커피/설탕)
query_grains = """
SELECT date, corn, wheat, rice, coffee, sugar
FROM grains
WHERE date >= (SELECT MAX(date) FROM grains) - INTERVAL '365 days'
ORDER BY date
"""
df_grains = pd.read_sql(query_grains, engine)

# date 기준 merge
df = pd.merge(df_commod, df_grains, on='date', how='inner')



# 결측치 보간 및 정렬
all_cols = ['gold', 'silver', 'copper', 'crude_oil', 'brent_oil', 'corn', 'wheat', 'rice', 'coffee', 'sugar']
df = df.sort_values('date').reset_index(drop=True)
df[all_cols] = df[all_cols].interpolate(method='linear')
# 맨 뒤 결측치는 바로 이전값으로 채움
df[all_cols] = df[all_cols].fillna(method='ffill')



# 1. 금속만 PCA (주성분 1개)
metals_cols = ['gold', 'silver', 'copper']
pca_metals = PCA(n_components=1)
metals_pca = pca_metals.fit_transform(df[metals_cols])
df['metals_pca'] = metals_pca[:,0]

# 2. 오일만 PCA (주성분 1개)
oil_cols = ['crude_oil', 'brent_oil']
pca_oil = PCA(n_components=1)
oil_pca = pca_oil.fit_transform(df[oil_cols])
df['oil_pca'] = oil_pca[:,0]

# 3. commodities 전체 PCA (주성분 1개)
commodities_cols = ['gold', 'silver', 'copper', 'crude_oil', 'brent_oil', 'corn', 'wheat', 'rice', 'coffee', 'sugar']
pca_commodities = PCA(n_components=1)
commodities_pca = pca_commodities.fit_transform(df[commodities_cols])
df['commodities_pca'] = commodities_pca[:,0]

# 4. grains_pca1: 옥수수, 밀, 쌀만
grains_cols = ['corn', 'wheat', 'rice']
pca_grains = PCA(n_components=1)
grains_pca = pca_grains.fit_transform(df[grains_cols])
df['grains_pca1'] = grains_pca[:,0]

# 5. agri_pca1: 옥수수, 밀, 쌀, 커피, 설탕 전체
agri_cols = ['corn', 'wheat', 'rice', 'coffee', 'sugar']
pca_agri = PCA(n_components=1)
agri_pca = pca_agri.fit_transform(df[agri_cols])
df['agri_pca1'] = agri_pca[:,0]

# 6. softs_pca1: 커피, 설탕만
softs_cols = ['coffee', 'sugar']
pca_softs = PCA(n_components=1)
softs_pca = pca_softs.fit_transform(df[softs_cols])
df['softs_pca1'] = softs_pca[:,0]


# 결과 확인
print(df[['date','metals_pca','oil_pca','commodities_pca','grains_pca1','agri_pca1','softs_pca1']].tail())

# 필요시 csv로 저장
# df.to_csv('commodities_pca_result.csv', index=False)
