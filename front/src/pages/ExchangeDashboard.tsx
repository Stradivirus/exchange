import React from 'react';
import ExchangePriceChart from '../components/ExchangePriceChart';

const ExchangeDashboard: React.FC = () => {
  return (
    <div className="App" style={{ background: '#f5f7fa', minHeight: '100vh', paddingBottom: 40 }}>
      <h1 style={{ textAlign: 'center', margin: '32px 0 0 0', fontWeight: 700 }}>환율 대시보드</h1>
  <ExchangePriceChart />
    </div>
  );
};

export default ExchangeDashboard;
