import React from 'react';
import { ExchangeDto } from '../../types/mainPageTypes';

interface Props {
  data: ExchangeDto;
}

const ExchangeSection: React.FC<Props> = ({ data }) => (
  <section>
    <h2>Exchange</h2>
    <ul>
      <li>USD: {data.usd?.toFixed(3)}</li>
      <li>JPY: {data.jpy?.toFixed(3)}</li>
      <li>EUR: {data.eur?.toFixed(3)}</li>
      <li>CNY: {data.cny?.toFixed(3)}</li>
    </ul>
  </section>
);

export default ExchangeSection;
