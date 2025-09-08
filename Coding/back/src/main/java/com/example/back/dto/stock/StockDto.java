package com.example.back.dto.stock;

import lombok.Builder;
import lombok.Data;
import java.sql.Date;

@Data
@Builder
public class StockDto {
    private Date date;
    private Double sp500;
    private Double sp500Volume;
    private Double dowJones;
    private Double dowJonesVolume;
    private Double nasdaq;
    private Double nasdaqVolume;
    private Double kospi;
    private Double kospiVolume;
    private Double kosdaq;
    private Double kosdaqVolume;
}
