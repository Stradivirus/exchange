import React from 'react';


// import { GoldDto } from '../../types/mainPageTypes';

interface Props {
  data: {
    goldList: any[];
    silverList: any[];
    copperList: any[];
    crudeOilList: any[];
    brentOilList: any[];
  };
}

const formatNum = (n: any) => (typeof n === 'number' ? n.toFixed(2) : n);
const formatDate = (dateStr: string) => dateStr ? dateStr.slice(0, 10) : '';

const renderCommodity = (name: string, items: any[]) => (
  <li>
    <strong>{name}:</strong>
    {items.length === 0 ? ' -' : (
      <ul>
        <li>close: {formatNum(items[0].close)}</li>
        <li>open: {formatNum(items[0].open)}</li>
        <li>high: {formatNum(items[0].high)}</li>
        <li>low: {formatNum(items[0].low)}</li>
        <li>volume: {items[0].volume}</li>
      </ul>
    )}
  </li>
);

const CommoditiesSection: React.FC<Props> = ({ data }) => {
  // 가장 먼저 데이터가 있는 상품의 날짜를 사용
  const firstDate =
    data.goldList[0]?.date ||
    data.silverList[0]?.date ||
    data.copperList[0]?.date ||
    data.crudeOilList[0]?.date ||
    data.brentOilList[0]?.date;
  const formattedDate = formatDate(firstDate);

  return (
    <div>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '1rem'
      }}>
        <span style={{ fontWeight: 700, fontSize: '1.5rem' }}>Commodities</span>
        <span style={{ fontWeight: 500 }}>{formattedDate}</span>
      </div>
      <ul style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0' }}>
        {renderCommodity('Gold', data.goldList)}
        {renderCommodity('Silver', data.silverList)}
        {renderCommodity('Copper', data.copperList)}
        {renderCommodity('Crude Oil', data.crudeOilList)}
        {renderCommodity('Brent Oil', data.brentOilList)}
      </ul>
    </div>
  );
};

export default CommoditiesSection;
