import React from 'react';

import { ExchangeDto } from '../../types/mainPageTypes';

interface Props {
  data: ExchangeDto[];
}

const formatDate = (dateStr: string) => dateStr ? dateStr.slice(0, 10) : '';

const ExchangeSection: React.FC<Props> = ({ data }) => {
  const usd = data[0];
  const jpy = data[1];
  const eur = data[2];
  const cny = data[3];
    if (!usd && !jpy && !eur && !cny) return <div>Exchange 데이터 없음</div>;
    const renderCurrency = (name: string, item: ExchangeDto | undefined) => (
      item ? (
        <li>
          <strong>{name}:</strong>
          <ul>
            <li>rate: {item.rate}</li>
            <li>단위 : {item.unit_name}</li>
            <li>date: {formatDate(item.date)}</li>
          </ul>
        </li>
      ) : null
    );
    return (
      <ul style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0' }}>
        {renderCurrency('USD', usd)}
        {renderCurrency('JPY', jpy)}
        {renderCurrency('EUR', eur)}
        {renderCurrency('CNY', cny)}
      </ul>
    );
};

export default ExchangeSection;
