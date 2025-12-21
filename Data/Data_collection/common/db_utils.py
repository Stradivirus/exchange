# common/db_utils.py
from pymongo import MongoClient, UpdateOne, DESCENDING
from common.config import MONGO_URI, MONGO_DB

def get_mongo_client():
    """MongoDB 클라이언트 반환"""
    return MongoClient(MONGO_URI)

def get_collection(client, collection_name):
    """컬렉션 반환"""
    db = client[MONGO_DB]
    return db[collection_name]

def create_date_index(collection, index_fields):
    """인덱스 생성 (중복 방지 및 조회 성능 향상)"""
    # date 필드가 있으면 기본 인덱스 생성
    existing_indexes = collection.index_information()
    
    # 복합 인덱스 이름 생성
    index_name = "_".join([f"{field}_{direction}" for field, direction in index_fields])
    
    if index_name not in existing_indexes:
        collection.create_index(index_fields, unique=True)
        # print(f"인덱스 생성 완료: {index_name}")

def get_latest_record(collection, sort_field="date"):
    """
    컬렉션에서 가장 최근 레코드 1개를 조회
    """
    try:
        latest = collection.find_one(sort=[(sort_field, DESCENDING)])
        return latest
    except Exception as e:
        print(f"최근 레코드 조회 실패: {e}")
        return None

def save_records(collection, records, unique_fields, verbose=False):
    """
    데이터 대량 저장 (Bulk Write) - Upsert 방식
    """
    if not records:
        return 0, 0
        
    operations = []
    for record in records:
        # 중복 체크를 위한 필터 생성
        filter_doc = {field: record[field] for field in unique_fields}
        
        # UpdateOne(filter, update, upsert=True)
        op = UpdateOne(
            filter_doc,
            {"$set": record},
            upsert=True
        )
        operations.append(op)
    
    if operations:
        try:
            result = collection.bulk_write(operations)
            if verbose:
                print(f"저장 완료: 신규/수정 {result.upserted_count + result.modified_count}건")
            return result.upserted_count, result.modified_count
        except Exception as e:
            print(f"Bulk Write 오류: {e}")
            return 0, 0
    return 0, 0