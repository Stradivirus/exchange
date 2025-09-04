# 프로젝트 개요

- 크롤링 데이터는 테스트용으로 저장합니다.

## 데이터 수집 (Data Collection)
- MongoDB Atlas 사용
- 데이터 출처: 한국은행, 야후 파이낸스, FRED 등

## 전처리 (Preprocessing)
- PostgreSQL 사용
- MongoDB Atlas에 수집된 정보를 연도별로 파티션된 테이블에 저장

## test 폴더
- 터미널에서 직접 실행

## 프론트엔드 + 백엔드 + Docker
- 시각화 코드 포함