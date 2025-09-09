CREATE TABLE pca (
    date DATE NOT NULL,
    metals_pca NUMERIC(20,4),
    oil_pca NUMERIC(20,4),
    commodities_pca NUMERIC(20,4),
    grains_pca NUMERIC(20,4),
    agri_pca NUMERIC(20,4),
    softs_pca NUMERIC(20,4),
    stock_pca NUMERIC(20,4),
    us_stock_pca NUMERIC(20,4),
    kr_stock_pca NUMERIC(20,4),
    PRIMARY KEY (date)
) PARTITION BY RANGE (date);

DO $$
DECLARE
    y INT;
BEGIN
    FOR y IN 2010..2025 LOOP
        EXECUTE format(
            'CREATE TABLE IF NOT EXISTS pca_%s PARTITION OF pca
             FOR VALUES FROM (''%s-01-01'') TO (''%s-01-01'');',
            y, y, y+1
        );
    END LOOP;
END $$;

GRANT INSERT, SELECT, UPDATE, DELETE ON TABLE pca TO exchange_admin;