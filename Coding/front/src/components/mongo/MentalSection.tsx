import React from 'react';
import { ConsumerSentimentDto, EconomicSentimentDto, NewsSentimentDto } from '../../types/mainPageTypes';

interface Props {
  consumerSentimentList: ConsumerSentimentDto[];
  economicSentimentList: EconomicSentimentDto[];
  newsSentimentList: NewsSentimentDto[];
}

const formatNum = (n: any) => (typeof n === 'number' ? n.toFixed(2) : n);
const formatDate = (dateStr: string) => dateStr ? dateStr.slice(0, 10) : '';

const renderSentiment = (label: string, item: any, extra?: React.ReactNode) => (
  <li>
    <strong>{label}:</strong>
    {item ? (
      <ul>
        <li>value: {formatNum(item.value)}</li>
        <li>date: {formatDate(item.date)}</li>
        {extra}
      </ul>
    ) : ' -'}
  </li>
);

const MentalSection: React.FC<Props> = ({ consumerSentimentList, economicSentimentList, newsSentimentList }) => {
  const consumer = consumerSentimentList?.[0];
  const economic = economicSentimentList?.[0];
  const news = newsSentimentList?.[0];
  const formattedDate = formatDate(consumer?.date || economic?.date || news?.date);

  return (
    <div>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '1rem'
      }}>
        <span style={{ fontWeight: 700, fontSize: '1.5rem' }}>심리지수</span>
        <span style={{ fontWeight: 500 }}>{formattedDate}</span>
      </div>
      <ul style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0' }}>
        {renderSentiment('소비자심리지수', consumer, consumer?.regionName && <li>region: {consumer.regionName}</li>)}
        {renderSentiment('경제심리지수', economic)}
        {renderSentiment('뉴스심리지수', news)}
      </ul>
    </div>
  );
};

export default MentalSection;
