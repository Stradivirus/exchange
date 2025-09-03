import React from 'react';
import { ExchangeDto } from '../../types/mainPageTypes';

interface Props {
  data: ExchangeDto;
}

const ExchangeSection: React.FC<Props> = ({ data }) => (
  <section>
    <h2>Exchange</h2>
    <ul>
      <li>USD: {data.usd}</li>
      <li>JPY: {data.jpy}</li>
      <li>EUR: {data.eur}</li>
      <li>CNY: {data.cny}</li>
    </ul>
  </section>
);

export default ExchangeSection;
