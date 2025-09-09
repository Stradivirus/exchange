import React from 'react';

import { CommoditiesIndexDto } from '../../types/mainPageTypes';

interface Props {
  data: CommoditiesIndexDto[];
}

const formatNum = (n: any) => (typeof n === 'number' ? n.toFixed(2) : n);
const formatDate = (dateStr: string) => dateStr ? dateStr.slice(0, 10) : '';

// 공통 렌더링 함수
const renderIndexItem = (label: string, item?: CommoditiesIndexDto) => {
  if (!item) return null;
  return (
    <li>
      <strong>{label}:</strong>
      <ul>
        <li>close: {formatNum(item.close)}</li>
        <li>open: {formatNum(item.open)}</li>
        <li>high: {formatNum(item.high)}</li>
        <li>low: {formatNum(item.low)}</li>
      </ul>
    </li>
  );
};

const CommoditiesIndexSection: React.FC<Props> = ({ data }) => {
  const dxy = data[0];
  const vix = data[1];
  if (!dxy && !vix) return <div>Commodities Index 데이터 없음</div>;

  // 가장 먼저 데이터가 있는 인덱스의 날짜를 사용
  const firstDate = dxy?.date || vix?.date;
  const formattedDate = formatDate(firstDate);

  return (
    <div>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '1rem'
      }}>
        <span style={{ fontWeight: 700, fontSize: '1.5rem' }}>Commodities Index</span>
        <span style={{ fontWeight: 500 }}>{formattedDate}</span>
      </div>
      <ul style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0' }}>
        {renderIndexItem('DXY', dxy)}
        {renderIndexItem('VIX', vix)}
      </ul>
    </div>
  );
};

export default CommoditiesIndexSection;
