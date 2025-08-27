package com.example.back.dto;

import com.example.back.entity.ExchangePrice;
import java.util.List;

public class ExchangePricePeriodResponse {
    private List<ExchangePrice> prices;
    private double maxPrice;
    private String maxDate;
    private double minPrice;
    private String minDate;

    public ExchangePricePeriodResponse(List<ExchangePrice> prices, double maxPrice, String maxDate, double minPrice, String minDate) {
        this.prices = prices;
        this.maxPrice = maxPrice;
        this.maxDate = maxDate;
        this.minPrice = minPrice;
        this.minDate = minDate;
    }

    public List<ExchangePrice> getPrices() {
        return prices;
    }
    public double getMaxPrice() {
        return maxPrice;
    }
    public String getMaxDate() {
        return maxDate;
    }
    public double getMinPrice() {
        return minPrice;
    }
    public String getMinDate() {
        return minDate;
    }
}
