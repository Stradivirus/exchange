import React from 'react';
// grains DTO 타입 import 필요 (RiceDto 등)

interface Props {
  rice: any[];
  wheat: any[];
  corn: any[];
  coffee: any[];
  sugar: any[];
}

const formatNum = (n: any) => (typeof n === 'number' ? n.toFixed(2) : n);
const formatDate = (dateStr: string) => dateStr ? dateStr.slice(0, 10) : '';

const renderGrain = (name: string, items: any[]) => (
  <li style={{ marginBottom: 16 }}>
    <strong>{name}:</strong>
    {items.length === 0 ? ' -' : (
      <ul style={{ marginLeft: 12 }}>
        <li>close: {formatNum(items[0].close)}</li>
        <li>open: {formatNum(items[0].open)}</li>
        <li>high: {formatNum(items[0].high)}</li>
        <li>low: {formatNum(items[0].low)}</li>
        <li>volume: {items[0].volume}</li>
      </ul>
    )}
  </li>
);

const GrainsSection: React.FC<Props> = ({ rice, wheat, corn, coffee, sugar }) => {
  // 가장 먼저 데이터가 있는 곡물의 날짜를 사용
  const firstDate =
    rice[0]?.date ||
    wheat[0]?.date ||
    corn[0]?.date ||
    coffee[0]?.date ||
    sugar[0]?.date;
  const formattedDate = formatDate(firstDate);

  return (
    <section>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '1rem'
      }}>
        <span style={{ fontWeight: 700, fontSize: '1.5rem' }}>Grains</span>
        <span style={{ fontWeight: 500 }}>{formattedDate}</span>
      </div>
      <ul style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0' }}>
        {renderGrain('Rice', rice)}
        {renderGrain('Wheat', wheat)}
        {renderGrain('Corn', corn)}
        {renderGrain('Coffee', coffee)}
        {renderGrain('Sugar', sugar)}
      </ul>
    </section>
  );
};

export default GrainsSection;
