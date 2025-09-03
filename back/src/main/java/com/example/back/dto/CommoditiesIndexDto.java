package com.example.back.dto;

import lombok.*;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class CommoditiesIndexDto {
    private String date;
    private Double dxy;
    private Double usdIndex;
    private Double vix;
}
