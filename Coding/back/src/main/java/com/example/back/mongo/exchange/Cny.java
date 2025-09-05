package com.example.back.mongo.exchange;

import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;
import java.util.Date;

@Document(collection = "CNY")
public class Cny {
    @Id
    private String id;
    private Date date;
    private Double rate;
    private String currency_code;
    private String unit_name;

    public String getId() { return id; }
    public Date getDate() { return date; }
    public Double getRate() { return rate; }
    public String getCurrency_code() { return currency_code; }
    public String getUnit_name() { return unit_name; }
}
