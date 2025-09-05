import React from 'react';

import { CommoditiesIndexDto } from '../../types/mainPageTypes';

interface Props {
  data: CommoditiesIndexDto[];
}


const formatNum = (n: any) => (typeof n === 'number' ? n.toFixed(2) : n);
const formatDate = (dateStr: string) => dateStr ? dateStr.slice(0, 10) : '';

const CommoditiesIndexSection: React.FC<Props> = ({ data }) => {
  const dxy = data[0];
  const vix = data[1];
  if (!dxy && !vix) return <div>Commodities Index 데이터 없음</div>;
  return (
    <ul style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0' }}>
      {dxy && (
        <li>
          <strong>DXY:</strong>
          <ul>
            <li>close: {formatNum(dxy.close)}</li>
            <li>open: {formatNum(dxy.open)}</li>
            <li>high: {formatNum(dxy.high)}</li>
            <li>low: {formatNum(dxy.low)}</li>
            <li>volume: {dxy.volume}</li>
            <li>price: {formatNum(dxy.price)}</li>
            <li>date: {formatDate(dxy.date)}</li>
          </ul>
        </li>
      )}
      {vix && (
        <li>
          <strong>VIX:</strong>
          <ul>
            <li>close: {formatNum(vix.close)}</li>
            <li>open: {formatNum(vix.open)}</li>
            <li>high: {formatNum(vix.high)}</li>
            <li>low: {formatNum(vix.low)}</li>
            <li>volume: {vix.volume}</li>
            <li>price: {formatNum(vix.price)}</li>
            <li>date: {formatDate(vix.date)}</li>
          </ul>
        </li>
      )}
    </ul>
  );
};

export default CommoditiesIndexSection;
