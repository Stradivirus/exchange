package com.example.back.service;

import com.example.back.entity.ExchangePrice;
import com.example.back.repository.ExchangePriceRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.mongodb.core.MongoTemplate;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class ExchangePriceService {
    private final ExchangePriceRepository repository;

    @Autowired
    private MongoTemplate mongoTemplate;

    public ExchangePriceService(ExchangePriceRepository repository) {
        this.repository = repository;
    }

    public List<ExchangePrice> getAllPrices() {
        return repository.findAll();
    }

}
