import React from 'react';

import { InterestRateDto } from '../../types/mainPageTypes';

interface Props {
  data: InterestRateDto[];
}

const formatDate = (dateStr: string) => dateStr ? dateStr.slice(0, 10) : '';

// 공통 렌더링 함수
const renderRateItem = (label: string, item?: InterestRateDto) => {
  if (!item) return null;
  return (
    <li>
      <strong>{label}:</strong>
      <ul>
        <li>rate: {item.rate}</li>
        <li>date: {formatDate(item.date)}</li>
      </ul>
    </li>
  );
};

const InterestRateSection: React.FC<Props> = ({ data }) => {
  const kor = data[0];
  const us = data[1];
  if (!kor && !us) return <div>Interest Rate 데이터 없음</div>;

  // 상단에는 제목만 표시, 각 항목별로 변경일(date) 표시
  return (
    <div>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '1rem'
      }}>
        <span style={{ fontWeight: 700, fontSize: '1.5rem' }}>Interest Rate</span>
      </div>
      <ul style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0' }}>
        {renderRateItem('한국 기준금리', kor)}
        {renderRateItem('미국 기준금리', us)}
      </ul>
    </div>
  );
}

export default InterestRateSection;
