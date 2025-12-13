-- 6. grains(곡물) 테이블 생성
CREATE TABLE grains (
    date DATE NOT NULL,
    corn FLOAT,
    corn_volume FLOAT,
    wheat FLOAT,
    wheat_volume FLOAT,
    rice FLOAT,
    rice_volume FLOAT,
    coffee FLOAT,
    coffee_volume FLOAT,
    sugar FLOAT,
    sugar_volume FLOAT
) PARTITION BY RANGE (date);

-- grains 테이블 파티션 자동 생성 (2010~2025)
DO $$
DECLARE
    y INT;
BEGIN
    FOR y IN 2010..2025 LOOP
        EXECUTE format(
            'CREATE TABLE IF NOT EXISTS grains_%s PARTITION OF grains
             FOR VALUES FROM (''%s-01-01'') TO (''%s-01-01'');',
            y, y, y+1
        );
    END LOOP;
END $$;

GRANT INSERT, SELECT, UPDATE, DELETE ON TABLE grains TO exchange_admin;

-- 4. commodities 테이블 sql
CREATE TABLE commodities (
    date DATE NOT NULL,
    gold FLOAT,
    gold_volume FLOAT,
    silver FLOAT,
    silver_volume FLOAT,
    copper FLOAT,
    copper_volume FLOAT,
    crude_oil FLOAT,
    crude_oil_volume FLOAT,
    brent_oil FLOAT,
    brent_oil_volume FLOAT
) PARTITION BY RANGE (date);

CREATE TABLE commodities_index(
    date DATE NOT NULL,
    dxy FLOAT,
    vix FLOAT
) PARTITION BY RANGE (date);

-- 5. commodities 테이블 파티션 자동 생성 (2000~2025)
DO $$
DECLARE
    y INT;
BEGIN
    FOR y IN 2010..2025 LOOP
        EXECUTE format(
            'CREATE TABLE IF NOT EXISTS commodities_%s PARTITION OF commodities
             FOR VALUES FROM (''%s-01-01'') TO (''%s-01-01'');',
            y, y, y+1
        );
    END LOOP;
END $$;

DO $$
DECLARE
    y INT;
BEGIN
    FOR y IN 2010..2025 LOOP
        EXECUTE format(
            'CREATE TABLE IF NOT EXISTS commodities_index_%s PARTITION OF commodities_index
             FOR VALUES FROM (''%s-01-01'') TO (''%s-01-01'');',
            y, y, y+1
        );
    END LOOP;
END $$;

GRANT INSERT, SELECT, UPDATE, DELETE ON TABLE commodities TO exchange_admin;
GRANT INSERT, SELECT, UPDATE, DELETE ON TABLE commodities_index TO exchange_admin;