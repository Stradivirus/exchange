package com.example.back.dto.interest;

import lombok.Builder;
import lombok.Getter;
import java.util.Date;

@Getter
@Builder
public class UsFedRateDto {
    private Date date;
    private Double rate;
    private Date created_at;
}
