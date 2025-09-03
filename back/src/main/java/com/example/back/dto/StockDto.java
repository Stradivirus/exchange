package com.example.back.dto;

import lombok.*;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class StockDto {
    private String date;
    private Double sp500;
    private Double dowJones;
    private Double nasdaq;
    private Double kospi;
    private Double kosdaq;
}
