package com.example.back.controller;

import com.example.back.entity.ExchangePrice;
import com.example.back.service.ExchangePriceService;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.Date;
import java.util.Date;
import org.springframework.format.annotation.DateTimeFormat;

@RestController
@RequestMapping("/api/exchange-price")
public class ExchangePriceController {
    private final ExchangePriceService service;

    public ExchangePriceController(ExchangePriceService service) {
        this.service = service;
    }

    @GetMapping
    public List<ExchangePrice> getAllPrices() {
        return service.getAllPrices();
    }

    // 기간별 환율 데이터 조회
    @GetMapping("/period")
    public List<ExchangePrice> getPricesByPeriod(
            @RequestParam("start") @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) Date start,
            @RequestParam("end") @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) Date end
    ) {
        return service.getPricesByPeriod(start, end);
    }
}
