package com.example.back.mongo.interest;

import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;
import java.util.Date;

@Document(collection = "KOR_BASE_RATE")
public class KorBaseRate {
    @Id
    private String id;
    private Date date;
    private Double rate;
    private String type;
    private String country;
    private String source;

    public String getId() { return id; }
    public Date getDate() { return date; }
    public Double getRate() { return rate; }
    public String getType() { return type; }
    public String getCountry() { return country; }
    public String getSource() { return source; }
}
