
import React, { useEffect, useState } from 'react';
import { MainPageResponseDto } from '../types/mainPageTypes';
import { fetchTodayInfo, fetchLatestExchangeFromPostgre, fetchLatestGrainsFromPostgre, fetchLatestCommoditiesFromPostgre, fetchLatestCommoditiesIndexFromPostgre, fetchLatestStockFromPostgre } from '../api/mainPageApi';
import CommoditiesSection from '../components/main/CommoditiesSection';
import CommoditiesIndexSection from '../components/main/CommoditiesIndexSection';
import ExchangeSection from '../components/main/ExchangeSection';
import ExchangePostgreSection from '../components/main/ExchangePostgreSection';
import InterestRateSection from '../components/main/InterestRateSection';
import StockSection from '../components/main/StockSection';
import StockPostgreSection from '../components/main/StockPostgreSection';
import GrainsSection from '../components/main/GrainsSection';
import SectionContainer from '../components/main/SectionContainer';
import MentalSection from '../components/main/MentalSection';
import GrainsPostgreSection from '../components/main/GrainsPostgreSection';
import CommoditiesPostgreSection from '../components/main/CommoditiesPostgreSection';
import CommoditiesIndexPostgreSection from '../components/main/CommoditiesIndexPostgreSection';

const MainPage: React.FC = () => {
  // PostgreSQL 주식 데이터 상태
  const [stockPostgre, setStockPostgre] = useState<any[] | null>(null);
  const [stockLoading, setStockLoading] = useState(false);
  const [stockError, setStockError] = useState<string | null>(null);
  const [showPostgreStock, setShowPostgreStock] = useState(false);

  // PostgreSQL 주식 데이터 불러오기
  const handleFetchStockPostgre = async () => {
    setStockLoading(true);
    setStockError(null);
    try {
      const result = await fetchLatestStockFromPostgre();
      setStockPostgre(result);
      setShowPostgreStock(true);
    } catch (e: any) {
      setStockError(e.message);
    } finally {
      setStockLoading(false);
    }
  };

  const handleBackToDefaultStock = () => {
    setShowPostgreStock(false);
  };

  // PostgreSQL 곡물, 원자재, 지수 데이터 상태
  const [grainsPostgre, setGrainsPostgre] = useState<any[] | null>(null);
  const [grainsLoading, setGrainsLoading] = useState(false);
  const [grainsError, setGrainsError] = useState<string | null>(null);
  const [showPostgreGrains, setShowPostgreGrains] = useState(false);

  const [commoditiesPostgre, setCommoditiesPostgre] = useState<any[] | null>(null);
  const [commoditiesLoading, setCommoditiesLoading] = useState(false);
  const [commoditiesError, setCommoditiesError] = useState<string | null>(null);
  const [showPostgreCommodities, setShowPostgreCommodities] = useState(false);

  const [commoditiesIndexPostgre, setCommoditiesIndexPostgre] = useState<any[] | null>(null);
  const [commoditiesIndexLoading, setCommoditiesIndexLoading] = useState(false);
  const [commoditiesIndexError, setCommoditiesIndexError] = useState<string | null>(null);
  const [showPostgreCommoditiesIndex, setShowPostgreCommoditiesIndex] = useState(false);

  // PostgreSQL 곡물 데이터 불러오기
  const handleFetchGrainsPostgre = async () => {
    setGrainsLoading(true);
    setGrainsError(null);
    try {
      const result = await fetchLatestGrainsFromPostgre();
      setGrainsPostgre(result);
      setShowPostgreGrains(true);
    } catch (e: any) {
      setGrainsError(e.message);
    } finally {
      setGrainsLoading(false);
    }
  };

  const handleBackToDefaultGrains = () => {
    setShowPostgreGrains(false);
  };

  // PostgreSQL 원자재 데이터 불러오기
  const handleFetchCommoditiesPostgre = async () => {
    setCommoditiesLoading(true);
    setCommoditiesError(null);
    try {
      const result = await fetchLatestCommoditiesFromPostgre();
      setCommoditiesPostgre(result);
      setShowPostgreCommodities(true);
    } catch (e: any) {
      setCommoditiesError(e.message);
    } finally {
      setCommoditiesLoading(false);
    }
  };

  const handleBackToDefaultCommodities = () => {
    setShowPostgreCommodities(false);
  };

  // PostgreSQL 지수 데이터 불러오기
  const handleFetchCommoditiesIndexPostgre = async () => {
    setCommoditiesIndexLoading(true);
    setCommoditiesIndexError(null);
    try {
      const result = await fetchLatestCommoditiesIndexFromPostgre();
      setCommoditiesIndexPostgre(result);
      setShowPostgreCommoditiesIndex(true);
    } catch (e: any) {
      setCommoditiesIndexError(e.message);
    } finally {
      setCommoditiesIndexLoading(false);
    }
  };

  const handleBackToDefaultCommoditiesIndex = () => {
    setShowPostgreCommoditiesIndex(false);
  };

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
        {!showPostgreStock ? (
          <>
            <div style={{ marginBottom: 16 }}>
              <button onClick={handleFetchStockPostgre} disabled={stockLoading}>
                {stockLoading ? '불러오는 중...' : '최신 주식(PostgreSQL) 보기'}
              </button>
              {stockError && <span style={{ color: 'red', marginLeft: 8 }}>{stockError}</span>}
            </div>
            <StockSection data={[...(data.sp500List || []), ...(data.dowJonesList || []), ...(data.nasdaqList || []), ...(data.kospiList || []), ...(data.kosdaqList || [])]} />
          </>
        ) : (
          <StockPostgreSection data={stockPostgre || []} onBack={handleBackToDefaultStock} />
        )}
      </SectionContainer>

      <SectionContainer>
        {!showPostgreGrains ? (
          <>
            <div style={{ marginBottom: 16 }}>
              <button onClick={handleFetchGrainsPostgre} disabled={grainsLoading}>
                {grainsLoading ? '불러오는 중...' : '최신 곡물(PostgreSQL) 보기'}
              </button>
              {grainsError && <span style={{ color: 'red', marginLeft: 8 }}>{grainsError}</span>}
            </div>
            <GrainsSection
              rice={data.riceList}
              wheat={data.wheatList}
              corn={data.cornList}
              coffee={data.coffeeList}
              sugar={data.sugarList}
            />
          </>
        ) : (
          <GrainsPostgreSection data={grainsPostgre || []} onBack={handleBackToDefaultGrains} />
        )}
      </SectionContainer>

      <SectionContainer>
        {!showPostgreCommodities ? (
          <>
            <div style={{ marginBottom: 16 }}>
              <button onClick={handleFetchCommoditiesPostgre} disabled={commoditiesLoading}>
                {commoditiesLoading ? '불러오는 중...' : '최신 원자재(PostgreSQL) 보기'}
              </button>
              {commoditiesError && <span style={{ color: 'red', marginLeft: 8 }}>{commoditiesError}</span>}
            </div>
            <CommoditiesSection
              data={{
                goldList: data.goldList,
                silverList: data.silverList,
                copperList: data.copperList,
                crudeOilList: data.crudeOilList,
                brentOilList: data.brentOilList,
              }}
            />
          </>
        ) : (
          <CommoditiesPostgreSection data={commoditiesPostgre || []} onBack={handleBackToDefaultCommodities} />
        )}
      </SectionContainer>

      <SectionContainer>
        {!showPostgreCommoditiesIndex ? (
          <>
            <div style={{ marginBottom: 16 }}>
              <button onClick={handleFetchCommoditiesIndexPostgre} disabled={commoditiesIndexLoading}>
                {commoditiesIndexLoading ? '불러오는 중...' : '최신 지수(PostgreSQL) 보기'}
              </button>
              {commoditiesIndexError && <span style={{ color: 'red', marginLeft: 8 }}>{commoditiesIndexError}</span>}
            </div>
            <CommoditiesIndexSection data={[...(data.dxyList || []), ...(data.vixList || [])]} />
          </>
        ) : (
          <CommoditiesIndexPostgreSection data={commoditiesIndexPostgre || []} onBack={handleBackToDefaultCommoditiesIndex} />
        )}
      </SectionContainer>
      <SectionContainer>
        <MentalSection
          consumerSentimentList={data.consumerSentimentList || []}
          economicSentimentList={data.economicSentimentList || []}
          newsSentimentList={data.newsSentimentList || []}
        />
      </SectionContainer>
      <SectionContainer>
        <InterestRateSection data={[...(data.korBaseRateList || []), ...(data.usFedRateList || [])]} />
      </SectionContainer>
    </div>
  );
};

export default MainPage;
