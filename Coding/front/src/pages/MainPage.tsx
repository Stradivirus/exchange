import React, { useEffect, useState } from 'react';
import { MainPageResponseDto } from '../types/mainPageTypes';
import { fetchTodayInfo, fetchLatestExchangeFromPostgre } from '../api/mainPageApi';

import CommoditiesSection from '../components/main/CommoditiesSection';
import CommoditiesIndexSection from '../components/main/CommoditiesIndexSection';
import ExchangeSection from '../components/main/ExchangeSection';
import ExchangePostgreSection from '../components/main/ExchangePostgreSection';
import InterestRateSection from '../components/main/InterestRateSection';
import StockSection from '../components/main/StockSection';
import GrainsSection from '../components/main/GrainsSection';
import SectionContainer from '../components/main/SectionContainer';

const MainPage: React.FC = () => {

  const [data, setData] = useState<MainPageResponseDto | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // PostgreSQL 환율 데이터 상태

  const [exchangePostgre, setExchangePostgre] = useState<any[] | null>(null);
  const [exchangeLoading, setExchangeLoading] = useState(false);
  const [exchangeError, setExchangeError] = useState<string | null>(null);
  const [showPostgreExchange, setShowPostgreExchange] = useState(false);


  useEffect(() => {
    fetchTodayInfo()
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  // PostgreSQL 환율 데이터 불러오기

  const handleFetchExchangePostgre = async () => {
    setExchangeLoading(true);
    setExchangeError(null);
    try {
      const result = await fetchLatestExchangeFromPostgre();
      setExchangePostgre(result);
      setShowPostgreExchange(true);
    } catch (e: any) {
      setExchangeError(e.message);
    } finally {
      setExchangeLoading(false);
    }
  };

  const handleBackToDefaultExchange = () => {
    setShowPostgreExchange(false);
  };

  if (loading) return <div>로딩 중...</div>;
  if (error) return <div>에러: {error}</div>;
  if (!data) return <div>데이터 없음</div>;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', background: '#f7f7f7', minHeight: '100vh', padding: '32px 0' }}>
      <h1 style={{ marginBottom: 32 }}>최신 주요 지표</h1>
      <SectionContainer>
        {!showPostgreExchange ? (
          <>
            <div style={{ marginBottom: 16 }}>
              <button onClick={handleFetchExchangePostgre} disabled={exchangeLoading}>
                {exchangeLoading ? '불러오는 중...' : '최신 환율(PostgreSQL) 보기'}
              </button>
              {exchangeError && <span style={{ color: 'red', marginLeft: 8 }}>{exchangeError}</span>}
            </div>
            <ExchangeSection
              data={
                [
                  ...(data.usdList || []),
                  ...(data.jpyList || []),
                  ...(data.eurList || []),
                  ...(data.cnyList || []),
                ]
              }
            />
          </>
        ) : (
          <ExchangePostgreSection data={exchangePostgre || []} onBack={handleBackToDefaultExchange} />
        )}
      </SectionContainer>
      <SectionContainer>
        <StockSection data={[...(data.sp500List || []), ...(data.dowJonesList || []), ...(data.nasdaqList || []), ...(data.kospiList || []), ...(data.kosdaqList || [])]} />
      </SectionContainer>
      <SectionContainer>
        <GrainsSection
          rice={data.riceList}
          wheat={data.wheatList}
          corn={data.cornList}
          coffee={data.coffeeList}
          sugar={data.sugarList}
        />
      </SectionContainer>
      <SectionContainer>
        <CommoditiesSection
          data={{
            goldList: data.goldList,
            silverList: data.silverList,
            copperList: data.copperList,
            crudeOilList: data.crudeOilList,
            brentOilList: data.brentOilList,
          }}
        />
      </SectionContainer>
      <SectionContainer>
        <CommoditiesIndexSection data={[...(data.dxyList || []), ...(data.vixList || [])]} />
      </SectionContainer>
      <SectionContainer>
        <InterestRateSection data={[...(data.korBaseRateList || []), ...(data.usFedRateList || [])]} />
      </SectionContainer>
    </div>
  );
};

export default MainPage;
