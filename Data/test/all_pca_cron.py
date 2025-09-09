def to_float(val):
    if pd.isnull(val):
        return None
    return float(val)
import pandas as pd
from sqlalchemy import create_engine
from sklearn.decomposition import PCA
from datetime import timedelta, datetime
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_engine():
    PG_HOST = "64.110.115.12"
    PG_DB = "exchange"
    PG_USER = "exchange_admin"
    PG_PASSWORD = "exchange_password"
    return create_engine(f"postgresql+psycopg2://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:5432/{PG_DB}")

def update_recent_pca():
    """최근 2년 데이터로 PCA 모델을 훈련하고, 최근 7일 데이터만 업데이트"""
    try:

        engine = get_engine()
        today = datetime.today().date()
        update_start_date = today - timedelta(days=7)
        window_days = 365*3

        logger.info(f"최근 3년 rolling PCA, 업데이트 대상 기간: {update_start_date} ~ {today}")

        # 전체 데이터 불러오기
        query_commod = """
        SELECT date, gold, silver, copper, crude_oil, brent_oil
        FROM commodities
        WHERE date >= '2010-01-01'
        ORDER BY date
        """
        df_commod = pd.read_sql(query_commod, engine)
        commod_cols = ['gold', 'silver', 'copper', 'crude_oil', 'brent_oil']
        df_commod = df_commod.sort_values('date').reset_index(drop=True)

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

        query_stock = """
        SELECT date, sp500, dow_jones, nasdaq, kospi, kosdaq
        FROM stock
        WHERE date >= '2010-01-01'
        ORDER BY date
        """
        df_stock = pd.read_sql(query_stock, engine)
        stock_cols = ['sp500', 'dow_jones', 'nasdaq', 'kospi', 'kosdaq']
        us_cols = ['sp500', 'dow_jones', 'nasdaq']
        kr_cols = ['kospi', 'kosdaq']
        df_stock = df_stock.sort_values('date').reset_index(drop=True)

        def rolling_pca(df, cols, window_days=window_days):
            result = []
            for idx, row in df.iterrows():
                cur_date = row['date']
                if cur_date < update_start_date:
                    result.append(None)
                    continue
                start_date = cur_date - timedelta(days=window_days)
                window_df = df[(df['date'] > start_date) & (df['date'] <= cur_date)].copy()
                window_df[cols] = window_df[cols].interpolate(method='linear', limit_direction='both')
                window_df[cols] = window_df[cols].ffill().bfill()
                if window_df[cols].isnull().any().any() or len(window_df) < 2:
                    result.append(None)
                    continue
                pca = PCA(n_components=1)
                pca_val = pca.fit_transform(window_df[cols])[-1,0]
                result.append(pca_val)
            return result

        # 최근 7일만 rolling PCA 계산
        df_commod['metals_pca'] = rolling_pca(df_commod, ['gold', 'silver', 'copper'])
        df_commod['oil_pca'] = rolling_pca(df_commod, ['crude_oil', 'brent_oil'])
        df_commod['commodities_pca'] = rolling_pca(df_commod, commod_cols)

        df_grains['grains_pca'] = rolling_pca(df_grains, grains_cols)
        df_grains['agri_pca'] = rolling_pca(df_grains, agri_cols)
        df_grains['softs_pca'] = rolling_pca(df_grains, softs_cols)

        df_stock['stock_pca'] = rolling_pca(df_stock, stock_cols)
        df_stock['us_stock_pca'] = rolling_pca(df_stock, us_cols)
        df_stock['kr_stock_pca'] = rolling_pca(df_stock, kr_cols)

        # 최근 7일 데이터만 추출
        recent_commod = df_commod[df_commod['date'] >= update_start_date]
        recent_grains = df_grains[df_grains['date'] >= update_start_date]
        recent_stock = df_stock[df_stock['date'] >= update_start_date]

        # DB 저장
        from sqlalchemy import text as sa_text
        all_dates = set(recent_commod['date'].tolist() + recent_grains['date'].tolist() + recent_stock['date'].tolist())
        inserted_count = 0
        updated_count = 0
        with engine.begin() as conn:
            for date in sorted(all_dates):
                check_sql = sa_text("SELECT 1 FROM pca WHERE date = :date LIMIT 1")
                result = conn.execute(check_sql, {'date': date}).fetchone()
                data = {'date': date}
                commod_row = recent_commod[recent_commod['date'] == date]
                if not commod_row.empty:
                    data.update({
                            'metals_pca': to_float(round(commod_row.iloc[0]['metals_pca'], 4)),
                            'oil_pca': to_float(round(commod_row.iloc[0]['oil_pca'], 4)),
                            'commodities_pca': to_float(round(commod_row.iloc[0]['commodities_pca'], 4))
                    })
                grains_row = recent_grains[recent_grains['date'] == date]
                if not grains_row.empty:
                    data.update({
                            'grains_pca': to_float(round(grains_row.iloc[0]['grains_pca'], 4)),
                            'agri_pca': to_float(round(grains_row.iloc[0]['agri_pca'], 4)),
                            'softs_pca': to_float(round(grains_row.iloc[0]['softs_pca'], 4))
                    })
                stock_row = recent_stock[recent_stock['date'] == date]
                if not stock_row.empty:
                    data.update({
                            'stock_pca': to_float(round(stock_row.iloc[0]['stock_pca'], 4)),
                            'us_stock_pca': to_float(round(stock_row.iloc[0]['us_stock_pca'], 4)),
                            'kr_stock_pca': to_float(round(stock_row.iloc[0]['kr_stock_pca'], 4))
                    })
                if result:
                    update_parts = []
                    update_data = {'date': date}
                    for key, value in data.items():
                        if key != 'date':
                            update_parts.append(f"{key} = :{key}")
                            update_data[key] = value
                    if update_parts:
                        update_sql = f"UPDATE pca SET {', '.join(update_parts)} WHERE date = :date"
                        conn.execute(sa_text(update_sql), update_data)
                        updated_count += 1
                else:
                    columns = list(data.keys())
                    placeholders = [f":{col}" for col in columns]
                    insert_sql = f"INSERT INTO pca ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
                    conn.execute(sa_text(insert_sql), data)
                    inserted_count += 1
        logger.info(f"PCA 업데이트 완료 - INSERT: {inserted_count}건, UPDATE: {updated_count}건")
        
    except Exception as e:
        logger.error(f"PCA 계산 중 오류 발생: {e}")
        raise

if __name__ == "__main__":
    update_recent_pca()
