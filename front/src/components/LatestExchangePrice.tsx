import React, { useEffect, useState } from 'react';
import { fetchLatestExchangePrice } from '../api/exchangePrice';

interface ExchangePrice {
  id: string;
  datetime: string;
  price: number;
}

const LatestExchangePrice: React.FC = () => {
  const [latest, setLatest] = useState<ExchangePrice | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchLatestExchangePrice()
      .then((data) => {
        setLatest(data);
        setLoading(false);
      })
      .catch((err) => {
        setError('데이터를 불러오지 못했습니다.');
        setLoading(false);
      });
  }, []);

  if (loading) return <div>로딩 중...</div>;
  if (error) return <div>{error}</div>;
  if (!latest) return <div>환율 데이터가 없습니다.</div>;

  return (
    <div style={{ padding: 24, border: '1px solid #ddd', borderRadius: 8, maxWidth: 400, margin: '32px auto', background: '#fafbfc' }}>
      <h2>가장 최근 환율</h2>
      <div><b>일시:</b> {new Date(latest.datetime).toLocaleString()}</div>
      <div><b>가격:</b> {latest.price.toLocaleString()} 원</div>
    </div>
  );
};

export default LatestExchangePrice;
