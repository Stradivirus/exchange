import React, { useEffect, useState } from 'react';
import { MainPageResponseDto } from '../types/mainPageTypes';
import { 
  fetchTodayInfo, 
  fetchLatestExchange, 
  fetchLatestGrains, 
  fetchLatestCommodities, 
  fetchLatestCommoditiesIndex, 
  fetchLatestStock 
} from '../api/mainPageApi';

// MongoDB 관련 컴포넌트 (오늘자 데이터)
import CommoditiesSection from '../components/mongo/CommoditiesSection';
import CommoditiesIndexSection from '../components/mongo/CommoditiesIndexSection';
import ExchangeSection from '../components/mongo/ExchangeSection';
import InterestRateSection from '../components/mongo/InterestRateSection';
import StockSection from '../components/mongo/StockSection';
import GrainsSection from '../components/mongo/GrainsSection';
import SectionContainer from '../components/mongo/SectionContainer';
import MentalSection from '../components/mongo/MentalSection';

// 최신 30일 데이터 표시 컴포넌트 (기존 postgre 폴더 재사용)
// ※ 추후 파일명을 PostgreSection -> LatestSection 등으로 변경하는 것을 권장합니다.
import StockPostgreSection from '../components/postgre/StockPostgreSection';
import ExchangePostgreSection from '../components/postgre/ExchangePostgreSection';
import GrainsPostgreSection from '../components/postgre/GrainsPostgreSection';
import CommoditiesPostgreSection from '../components/postgre/CommoditiesPostgreSection';
import CommoditiesIndexPostgreSection from '../components/postgre/CommoditiesIndexPostgreSection';

const MainPage: React.FC = () => {
  const [data, setData] = useState<MainPageResponseDto | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 초기 데이터 로딩
  useEffect(() => {
    fetchTodayInfo()
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  // 1. 환율 최신 30개 상태
  const [exchangeLatest, setExchangeLatest] = useState<any[] | null>(null);
  const [exchangeLoading, setExchangeLoading] = useState(false);
  const [exchangeError, setExchangeError] = useState<string | null>(null);
  const [showLatestExchange, setShowLatestExchange] = useState(false);

  const handleFetchExchangeLatest = async () => {
    setExchangeLoading(true);
    setExchangeError(null);
    try {
      const result = await fetchLatestExchange();
      setExchangeLatest(result);
      setShowLatestExchange(true);
    } catch (e: any) {
      setExchangeError(e.message);
    } finally {
      setExchangeLoading(false);
    }
  };

  // 2. 주식 최신 30개 상태
  const [stockLatest, setStockLatest] = useState<any[] | null>(null);
  const [stockLoading, setStockLoading] = useState(false);
  const [stockError, setStockError] = useState<string | null>(null);
  const [showLatestStock, setShowLatestStock] = useState(false);

  const handleFetchStockLatest = async () => {
    setStockLoading(true);
    setStockError(null);
    try {
      const result = await fetchLatestStock();
      setStockLatest(result);
      setShowLatestStock(true);
    } catch (e: any) {
      setStockError(e.message);
    } finally {
      setStockLoading(false);
    }
  };

  // 3. 곡물 최신 30개 상태
  const [grainsLatest, setGrainsLatest] = useState<any[] | null>(null);
  const [grainsLoading, setGrainsLoading] = useState(false);
  const [grainsError, setGrainsError] = useState<string | null>(null);
  const [showLatestGrains, setShowLatestGrains] = useState(false);

  const handleFetchGrainsLatest = async () => {
    setGrainsLoading(true);
    setGrainsError(null);
    try {
      const result = await fetchLatestGrains();
      setGrainsLatest(result);
      setShowLatestGrains(true);
    } catch (e: any) {
      setGrainsError(e.message);
    } finally {
      setGrainsLoading(false);
    }
  };

  // 4. 원자재 최신 30개 상태
  const [commoditiesLatest, setCommoditiesLatest] = useState<any[] | null>(null);
  const [commoditiesLoading, setCommoditiesLoading] = useState(false);
  const [commoditiesError, setCommoditiesError] = useState<string | null>(null);
  const [showLatestCommodities, setShowLatestCommodities] = useState(false);

  const handleFetchCommoditiesLatest = async () => {
    setCommoditiesLoading(true);
    setCommoditiesError(null);
    try {
      const result = await fetchLatestCommodities();
      setCommoditiesLatest(result);
      setShowLatestCommodities(true);
    } catch (e: any) {
      setCommoditiesError(e.message);
    } finally {
      setCommoditiesLoading(false);
    }
  };

  // 5. 지수 최신 30개 상태
  const [commoditiesIndexLatest, setCommoditiesIndexLatest] = useState<any[] | null>(null);
  const [commoditiesIndexLoading, setCommoditiesIndexLoading] = useState(false);
  const [commoditiesIndexError, setCommoditiesIndexError] = useState<string | null>(null);
  const [showLatestCommoditiesIndex, setShowLatestCommoditiesIndex] = useState(false);

  const handleFetchCommoditiesIndexLatest = async () => {
    setCommoditiesIndexLoading(true);
    setCommoditiesIndexError(null);
    try {
      const result = await fetchLatestCommoditiesIndex();
      setCommoditiesIndexLatest(result);
      setShowLatestCommoditiesIndex(true);
    } catch (e: any) {
      setCommoditiesIndexError(e.message);
    } finally {
      setCommoditiesIndexLoading(false);
    }
  };


  if (loading) return <div>로딩 중...</div>;
  if (error) return <div>에러: {error}</div>;
  if (!data) return <div>데이터 없음</div>;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', background: '#f7f7f7', minHeight: '100vh', padding: '32px 0' }}>
      <h1 style={{ marginBottom: 32 }}>최신 주요 지표</h1>

      {/* 1. 환율 섹션 */}
      <SectionContainer>
        {!showLatestExchange ? (
          <>
            <div style={{ marginBottom: 16 }}>
              <button onClick={handleFetchExchangeLatest} disabled={exchangeLoading}>
                {exchangeLoading ? '불러오는 중...' : '최신 환율(30일) 보기'}
              </button>
              {exchangeError && <span style={{ color: 'red', marginLeft: 8 }}>{exchangeError}</span>}
            </div>
            <ExchangeSection
              data={[...(data.usdList || []), ...(data.jpyList || []), ...(data.eurList || []), ...(data.cnyList || [])]}
            />
          </>
        ) : (
          <ExchangePostgreSection data={exchangeLatest || []} onBack={() => setShowLatestExchange(false)} />
        )}
      </SectionContainer>

      {/* 2. 주식 섹션 */}
      <SectionContainer>
        {!showLatestStock ? (
          <>
            <div style={{ marginBottom: 16 }}>
              <button onClick={handleFetchStockLatest} disabled={stockLoading}>
                {stockLoading ? '불러오는 중...' : '최신 주식(30일) 보기'}
              </button>
              {stockError && <span style={{ color: 'red', marginLeft: 8 }}>{stockError}</span>}
            </div>
            <StockSection data={[...(data.sp500List || []), ...(data.dowJonesList || []), ...(data.nasdaqList || []), ...(data.kospiList || []), ...(data.kosdaqList || [])]} />
          </>
        ) : (
          <StockPostgreSection data={stockLatest || []} onBack={() => setShowLatestStock(false)} />
        )}
      </SectionContainer>

      {/* 3. 곡물 섹션 */}
      <SectionContainer>
        {!showLatestGrains ? (
          <>
            <div style={{ marginBottom: 16 }}>
              <button onClick={handleFetchGrainsLatest} disabled={grainsLoading}>
                {grainsLoading ? '불러오는 중...' : '최신 곡물(30일) 보기'}
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
          <GrainsPostgreSection data={grainsLatest || []} onBack={() => setShowLatestGrains(false)} />
        )}
      </SectionContainer>

      {/* 4. 원자재 섹션 */}
      <SectionContainer>
        {!showLatestCommodities ? (
          <>
            <div style={{ marginBottom: 16 }}>
              <button onClick={handleFetchCommoditiesLatest} disabled={commoditiesLoading}>
                {commoditiesLoading ? '불러오는 중...' : '최신 원자재(30일) 보기'}
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
          <CommoditiesPostgreSection data={commoditiesLatest || []} onBack={() => setShowLatestCommodities(false)} />
        )}
      </SectionContainer>

      {/* 5. 지수 섹션 */}
      <SectionContainer>
        {!showLatestCommoditiesIndex ? (
          <>
            <div style={{ marginBottom: 16 }}>
              <button onClick={handleFetchCommoditiesIndexLatest} disabled={commoditiesIndexLoading}>
                {commoditiesIndexLoading ? '불러오는 중...' : '최신 지수(30일) 보기'}
              </button>
              {commoditiesIndexError && <span style={{ color: 'red', marginLeft: 8 }}>{commoditiesIndexError}</span>}
            </div>
            <CommoditiesIndexSection data={[...(data.dxyList || []), ...(data.vixList || [])]} />
          </>
        ) : (
          <CommoditiesIndexPostgreSection data={commoditiesIndexLatest || []} onBack={() => setShowLatestCommoditiesIndex(false)} />
        )}
      </SectionContainer>

      {/* 6. 심리 지수 (변경 없음) */}
      <SectionContainer>
        <MentalSection
          consumerSentimentList={data.consumerSentimentList || []}
          economicSentimentList={data.economicSentimentList || []}
          newsSentimentList={data.newsSentimentList || []}
        />
      </SectionContainer>

      {/* 7. 금리 섹션 (변경 없음) */}
      <SectionContainer>
        <InterestRateSection data={[...(data.korBaseRateList || []), ...(data.usFedRateList || [])]} />
      </SectionContainer>
    </div>
  );
};

export default MainPage;