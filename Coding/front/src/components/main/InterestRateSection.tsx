import React from 'react';
import { InterestRateDto } from '../../types/mainPageTypes';

interface Props {
  data: InterestRateDto;
}

const InterestRateSection: React.FC<Props> = ({ data }) => (
  <section>
    <h2>Interest Rate</h2>
    <ul>
      <li>한국 기준금리: {data.korBaseRate}</li>
      <li>미국 기준금리: {data.usFedRate}</li>
    </ul>
  </section>
);

export default InterestRateSection;
