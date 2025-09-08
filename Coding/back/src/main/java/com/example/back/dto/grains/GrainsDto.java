package com.example.back.dto.grains;

import lombok.Builder;
import lombok.Data;
import java.sql.Date;

@Data
@Builder
public class GrainsDto {
    private Date date;
    private Double corn;
    private Double cornVolume;
    private Double wheat;
    private Double wheatVolume;
    private Double rice;
    private Double riceVolume;
    private Double coffee;
    private Double coffeeVolume;
    private Double sugar;
    private Double sugarVolume;
}
