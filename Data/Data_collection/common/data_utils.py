# common/data_utils.py
"""
데이터 처리 관련 공통 함수
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Any


def safe_clean_value(value: Any) -> Any:
    """
    안전한 데이터 변환 함수
    pandas Series, NaN, Timestamp, numpy 타입 등을 처리
    
    Args:
        value: 변환할 값
        
    Returns:
        Python 기본 타입으로 변환된 값
    """
    # pandas Series가 넘어올 경우 첫 번째 값 사용
    if isinstance(value, pd.Series):
        value = value.iloc[0]
    
    # NaN 체크
    if pd.isna(value):
        return None
    
    # Timestamp 변환
    if isinstance(value, (pd.Timestamp, np.datetime64)):
        return pd.to_datetime(value).to_pydatetime()
    
    # numpy 숫자 타입 변환
    if isinstance(value, (np.integer, np.floating)):
        return float(value)
    
    # 복잡한 타입은 문자열로 변환
    if isinstance(value, (tuple, list, dict)):
        return str(value)
    
    return value


def get_recent_date_range(days_back: int = 5, date_format: str = '%Y%m%d') -> tuple:
    """
    최근 날짜 범위 반환
    
    Args:
        days_back: 며칠 전까지 조회할지
        date_format: 날짜 포맷 (기본: YYYYMMDD)
        
    Returns:
        (start_date, end_date) 튜플
    """
    today = datetime.now()
    start_date = (today - timedelta(days=days_back)).strftime(date_format)
    end_date = today.strftime(date_format)
    return start_date, end_date


def get_recent_month_range(months_back: int = 1) -> tuple:
    """
    최근 월 범위 반환
    
    Args:
        months_back: 몇 달 전까지 조회할지
        
    Returns:
        (start_month, end_month) 튜플 (YYYYMM 형식)
    """
    today = datetime.now()
    start_date = (today - pd.DateOffset(months=months_back)).replace(day=1)
    start_month = start_date.strftime('%Y%m')
    end_month = today.strftime('%Y%m')
    return start_month, end_month


def dataframe_to_records(df: pd.DataFrame, 
                        date_column: str = 'date',
                        additional_fields: dict = None) -> list:
    """
    DataFrame을 MongoDB 레코드 리스트로 변환
    
    Args:
        df: 변환할 DataFrame
        date_column: 날짜 컬럼명
        additional_fields: 추가할 필드 딕셔너리 (예: {'source': 'BOK'})
        
    Returns:
        레코드 리스트
    """
    records = []
    
    for _, row in df.iterrows():
        record = {}
        
        # 모든 컬럼 변환
        for col in df.columns:
            record[col] = safe_clean_value(row[col])
        
        # created_at 추가
        record['created_at'] = datetime.now()
        
        # 추가 필드
        if additional_fields:
            record.update(additional_fields)
        
        records.append(record)
    
    return records


def filter_changed_values(df: pd.DataFrame, 
                         value_column: str,
                         date_column: str = 'date',
                         tolerance: float = 0.01) -> pd.DataFrame:
    """
    값이 변동된 행만 필터링
    (기준금리처럼 변동이 있을 때만 저장해야 하는 경우)
    
    Args:
        df: DataFrame
        value_column: 비교할 값 컬럼
        date_column: 날짜 컬럼
        tolerance: 허용 오차
        
    Returns:
        변동된 행만 포함한 DataFrame
    """
    df = df.sort_values(date_column)
    df['prev_value'] = df[value_column].shift(1)
    
    # 첫 행이거나 값이 변경된 행만 선택
    changed = df[
        (df['prev_value'].isna()) | 
        (abs(df[value_column] - df['prev_value']) >= tolerance)
    ]
    
    return changed.drop('prev_value', axis=1)


def print_summary(data_name: str, inserted: int, updated: int, 
                 latest_value: Any = None, latest_date: datetime = None):
    """
    데이터 수집 결과 요약 출력
    
    Args:
        data_name: 데이터 이름
        inserted: 신규 삽입 개수
        updated: 업데이트 개수
        latest_value: 최신 값
        latest_date: 최신 날짜
    """
    if inserted > 0 or updated > 0:
        msg = f"{data_name}: 신규 {inserted}개, 업데이트 {updated}개"
        
        if latest_value is not None and latest_date is not None:
            date_str = latest_date.strftime('%Y-%m-%d')
            
            # 숫자 형식 처리
            if isinstance(latest_value, (int, float)):
                if latest_value > 1000:
                    value_str = f"{latest_value:,.2f}"
                else:
                    value_str = f"{latest_value:.2f}"
            else:
                value_str = str(latest_value)
            
            msg += f", 최신값: {value_str} ({date_str})"
        
        print(msg)
    else:
        print(f"{data_name}: 변경사항 없음")


def retry_on_failure(func, max_retries: int = 3, delay: float = 1.0):
    """
    실패시 재시도하는 데코레이터
    
    Args:
        func: 실행할 함수
        max_retries: 최대 재시도 횟수
        delay: 재시도 간 대기 시간(초)
    """
    import time
    
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"재시도 {attempt + 1}/{max_retries}: {e}")
                time.sleep(delay)
            else:
                print(f"최종 실패: {e}")
                raise