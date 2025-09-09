package com.example.back.dto.mental;

import java.util.Date;

public class ConsumerSentimentDto {
    private Date date;
    private String statCode;
    private String itemCode;
    private String itemName;
    private String unitName;
    private Double value;
    private Date createdAt;
    private String regionCode;
    private String regionName;

    public Date getDate() { return date; }
    public void setDate(Date date) { this.date = date; }
    public String getStatCode() { return statCode; }
    public void setStatCode(String statCode) { this.statCode = statCode; }
    public String getItemCode() { return itemCode; }
    public void setItemCode(String itemCode) { this.itemCode = itemCode; }
    public String getItemName() { return itemName; }
    public void setItemName(String itemName) { this.itemName = itemName; }
    public String getUnitName() { return unitName; }
    public void setUnitName(String unitName) { this.unitName = unitName; }
    public Double getValue() { return value; }
    public void setValue(Double value) { this.value = value; }
    public Date getCreatedAt() { return createdAt; }
    public void setCreatedAt(Date createdAt) { this.createdAt = createdAt; }
    public String getRegionCode() { return regionCode; }
    public void setRegionCode(String regionCode) { this.regionCode = regionCode; }
    public String getRegionName() { return regionName; }
    public void setRegionName(String regionName) { this.regionName = regionName; }
}
