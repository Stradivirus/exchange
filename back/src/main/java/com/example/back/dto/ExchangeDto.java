package com.example.back.dto;

import lombok.*;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class ExchangeDto {
    private String date;
    private Double usd;
    private Double jpy;
    private Double eur;
    private Double cny;
}
