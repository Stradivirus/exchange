import React from 'react';
import { CommoditiesDto } from '../../types/mainPageTypes';

interface Props {
  data: CommoditiesDto;
}

const CommoditiesSection: React.FC<Props> = ({ data }) => (
  <section>
    <h2>Commodities</h2>
    <ul>
      <li>Gold: {data.gold?.toFixed(3)}</li>
      <li>Silver: {data.silver?.toFixed(3)}</li>
      <li>Copper: {data.copper?.toFixed(3)}</li>
      <li>Crude Oil: {data.crudeOil?.toFixed(3)}</li>
      <li>Brent Oil: {data.brentOil?.toFixed(3)}</li>
    </ul>
  </section>
);

export default CommoditiesSection;
