import React from 'react';
import { CommoditiesIndexDto } from '../../types/mainPageTypes';

interface Props {
  data: CommoditiesIndexDto;
}

const CommoditiesIndexSection: React.FC<Props> = ({ data }) => (
  <section>
    <h2>Commodities Index</h2>
    <ul>
      <li>DXY: {data.dxy}</li>
      <li>USD Index: {data.usdIndex}</li>
      <li>VIX: {data.vix}</li>
    </ul>
  </section>
);

export default CommoditiesIndexSection;
