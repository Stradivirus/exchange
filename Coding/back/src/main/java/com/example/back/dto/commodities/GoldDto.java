package com.example.back.dto.commodities;

import lombok.Builder;
import lombok.Getter;
import java.util.Date;

@Getter
@Builder
public class GoldDto {
    private Date date;
    private Double close;
    private Double open;
    private Double high;
    private Double low;
    private Double volume;
    private Double price;
    private Date created_at;
}
