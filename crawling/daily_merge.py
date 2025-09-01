import os
from sqlalchemy import create_engine
import pandas as pd
from pymongo import MongoClient

# 환경변수 또는 상수로 DB 접속 정보 관리
PG_HOST = os.getenv("PG_HOST", "64.110.115.12")
PG_DB = os.getenv("PG_DB", "exchange_rate")
PG_USER = os.getenv("PG_USER", "exchange_admin")
PG_PASSWORD = os.getenv("PG_PASSWORD", "exchange_password")
PG_TABLE = os.getenv("PG_TABLE", "daily_exchange")

def save_daily_to_postgres(df, ip=PG_HOST, db=PG_DB, user=PG_USER, password=PG_PASSWORD, table=PG_TABLE):
    """
    일별 집계 데이터프레임을 PostgreSQL에 저장
    """
    # 결측치 보간: 각 컬럼별로 ffill, bfill 순서로
    for col in ["dollar", "gold", "oil", "dxy", "base_rate", "us_base_rate"]:
        df[col] = df[col].ffill().bfill()
    # 컬럼 순서 맞추기 (date, dollar, gold, oil, dxy, base_rate, us_base_rate)
    df_save = df[["date_only", "dollar", "gold", "oil", "dxy", "base_rate", "us_base_rate"]].copy()
    df_save = df_save.rename(columns={"date_only": "date"})
    # DB 연결
    engine = create_engine(
        f"postgresql+psycopg2://{user}:{password}@{ip}:5432/{db}"
    )
    # 저장
    df_save.to_sql(table, engine, if_exists="replace", index=False)
    print(f"PostgreSQL({db}) {table} 테이블에 저장 완료!")
    print("저장 직전 데이터 미리보기:")
    print(df_save.head())
    print("행 개수:", len(df_save))

def get_daily_dollar(df_dollar):
    """
    환율 데이터프레임에서 하루 평균 환율 집계
    """
    df_dollar["date_only"] = df_dollar["date"].dt.date
    df_dollar_daily = df_dollar.groupby("date_only")["dollar"].mean().reset_index()
    return df_dollar_daily

# 1. MongoDB에서 데이터 불러오기
client = MongoClient("mongodb+srv://stradivirus:1q2w3e4r6218@cluster0.e7rvfpz.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client["exchange"]

def load_collection_to_df(collection_name, date_field="datetime", value_field="price"):
    data = list(db[collection_name].find({}, {date_field: 1, value_field: 1, "_id": 0}))
    df = pd.DataFrame(data)
    df = df.sort_values(date_field)
    df = df.rename(columns={date_field: "date", value_field: collection_name})
    return df


df_dollar = load_collection_to_df("dollar")
df_gold = load_collection_to_df("gold")
df_oil = load_collection_to_df("oil")
df_dxy = load_collection_to_df("dxy")
# 금리 등도 동일하게

# 2. 집계 및 결측치 처리
df_dollar["date_only"] = df_dollar["date"].dt.date
df_dollar_daily = df_dollar.groupby("date_only")["dollar"].mean().reset_index()

# gold, oil, dxy, 금리 등도 하루 평균 집계
df_gold["date_only"] = df_gold["date"].dt.date
df_gold_daily = df_gold.groupby("date_only")["gold"].mean().reset_index()

df_oil["date_only"] = df_oil["date"].dt.date
df_oil_daily = df_oil.groupby("date_only")["oil"].mean().reset_index()

df_dxy["date_only"] = df_dxy["date"].dt.date
df_dxy_daily = df_dxy.groupby("date_only")["dxy"].mean().reset_index()

# 금리 등도 동일하게 (예시)
df_base_rate = load_collection_to_df("base_rate", date_field="date", value_field="rate")
df_base_rate["date_only"] = df_base_rate["date"].dt.date
df_base_rate_daily = df_base_rate.groupby("date_only")["base_rate"].mean().reset_index()
df_us_base_rate = load_collection_to_df("us_base_rate", date_field="date", value_field="rate")
df_us_base_rate["date_only"] = df_us_base_rate["date"].dt.date
df_us_base_rate_daily = df_us_base_rate.groupby("date_only")["us_base_rate"].mean().reset_index()

# merge 리스트 완성 (금리까지 포함)
dfs = [df_dollar_daily, df_gold_daily, df_oil_daily, df_dxy_daily, df_base_rate_daily, df_us_base_rate_daily]

# 3. 날짜 기준으로 merge
df = dfs[0]
for d in dfs[1:]:
    df = pd.merge(df, d, on="date_only", how="outer")

# 4. 결측치 처리
for col in ["dollar", "gold", "oil", "dxy", "base_rate", "us_base_rate"]:
    df[col] = df[col].ffill().bfill()

# 5. PostgreSQL에 저장
print("최종 merge 데이터:", df.shape)
save_daily_to_postgres(df)