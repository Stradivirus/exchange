package com.example.back.controller;

import com.example.back.entity.ExchangePrice;
import com.example.back.service.ExchangePriceService;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

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
}
