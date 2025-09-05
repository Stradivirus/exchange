package com.example.back.mongo.stock;

import org.springframework.data.mongodb.repository.MongoRepository;

public interface Sp500Repository extends MongoRepository<Sp500, String> {
    Sp500 findTopByOrderByDateDesc();
}
