import React from 'react';
import { StockDto } from '../../types/mainPageTypes';

interface Props {
  data: StockDto;
}

const StockSection: React.FC<Props> = ({ data }) => (
  <section>
    <h2>Stock</h2>
    <ul>
      <li>S&P500: {data.sp500?.toFixed(3)}</li>
      <li>Dow Jones: {data.dowJones?.toFixed(3)}</li>
      <li>NASDAQ: {data.nasdaq?.toFixed(3)}</li>
      <li>KOSPI: {data.kospi?.toFixed(3)}</li>
      <li>KOSDAQ: {data.kosdaq?.toFixed(3)}</li>
    </ul>
  </section>
);

export default StockSection;
