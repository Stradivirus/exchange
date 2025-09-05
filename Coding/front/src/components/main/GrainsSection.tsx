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
        <li>price: {formatNum(items[0].price)}</li>
        <li>date: {formatDate(items[0].date)}</li>
      </ul>
    )}
  </li>
);

const GrainsSection: React.FC<Props> = ({ rice, wheat, corn, coffee, sugar }) => (
  <section>
  <ul style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0' }}>
      {renderGrain('Rice', rice)}
      {renderGrain('Wheat', wheat)}
      {renderGrain('Corn', corn)}
      {renderGrain('Coffee', coffee)}
      {renderGrain('Sugar', sugar)}
    </ul>
  </section>
);

export default GrainsSection;
