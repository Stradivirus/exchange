# PreProcessing/all_pca_cron.py
"""
PCA 일일 업데이트 (최근 7일)
3년 rolling window로 PCA 계산하되, 최근 7일치만 업데이트
"""
import os
import pandas as pd
from sqlalchemy import create_engine, text
from sklearn.decomposition import PCA
from datetime import timedelta, datetime
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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


def to_float(val):
    """안전한 float 변환"""
    if pd.isnull(val):
        return None
    return float(val)


def rolling_pca(df, cols, window_days, update_start_date):
    """
    Rolling PCA 계산 (최근 7일만)
    
    Args:
        df: DataFrame
        cols: PCA 계산할 컬럼 리스트
        window_days: 윈도우 크기 (일수)
        update_start_date: 업데이트 시작 날짜
    
    Returns:
        PCA 값 리스트
    """
    result = []
    
    for idx, row in df.iterrows():
        cur_date = row['date']
        
        # 최근 7일 이전 데이터는 건너뛰기
        if cur_date < update_start_date:
            result.append(None)
            continue
        
        start_date = cur_date - timedelta(days=window_days)
        window_df = df[(df['date'] > start_date) & (df['date'] <= cur_date)].copy()
        
        # 결측치 처리
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


def update_recent_pca():
    """최근 7일 PCA 업데이트"""
    try:
        engine = get_engine()
        today = datetime.today().date()
        update_start_date = today - timedelta(days=7)
        window_days = 365 * 3  # 3년 rolling window
        
        logger.info(f"최근 3년 rolling PCA 계산, 업데이트 기간: {update_start_date} ~ {today}")
        
        # ===== 1. Commodities 데이터 로딩 =====
        logger.info("Commodities 데이터 로딩 중...")
        query_commod = """
        SELECT date, gold, silver, copper, crude_oil, brent_oil
        FROM commodities
        WHERE date >= '2010-01-01'
        ORDER BY date
        """
        df_commod = pd.read_sql(query_commod, engine)
        df_commod = df_commod.sort_values('date').reset_index(drop=True)
        
        # ===== 2. Grains 데이터 로딩 =====
        logger.info("Grains 데이터 로딩 중...")
        query_grains = """
        SELECT date, corn, wheat, rice, coffee, sugar
        FROM grains
        WHERE date >= '2010-01-01'
        ORDER BY date
        """
        df_grains = pd.read_sql(query_grains, engine)
        df_grains = df_grains.sort_values('date').reset_index(drop=True)
        
        # ===== 3. Stock 데이터 로딩 =====
        logger.info("Stock 데이터 로딩 중...")
        query_stock = """
        SELECT date, sp500, dow_jones, nasdaq, kospi, kosdaq
        FROM stock
        WHERE date >= '2010-01-01'
        ORDER BY date
        """
        df_stock = pd.read_sql(query_stock, engine)
        df_stock = df_stock.sort_values('date').reset_index(drop=True)
        
        # ===== 4. PCA 계산 (최근 7일만) =====
        logger.info("PCA 계산 중...")
        
        # Commodities
        df_commod['metals_pca'] = rolling_pca(
            df_commod, ['gold', 'silver', 'copper'], window_days, update_start_date
        )
        df_commod['oil_pca'] = rolling_pca(
            df_commod, ['crude_oil', 'brent_oil'], window_days, update_start_date
        )
        df_commod['commodities_pca'] = rolling_pca(
            df_commod, ['gold', 'silver', 'copper', 'crude_oil', 'brent_oil'], 
            window_days, update_start_date
        )
        
        # Grains
        df_grains['grains_pca'] = rolling_pca(
            df_grains, ['corn', 'wheat', 'rice'], window_days, update_start_date
        )
        df_grains['agri_pca'] = rolling_pca(
            df_grains, ['corn', 'wheat', 'rice', 'coffee', 'sugar'], 
            window_days, update_start_date
        )
        df_grains['softs_pca'] = rolling_pca(
            df_grains, ['coffee', 'sugar'], window_days, update_start_date
        )
        
        # Stock
        df_stock['stock_pca'] = rolling_pca(
            df_stock, ['sp500', 'dow_jones', 'nasdaq', 'kospi', 'kosdaq'], 
            window_days, update_start_date
        )
        df_stock['us_stock_pca'] = rolling_pca(
            df_stock, ['sp500', 'dow_jones', 'nasdaq'], window_days, update_start_date
        )
        df_stock['kr_stock_pca'] = rolling_pca(
            df_stock, ['kospi', 'kosdaq'], window_days, update_start_date
        )
        
        # ===== 5. 최근 7일 데이터만 추출 =====
        recent_commod = df_commod[df_commod['date'] >= update_start_date]
        recent_grains = df_grains[df_grains['date'] >= update_start_date]
        recent_stock = df_stock[df_stock['date'] >= update_start_date]
        
        logger.info(f"최근 데이터: Commodities {len(recent_commod)}건, "
                   f"Grains {len(recent_grains)}건, Stock {len(recent_stock)}건")
        
        # ===== 6. DB 저장 =====
        logger.info("DB에 저장 중...")
        
        all_dates = set(
            recent_commod['date'].tolist() + 
            recent_grains['date'].tolist() + 
            recent_stock['date'].tolist()
        )
        
        inserted_count = 0
        updated_count = 0
        
        with engine.begin() as conn:
            for date in sorted(all_dates):
                # 기존 레코드 확인
                check_sql = text("SELECT 1 FROM pca WHERE date = :date LIMIT 1")
                result = conn.execute(check_sql, {'date': date}).fetchone()
                
                # 데이터 수집
                data = {'date': date}
                
                # Commodities 데이터
                commod_row = recent_commod[recent_commod['date'] == date]
                if not commod_row.empty:
                    data.update({
                        'metals_pca': to_float(commod_row.iloc[0]['metals_pca']),
                        'oil_pca': to_float(commod_row.iloc[0]['oil_pca']),
                        'commodities_pca': to_float(commod_row.iloc[0]['commodities_pca'])
                    })
                
                # Grains 데이터
                grains_row = recent_grains[recent_grains['date'] == date]
                if not grains_row.empty:
                    data.update({
                        'grains_pca': to_float(grains_row.iloc[0]['grains_pca']),
                        'agri_pca': to_float(grains_row.iloc[0]['agri_pca']),
                        'softs_pca': to_float(grains_row.iloc[0]['softs_pca'])
                    })
                
                # Stock 데이터
                stock_row = recent_stock[recent_stock['date'] == date]
                if not stock_row.empty:
                    data.update({
                        'stock_pca': to_float(stock_row.iloc[0]['stock_pca']),
                        'us_stock_pca': to_float(stock_row.iloc[0]['us_stock_pca']),
                        'kr_stock_pca': to_float(stock_row.iloc[0]['kr_stock_pca'])
                    })
                
                # INSERT 또는 UPDATE
                if result:
                    # UPDATE
                    update_parts = []
                    update_data = {'date': date}
                    
                    for key, value in data.items():
                        if key != 'date' and value is not None:
                            update_parts.append(f"{key} = :{key}")
                            update_data[key] = value
                    
                    if update_parts:
                        update_sql = f"UPDATE pca SET {', '.join(update_parts)} WHERE date = :date"
                        conn.execute(text(update_sql), update_data)
                        updated_count += 1
                else:
                    # INSERT
                    columns = [k for k, v in data.items() if v is not None]
                    placeholders = [f":{col}" for col in columns]
                    insert_sql = f"INSERT INTO pca ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
                    insert_data = {k: v for k, v in data.items() if v is not None}
                    conn.execute(text(insert_sql), insert_data)
                    inserted_count += 1
        
        logger.info(f"PCA 업데이트 완료 - INSERT: {inserted_count}건, UPDATE: {updated_count}건")
        
    except Exception as e:
        logger.error(f"PCA 계산 중 오류 발생: {e}")
        raise


if __name__ == "__main__":
    update_recent_pca()