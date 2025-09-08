package com.example.back.dto.commodities_index;

import lombok.Builder;
import lombok.Data;
import java.sql.Date;

@Data
@Builder
public class CommoditiesIndexDto {
    private Date date;
    private Double dxy;
    private Double vix;
}
