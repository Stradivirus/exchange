package com.example.back.mongo.commodities;

import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;
import java.util.Date;

@Document(collection = "SILVER")
public class Silver {
    @Id
    private String id;
    private Date date;
    private Double close;
    private Double open;
    private Double high;
    private Double low;
    private Double volume;
    private Double price;
    private Date created_at;

    public String getId() { return id; }
    public Date getDate() { return date; }
    public Double getClose() { return close; }
    public Double getOpen() { return open; }
    public Double getHigh() { return high; }
    public Double getLow() { return low; }
    public Double getVolume() { return volume; }
    public Double getPrice() { return price; }
    public Date getCreated_at() { return created_at; }
}
