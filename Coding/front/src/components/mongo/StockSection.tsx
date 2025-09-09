import React from 'react';

import { StockDto } from '../../types/mainPageTypes';

interface Props {
  data: StockDto[];
}

const formatNum = (n: any) => (typeof n === 'number' ? n.toFixed(2) : n);
const formatDate = (dateStr: string) => dateStr ? dateStr.slice(0, 10) : '';

// 공통 렌더링 함수
const renderStockItem = (label: string, item?: StockDto) => {
  if (!item) return null;
  return (
    <li>
      <strong>{label}:</strong>
      <ul>
        <li>close: {formatNum(item.close)}</li>
        <li>open: {formatNum(item.open)}</li>
        <li>high: {formatNum(item.high)}</li>
        <li>low: {formatNum(item.low)}</li>
        <li>volume: {item.volume}</li>
      </ul>
    </li>
  );
};

const StockSection: React.FC<Props> = ({ data }) => {
  const sp500 = data[0];
  const dow = data[1];
  const nasdaq = data[2];
  const kospi = data[3];
  const kosdaq = data[4];
  if (!sp500 && !dow && !nasdaq && !kospi && !kosdaq) return <div>Stock 데이터 없음</div>;

  // 가장 첫 번째 데이터의 날짜를 사용
  const date = sp500?.date || dow?.date || nasdaq?.date || kospi?.date || kosdaq?.date;
  const formattedDate = formatDate(date);

  return (
    <div>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '1rem'
      }}>
        <span style={{ fontWeight: 700, fontSize: '1.5rem' }}>Stock</span>
        <span style={{ fontWeight: 500 }}>{formattedDate}</span>
      </div>
      <ul style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0' }}>
        {renderStockItem('S&P500', sp500)}
        {renderStockItem('Dow Jones', dow)}
        {renderStockItem('NASDAQ', nasdaq)}
        {renderStockItem('KOSPI', kospi)}
        {renderStockItem('KOSDAQ', kosdaq)}
      </ul>
    </div>
  );
};

export default StockSection;
