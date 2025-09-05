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

  // 가장 첫 번째 데이터의 날짜를 사용 (예시)
  const date = usd?.date || jpy?.date || eur?.date || cny?.date;
  const formattedDate = formatDate(date);

  const renderCurrency = (name: string, item: ExchangeDto | undefined) => (
    item ? (
      <li>
        <strong>{name}:</strong>
        <ul>
          <li>rate: {item.rate}</li>
        </ul>
      </li>
    ) : null
  );

  // 단위 문자열 만들기 (존재하는 통화의 단위만 표시)
  const unitNames = [usd, jpy, eur, cny]
    .filter(item => item && item.unit_name)
    .map(item => item.unit_name)
    .filter((v, i, arr) => arr.indexOf(v) === i) // 중복 제거
    .join(', ');

  return (
    <div>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '1rem'
      }}>
        <span style={{ fontWeight: 700, fontSize: '1.5rem' }}>Exchange</span>
        <span style={{ fontWeight: 500 }}>
          {unitNames && (
            <span style={{ marginLeft: 8, fontWeight: 400, fontSize: '1rem', color: '#888' }}>
              단위 : {unitNames}
            </span>
          )}
          <span style={{ marginLeft: '2em' }}>{formattedDate}</span>
        </span>
      </div>
      <ul style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0' }}>
        {renderCurrency('USD', usd)}
        {renderCurrency('JPY', jpy)}
        {renderCurrency('EUR', eur)}
        {renderCurrency('CNY', cny)}
      </ul>
    </div>
  );
};

export default ExchangeSection;
