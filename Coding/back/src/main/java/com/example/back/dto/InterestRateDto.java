package com.example.back.dto;

import lombok.*;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class InterestRateDto {
    private String date;
    private Double korBaseRate;
    private Double usFedRate;
}
