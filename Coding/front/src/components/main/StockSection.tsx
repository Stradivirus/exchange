import React from 'react';

import { StockDto } from '../../types/mainPageTypes';

interface Props {
  data: StockDto[];
}


const formatNum = (n: any) => (typeof n === 'number' ? n.toFixed(2) : n);
const formatDate = (dateStr: string) => dateStr ? dateStr.slice(0, 10) : '';

const StockSection: React.FC<Props> = ({ data }) => {
  const sp500 = data[0];
  const dow = data[1];
  const nasdaq = data[2];
  const kospi = data[3];
  const kosdaq = data[4];
  if (!sp500 && !dow && !nasdaq && !kospi && !kosdaq) return <div>Stock 데이터 없음</div>;
  return (
    <ul style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0' }}>
      {sp500 && (
        <li>
          <strong>S&P500:</strong>
          <ul>
            <li>close: {formatNum(sp500.close)}</li>
            <li>open: {formatNum(sp500.open)}</li>
            <li>high: {formatNum(sp500.high)}</li>
            <li>low: {formatNum(sp500.low)}</li>
            <li>volume: {sp500.volume}</li>
            <li>date: {formatDate(sp500.date)}</li>
          </ul>
        </li>
      )}
      {dow && (
        <li>
          <strong>Dow Jones:</strong>
          <ul>
            <li>close: {formatNum(dow.close)}</li>
            <li>open: {formatNum(dow.open)}</li>
            <li>high: {formatNum(dow.high)}</li>
            <li>low: {formatNum(dow.low)}</li>
            <li>volume: {dow.volume}</li>
            <li>date: {formatDate(dow.date)}</li>
          </ul>
        </li>
      )}
      {nasdaq && (
        <li>
          <strong>NASDAQ:</strong>
          <ul>
            <li>close: {formatNum(nasdaq.close)}</li>
            <li>open: {formatNum(nasdaq.open)}</li>
            <li>high: {formatNum(nasdaq.high)}</li>
            <li>low: {formatNum(nasdaq.low)}</li>
            <li>volume: {nasdaq.volume}</li>
            <li>date: {formatDate(nasdaq.date)}</li>
          </ul>
        </li>
      )}
      {kospi && (
        <li>
          <strong>KOSPI:</strong>
          <ul>
            <li>close: {formatNum(kospi.close)}</li>
            <li>open: {formatNum(kospi.open)}</li>
            <li>high: {formatNum(kospi.high)}</li>
            <li>low: {formatNum(kospi.low)}</li>
            <li>volume: {kospi.volume}</li>
            <li>date: {formatDate(kospi.date)}</li>
          </ul>
        </li>
      )}
      {kosdaq && (
        <li>
          <strong>KOSDAQ:</strong>
          <ul>
            <li>close: {formatNum(kosdaq.close)}</li>
            <li>open: {formatNum(kosdaq.open)}</li>
            <li>high: {formatNum(kosdaq.high)}</li>
            <li>low: {formatNum(kosdaq.low)}</li>
            <li>volume: {kosdaq.volume}</li>
            <li>date: {formatDate(kosdaq.date)}</li>
          </ul>
        </li>
      )}
    </ul>
  );
};

export default StockSection;
