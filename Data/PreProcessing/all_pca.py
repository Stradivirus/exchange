# PreProcessing/all_pca.py
"""
PCA 전체 계산 (2010년~현재)
PostgreSQL의 commodities, grains, stock 테이블에서 데이터를 읽어
PCA를 계산하여 pca 테이블에 저장
"""
import os
import pandas as pd
from sqlalchemy import create_engine, text
from sklearn.decomposition import PCA
from datetime import timedelta, datetime

# 환경변수 지원 (GitHub Actions 호환)
PG_HOST = os.getenv("PG_HOST")
PG_DB = os.getenv("PG_DB")
PG_USER = os.getenv("PG_USER")
PG_PASSWORD = os.getenv("PG_PASSWORD")


def get_engine():
    """PostgreSQL 연결 엔진 생성"""
    return create_engine(
        f"postgresql+psycopg2://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:5432/{PG_DB}"
    )


def rolling_pca(df, cols, window_days=365*3):
    """
    Rolling PCA 계산
    
    Args:
        df: DataFrame (date 컬럼 필수)
        cols: PCA 계산할 컬럼 리스트
        window_days: 윈도우 크기 (일수)
    
    Returns:
        PCA 값 리스트
    """
    result = []
    for idx, row in df.iterrows():
        cur_date = row['date']
        start_date = cur_date - timedelta(days=window_days)
        
        # 윈도우 데이터 추출
        window_df = df[(df['date'] > start_date) & (df['date'] <= cur_date)].copy()
        
        # 결측치 처리: 선형보간 → ffill → bfill
        window_df[cols] = window_df[cols].interpolate(method='linear', limit_direction='both')
        window_df[cols] = window_df[cols].ffill().bfill()
        
        # 유효성 검사
        if window_df[cols].isnull().any().any() or len(window_df) < 2:
            result.append(None)
            continue
        
        # PCA 계산
        pca = PCA(n_components=1)
        pca_val = pca.fit_transform(window_df[cols])[-1, 0]
        result.append(pca_val)
    
    return result


def main():
    """메인 실행"""
    print(f"=== PCA 전체 계산 시작 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ===")
    
    engine = get_engine()
    
    # ===== 1. Commodities PCA =====
    print("\n--- Commodities 데이터 로딩 중 ---")
    query_commod = """
    SELECT date, gold, silver, copper, crude_oil, brent_oil
    FROM commodities
    WHERE date >= '2010-01-01'
    ORDER BY date
    """
    df_commod = pd.read_sql(query_commod, engine)
    df_commod = df_commod.sort_values('date').reset_index(drop=True)
    
    print("Commodities PCA 계산 중...")
    metals_cols = ['gold', 'silver', 'copper']
    oil_cols = ['crude_oil', 'brent_oil']
    commod_cols = ['gold', 'silver', 'copper', 'crude_oil', 'brent_oil']
    
    df_commod['metals_pca'] = rolling_pca(df_commod, metals_cols)
    df_commod['oil_pca'] = rolling_pca(df_commod, oil_cols)
    df_commod['commodities_pca'] = rolling_pca(df_commod, commod_cols)
    
    print(f"Commodities PCA: {len(df_commod)}건 계산 완료")
    print(df_commod[['date', 'metals_pca', 'oil_pca', 'commodities_pca']].tail(5))
    
    # ===== 2. Grains PCA =====
    print("\n--- Grains 데이터 로딩 중 ---")
    query_grains = """
    SELECT date, corn, wheat, rice, coffee, sugar
    FROM grains
    WHERE date >= '2010-01-01'
    ORDER BY date
    """
    df_grains = pd.read_sql(query_grains, engine)
    df_grains = df_grains.sort_values('date').reset_index(drop=True)
    
    print("Grains PCA 계산 중...")
    grains_cols = ['corn', 'wheat', 'rice']
    agri_cols = ['corn', 'wheat', 'rice', 'coffee', 'sugar']
    softs_cols = ['coffee', 'sugar']
    
    df_grains['grains_pca'] = rolling_pca(df_grains, grains_cols)
    df_grains['agri_pca'] = rolling_pca(df_grains, agri_cols)
    df_grains['softs_pca'] = rolling_pca(df_grains, softs_cols)
    
    print(f"Grains PCA: {len(df_grains)}건 계산 완료")
    print(df_grains[['date', 'grains_pca', 'agri_pca', 'softs_pca']].tail(5))
    
    # ===== 3. Stock PCA =====
    print("\n--- Stock 데이터 로딩 중 ---")
    query_stock = """
    SELECT date, sp500, dow_jones, nasdaq, kospi, kosdaq
    FROM stock
    WHERE date >= '2010-01-01'
    ORDER BY date
    """
    df_stock = pd.read_sql(query_stock, engine)
    df_stock = df_stock.sort_values('date').reset_index(drop=True)
    
    print("Stock PCA 계산 중...")
    stock_cols = ['sp500', 'dow_jones', 'nasdaq', 'kospi', 'kosdaq']
    us_cols = ['sp500', 'dow_jones', 'nasdaq']
    kr_cols = ['kospi', 'kosdaq']
    
    df_stock['stock_pca'] = rolling_pca(df_stock, stock_cols)
    df_stock['us_stock_pca'] = rolling_pca(df_stock, us_cols)
    df_stock['kr_stock_pca'] = rolling_pca(df_stock, kr_cols)
    
    print(f"Stock PCA: {len(df_stock)}건 계산 완료")
    print(df_stock[['date', 'stock_pca', 'us_stock_pca', 'kr_stock_pca']].tail(5))
    
    # ===== 4. DB 저장 =====
    print("\n--- PCA 테이블에 저장 중 ---")
    
    with engine.begin() as conn:
        # Commodities PCA 저장
        for _, row in df_commod[['date', 'metals_pca', 'oil_pca', 'commodities_pca']].iterrows():
            sql = '''
            INSERT INTO pca (date, metals_pca, oil_pca, commodities_pca)
            VALUES (:date, :metals_pca, :oil_pca, :commodities_pca)
            ON CONFLICT (date) DO UPDATE SET
                metals_pca = EXCLUDED.metals_pca,
                oil_pca = EXCLUDED.oil_pca,
                commodities_pca = EXCLUDED.commodities_pca;
            '''
            conn.execute(text(sql), {
                'date': row['date'],
                'metals_pca': row['metals_pca'],
                'oil_pca': row['oil_pca'],
                'commodities_pca': row['commodities_pca'],
            })
        print(f"Commodities PCA: {len(df_commod)}건 저장 완료")
        
        # Grains PCA 저장
        for _, row in df_grains[['date', 'grains_pca', 'agri_pca', 'softs_pca']].iterrows():
            sql = '''
            INSERT INTO pca (date, grains_pca, agri_pca, softs_pca)
            VALUES (:date, :grains_pca, :agri_pca, :softs_pca)
            ON CONFLICT (date) DO UPDATE SET
                grains_pca = EXCLUDED.grains_pca,
                agri_pca = EXCLUDED.agri_pca,
                softs_pca = EXCLUDED.softs_pca;
            '''
            conn.execute(text(sql), {
                'date': row['date'],
                'grains_pca': row['grains_pca'],
                'agri_pca': row['agri_pca'],
                'softs_pca': row['softs_pca'],
            })
        print(f"Grains PCA: {len(df_grains)}건 저장 완료")
        
        # Stock PCA 저장
        for _, row in df_stock[['date', 'stock_pca', 'us_stock_pca', 'kr_stock_pca']].iterrows():
            sql = '''
            INSERT INTO pca (date, stock_pca, us_stock_pca, kr_stock_pca)
            VALUES (:date, :stock_pca, :us_stock_pca, :kr_stock_pca)
            ON CONFLICT (date) DO UPDATE SET
                stock_pca = EXCLUDED.stock_pca,
                us_stock_pca = EXCLUDED.us_stock_pca,
                kr_stock_pca = EXCLUDED.kr_stock_pca;
            '''
            conn.execute(text(sql), {
                'date': row['date'],
                'stock_pca': row['stock_pca'],
                'us_stock_pca': row['us_stock_pca'],
                'kr_stock_pca': row['kr_stock_pca'],
            })
        print(f"Stock PCA: {len(df_stock)}건 저장 완료")
    
    print(f"\n=== PCA 전체 계산 완료 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ===")


if __name__ == "__main__":
    main()