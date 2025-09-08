package com.example.back.dto.commodities;

import lombok.Builder;
import lombok.Data;
import java.sql.Date;

@Data
@Builder
public class CommoditiesDto {
    private Date date;
    private Double gold;
    private Double goldVolume;
    private Double silver;
    private Double silverVolume;
    private Double copper;
    private Double copperVolume;
    private Double crudeOil;
    private Double crudeOilVolume;
    private Double brentOil;
    private Double brentOilVolume;
}
