package com.example.back.mongo.mental;

import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;
import java.util.Date;

@Document(collection = "news_sentiment")
public class NewsSentiment {
    @Id
    private String id;
    private Date date;
    private String statCode;
    private String itemCode;
    private String itemName;
    private String unitName;
    private Double value;

    public String getId() { return id; }
    public Date getDate() { return date; }
    public String getStatCode() { return statCode; }
    public String getItemCode() { return itemCode; }
    public String getItemName() { return itemName; }
    public String getUnitName() { return unitName; }
    public Double getValue() { return value; }
}
