package com.example.back.dto.exchange;

import lombok.Builder;
import lombok.Getter;

import java.time.LocalDate;

@Getter
@Builder
public class ExchangeDto {
    private LocalDate date;
    private Double usd;
    private Double jpy;
    private Double eur;
    private Double cny;
}