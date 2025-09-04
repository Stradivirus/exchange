package com.example.back.dto;

import lombok.*;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class MainPageResponseDto {
    private CommoditiesDto commodities;
    private CommoditiesIndexDto commoditiesIndex;
    private ExchangeDto exchange;
    private InterestRateDto interestRate;
    private StockDto stock;
}
