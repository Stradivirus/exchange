package com.example.back.mongo;

import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;
import java.util.Date;

@Document(collection = "KOSDAQ")
public class Kosdaq {
    @Id
    private String id;
    private Date date;
    private Double close;
    private Double open;
    private Double high;
    private Double low;
    private Double volume;
    private Double index_value;
    private Date created_at;

    public String getId() { return id; }
    public Date getDate() { return date; }
    public Double getClose() { return close; }
    public Double getOpen() { return open; }
    public Double getHigh() { return high; }
    public Double getLow() { return low; }
    public Double getVolume() { return volume; }
    public Double getIndex_value() { return index_value; }
    public Date getCreated_at() { return created_at; }
}
