-- 1. 파티션 테이블 생성
CREATE TABLE interest_rate (
    date DATE NOT NULL,
    kor_base_rate FLOAT,
    us_fed_rate FLOAT
) PARTITION BY RANGE (date);

-- 2. 연도별 파티션 자동 생성 (2000~2025)
DO $$
DECLARE
    y INT;
BEGIN
    FOR y IN 2000..2025 LOOP
        EXECUTE format(
            'CREATE TABLE IF NOT EXISTS interest_rate_%s PARTITION OF interest_rate
             FOR VALUES FROM (''%s-01-01'') TO (''%s-01-01'');',
            y, y, y+1
        );
    END LOOP;
END $$;

-- 3. 권한 부여 (슈퍼유저로 실행)
GRANT INSERT, SELECT, UPDATE, DELETE ON TABLE interest_rate TO exchange_admin;