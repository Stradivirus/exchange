package com.example.back.dto;

import lombok.*;
import java.time.LocalDate;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class DailyExchangeResponse {
    private LocalDate date;
    private Double dollar;
    private Double gold;
    private Double oil;
    private Double dxy;
    private Double baseRate;
    private Double usBaseRate;
}
