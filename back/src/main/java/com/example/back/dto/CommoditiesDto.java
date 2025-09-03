package com.example.back.dto;

import lombok.*;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class CommoditiesDto {
    private String date;
    private Double gold;
    private Double silver;
    private Double copper;
    private Double crudeOil;
    private Double brentOil;
}
