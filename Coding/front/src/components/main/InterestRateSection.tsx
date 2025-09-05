import React from 'react';

import { InterestRateDto } from '../../types/mainPageTypes';

interface Props {
  data: InterestRateDto[];
}


const formatDate = (dateStr: string) => dateStr ? dateStr.slice(0, 10) : '';

const InterestRateSection: React.FC<Props> = ({ data }) => {
  const kor = data[0];
  const us = data[1];
  if (!kor && !us) return <div>Interest Rate 데이터 없음</div>;
  return (
    <ul style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0' }}>
      {kor && (
        <li>
          <strong>한국 기준금리:</strong>
          <ul>
            <li>rate: {kor.rate}</li>
            <li>date: {formatDate(kor.date)}</li>
          </ul>
        </li>
      )}
      {us && (
        <li>
          <strong>미국 기준금리:</strong>
          <ul>
            <li>rate: {us.rate}</li>
            <li>date: {formatDate(us.date)}</li>
          </ul>
        </li>
      )}
    </ul>
  );

}
export default InterestRateSection;
