package com.example.back.dto.exchange;

import lombok.Builder;
import lombok.Getter;
import java.util.Date;

@Getter
@Builder
public class EurDto {
    private Date date;
    private Double rate;
    private String currency_code;
    private String unit_name;
    private Date created_at;
}
