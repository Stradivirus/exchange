package com.example.back.mongo;

import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;
import java.util.Date;

@Document(collection = "US_FED_RATE")
public class UsFedRate {
    @Id
    private String id;
    private Date date;
    private Double rate;
    private String type;
    private String country;
    private String source;
    private String series_id;
    private Date created_at;

    public String getId() { return id; }
    public Date getDate() { return date; }
    public Double getRate() { return rate; }
    public String getType() { return type; }
    public String getCountry() { return country; }
    public String getSource() { return source; }
    public String getSeries_id() { return series_id; }
    public Date getCreated_at() { return created_at; }
}
