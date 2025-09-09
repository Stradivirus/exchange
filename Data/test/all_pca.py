import pandas as pd
from sqlalchemy import create_engine
from sklearn.decomposition import PCA


# DB 접속 정보 하드코딩
def get_engine():
    PG_HOST = "64.110.115.12"
    PG_DB = "exchange"
    PG_USER = "exchange_admin"
    PG_PASSWORD = "exchange_password"
    return create_engine(f"postgresql+psycopg2://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:5432/{PG_DB}")


engine = get_engine()


from datetime import date



# ===== Commodities PCA (rolling 3년) =====
query_commod = """
SELECT date, gold, silver, copper, crude_oil, brent_oil
FROM commodities
WHERE date >= '2010-01-01'
ORDER BY date
"""
df_commod = pd.read_sql(query_commod, engine)
commod_cols = ['gold', 'silver', 'copper', 'crude_oil', 'brent_oil']
df_commod = df_commod.sort_values('date').reset_index(drop=True)

from datetime import timedelta, datetime

def rolling_pca(df, cols, window_days=365*3):
    result = []
    for idx, row in df.iterrows():
        cur_date = row['date']
        start_date = cur_date - timedelta(days=window_days)
        window_df = df[(df['date'] > start_date) & (df['date'] <= cur_date)].copy()
        # 결측치 처리: 선형보간, ffill, bfill
        window_df[cols] = window_df[cols].interpolate(method='linear', limit_direction='both')
        window_df[cols] = window_df[cols].ffill().bfill()
        if window_df[cols].isnull().any().any() or len(window_df) < 2:
            result.append(None)
            continue
        pca = PCA(n_components=1)
        pca_val = pca.fit_transform(window_df[cols])[-1,0]  # 해당 날짜의 값
        result.append(pca_val)
    return result

# 금속 PCA (rolling)
metals_cols = ['gold', 'silver', 'copper']
df_commod['metals_pca'] = rolling_pca(df_commod, metals_cols)
# 오일 PCA (rolling)
oil_cols = ['crude_oil', 'brent_oil']
df_commod['oil_pca'] = rolling_pca(df_commod, oil_cols)
# commodities 전체 PCA (rolling)
df_commod['commodities_pca'] = rolling_pca(df_commod, commod_cols)

print("\n[Commodities PCA 결과]")
print(df_commod[['date','metals_pca','oil_pca','commodities_pca']].tail(10))


agri_cols = ['corn', 'wheat', 'rice', 'coffee', 'sugar']

# ===== Grains PCA (rolling 3년) =====
query_grains = """
SELECT date, corn, wheat, rice, coffee, sugar
FROM grains
WHERE date >= '2010-01-01'
ORDER BY date
"""
df_grains = pd.read_sql(query_grains, engine)
grains_cols = ['corn', 'wheat', 'rice']
agri_cols = ['corn', 'wheat', 'rice', 'coffee', 'sugar']
softs_cols = ['coffee', 'sugar']
df_grains = df_grains.sort_values('date').reset_index(drop=True)

df_grains['grains_pca'] = rolling_pca(df_grains, grains_cols)
df_grains['agri_pca'] = rolling_pca(df_grains, agri_cols)
df_grains['softs_pca'] = rolling_pca(df_grains, softs_cols)

print("\n[Grains/Agri/Softs PCA 결과]")
print(df_grains[['date','grains_pca','agri_pca','softs_pca']].tail(10))




# stock 데이터 로딩 및 컬럼 정의
query_stock = """
SELECT date, sp500, dow_jones, nasdaq, kospi, kosdaq
FROM stock
WHERE date >= '2010-01-01'
ORDER BY date
"""
df_stock = pd.read_sql(query_stock, engine)
df_stock = df_stock.sort_values('date').reset_index(drop=True)
stock_cols = ['sp500', 'dow_jones', 'nasdaq', 'kospi', 'kosdaq']
us_cols = ['sp500', 'dow_jones', 'nasdaq']
kr_cols = ['kospi', 'kosdaq']

df_stock['stock_pca'] = rolling_pca(df_stock, stock_cols)
df_stock['us_stock_pca'] = rolling_pca(df_stock, us_cols)
df_stock['kr_stock_pca'] = rolling_pca(df_stock, kr_cols)

print("\n[Stock PCA 결과]")
print(df_stock[['date','stock_pca','us_stock_pca','kr_stock_pca']].tail(10))


# === 각 파트별로 pca 테이블에 upsert ===
from sqlalchemy import text as sa_text


# 1. Commodities PCA 저장
with engine.begin() as conn:
    for _, row in df_commod[['date','metals_pca','oil_pca','commodities_pca']].iterrows():
        sql = '''
        INSERT INTO pca (date, metals_pca, oil_pca, commodities_pca)
        VALUES (:date, :metals_pca, :oil_pca, :commodities_pca)
        ON CONFLICT (date) DO UPDATE SET
            metals_pca = EXCLUDED.metals_pca,
            oil_pca = EXCLUDED.oil_pca,
            commodities_pca = EXCLUDED.commodities_pca;
        '''
        conn.execute(sa_text(sql), {
            'date': row['date'],
            'metals_pca': row['metals_pca'],
            'oil_pca': row['oil_pca'],
            'commodities_pca': row['commodities_pca'],
        })
print(f"Commodities PCA {len(df_commod)}건 저장(upsert) 완료.")


# 2. Grains/Agri/Softs PCA 저장
with engine.begin() as conn:
    for _, row in df_grains[['date','grains_pca','agri_pca','softs_pca']].iterrows():
        sql = '''
        INSERT INTO pca (date, grains_pca, agri_pca, softs_pca)
        VALUES (:date, :grains_pca, :agri_pca, :softs_pca)
        ON CONFLICT (date) DO UPDATE SET
            grains_pca = EXCLUDED.grains_pca,
            agri_pca = EXCLUDED.agri_pca,
            softs_pca = EXCLUDED.softs_pca;
        '''
        conn.execute(sa_text(sql), {
            'date': row['date'],
            'grains_pca': row['grains_pca'],
            'agri_pca': row['agri_pca'],
            'softs_pca': row['softs_pca'],
        })
print(f"Grains/Agri/Softs PCA {len(df_grains)}건 저장(upsert) 완료.")


# 3. Stock PCA 저장
with engine.begin() as conn:
    for _, row in df_stock[['date','stock_pca','us_stock_pca','kr_stock_pca']].iterrows():
        sql = '''
        INSERT INTO pca (date, stock_pca, us_stock_pca, kr_stock_pca)
        VALUES (:date, :stock_pca, :us_stock_pca, :kr_stock_pca)
        ON CONFLICT (date) DO UPDATE SET
            stock_pca = EXCLUDED.stock_pca,
            us_stock_pca = EXCLUDED.us_stock_pca,
            kr_stock_pca = EXCLUDED.kr_stock_pca;
        '''
        conn.execute(sa_text(sql), {
            'date': row['date'],
            'stock_pca': row['stock_pca'],
            'us_stock_pca': row['us_stock_pca'],
            'kr_stock_pca': row['kr_stock_pca'],
        })
print(f"Stock PCA {len(df_stock)}건 저장(upsert) 완료.")
