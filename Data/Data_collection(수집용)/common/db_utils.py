# common/db_utils.py
"""
MongoDB 관련 공통 함수
"""
from pymongo import MongoClient
from datetime import datetime
from typing import List, Dict, Any, Optional
from .config import MONGO_URI, MONGO_DB


def get_mongo_client():
    """MongoDB 클라이언트 생성"""
    return MongoClient(MONGO_URI)


def get_collection(client, collection_name: str):
    """컬렉션 반환"""
    db = client[MONGO_DB]
    return db[collection_name]


def create_date_index(collection, index_fields: List[tuple], unique: bool = True):
    """
    날짜 기반 인덱스 생성
    
    Args:
        collection: MongoDB 컬렉션
        index_fields: 인덱스 필드 리스트 [("date", 1), ("currency_code", 1)]
        unique: 유니크 제약 여부
    """
    try:
        collection.create_index(index_fields, unique=unique)
    except Exception as e:
        print(f"인덱스 생성 오류 (무시 가능): {e}")


def save_records(collection, records: List[Dict[str, Any]], 
                unique_fields: List[str], verbose: bool = True) -> tuple:
    """
    레코드 일괄 저장 (upsert 방식)
    
    Args:
        collection: MongoDB 컬렉션
        records: 저장할 레코드 리스트
        unique_fields: 중복 체크할 필드 리스트 (예: ["date", "currency_code"])
        verbose: 로그 출력 여부
    
    Returns:
        (inserted_count, updated_count) 튜플
    """
    inserted_count = 0
    updated_count = 0
    
    for record in records:
        try:
            # 중복 체크를 위한 쿼리 생성
            query = {field: record[field] for field in unique_fields}
            
            result = collection.replace_one(
                query,
                record,
                upsert=True
            )
            
            if result.upserted_id:
                inserted_count += 1
            elif result.modified_count > 0:
                updated_count += 1
                
        except Exception as e:
            if verbose:
                print(f"레코드 저장 오류: {e}")
    
    return inserted_count, updated_count


def save_single_record(collection, record: Dict[str, Any], 
                      unique_fields: List[str]) -> str:
    """
    단일 레코드 저장
    
    Returns:
        "inserted", "updated", "unchanged" 중 하나
    """
    try:
        query = {field: record[field] for field in unique_fields}
        result = collection.replace_one(query, record, upsert=True)
        
        if result.upserted_id:
            return "inserted"
        elif result.modified_count > 0:
            return "updated"
        else:
            return "unchanged"
    except Exception as e:
        print(f"레코드 저장 오류: {e}")
        return "error"


def get_latest_record(collection, sort_field: str = "date"):
    """최신 레코드 조회"""
    try:
        result = collection.find().sort(sort_field, -1).limit(1)
        records = list(result)
        return records[0] if records else None
    except Exception as e:
        print(f"최신 레코드 조회 오류: {e}")
        return None


def get_collection_stats(client, collection_name: str) -> Dict[str, Any]:
    """컬렉션 통계 조회"""
    collection = get_collection(client, collection_name)
    
    try:
        count = collection.count_documents({})
        latest = get_latest_record(collection)
        
        return {
            "collection_name": collection_name,
            "total_count": count,
            "latest_date": latest.get("date") if latest else None,
            "latest_value": latest.get("rate") or latest.get("close") or latest.get("value") if latest else None
        }
    except Exception as e:
        print(f"통계 조회 오류: {e}")
        return {
            "collection_name": collection_name,
            "total_count": 0,
            "error": str(e)
        }