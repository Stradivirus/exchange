import React, { useEffect, useState } from 'react';
import { fetchLatestExchangePrice } from '../api/exchangePrice';

const ExchangePriceDashboard: React.FC = () => {
  const [latest, setLatest] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    fetchLatestExchangePrice()
      .then(latestData => {
        setLatest(latestData);
        setLoading(false);
      })
      .catch(() => {
        setError('데이터를 불러오지 못했습니다.');
        setLoading(false);
      });
  }, []);

  if (loading) return <div>로딩 중...</div>;
  if (error) return <div>{error}</div>;

  return (
    <div style={{ maxWidth: 700, margin: '32px auto', padding: 24 }}>
      <div style={{ padding: 24, border: '1px solid #ddd', borderRadius: 8, background: '#fafbfc', minWidth: 300 }}>
        <h2 style={{ margin: 0 }}>가장 최근 환율</h2>
        {latest && (
          <>
            <div><b>일시:</b> {new Date(latest.datetime).toLocaleString()}</div>
            <div><b>가격:</b> {latest.price.toLocaleString()} 원</div>
          </>
        )}
      </div>
    </div>
  );
};

export default ExchangePriceDashboard;
