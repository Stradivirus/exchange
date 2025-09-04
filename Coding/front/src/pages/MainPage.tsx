import React, { useEffect, useState } from 'react';
import { MainPageResponseDto } from '../types/mainPageTypes';
import { fetchTodayInfo } from '../api/mainPageApi';
import CommoditiesSection from '../components/main/CommoditiesSection';
import CommoditiesIndexSection from '../components/main/CommoditiesIndexSection';
import ExchangeSection from '../components/main/ExchangeSection';
import InterestRateSection from '../components/main/InterestRateSection';
import StockSection from '../components/main/StockSection';

const MainPage: React.FC = () => {
  const [data, setData] = useState<MainPageResponseDto | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchTodayInfo()
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div>로딩 중...</div>;
  if (error) return <div>에러: {error}</div>;
  if (!data) return <div>데이터 없음</div>;

  return (
    <div>
      <h1>최신 주요 지표</h1>
      {data.exchange ? <ExchangeSection data={data.exchange} /> : <div>Exchange 데이터 없음</div>}
      {data.stock ? <StockSection data={data.stock} /> : <div>Stock 데이터 없음</div>}
      {data.commodities ? <CommoditiesSection data={data.commodities} /> : <div>Commodities 데이터 없음</div>}
      {data.commoditiesIndex ? <CommoditiesIndexSection data={data.commoditiesIndex} /> : <div>Commodities Index 데이터 없음</div>}
      {data.interestRate ? <InterestRateSection data={data.interestRate} /> : <div>Interest Rate 데이터 없음</div>}
    </div>
  );
};

export default MainPage;
