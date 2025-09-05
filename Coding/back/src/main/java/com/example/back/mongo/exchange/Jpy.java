package com.example.back.mongo.exchange;

import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;
import java.util.Date;

@Document(collection = "JPY")
public class Jpy {
    @Id
    private String id;
    private Date date;
    private Double rate;
    private String unit_name;

    public String getId() { return id; }
    public Date getDate() { return date; }
    public Double getRate() { return rate; }
    public String getUnit_name() { return unit_name; }
}
