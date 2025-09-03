import React from 'react';
import { CommoditiesIndexDto } from '../../types/mainPageTypes';

interface Props {
  data: CommoditiesIndexDto;
}

const CommoditiesIndexSection: React.FC<Props> = ({ data }) => (
  <section>
    <h2>Commodities Index</h2>
    <ul>
      <li>DXY: {data.dxy?.toFixed(3)}</li>
      <li>USD Index: {data.usdIndex?.toFixed(3)}</li>
      <li>VIX: {data.vix?.toFixed(3)}</li>
    </ul>
  </section>
);

export default CommoditiesIndexSection;
