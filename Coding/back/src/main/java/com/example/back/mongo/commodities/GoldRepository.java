package com.example.back.mongo.commodities;

import org.springframework.data.mongodb.repository.MongoRepository;

public interface GoldRepository extends MongoRepository<Gold, String> {
    Gold findTopByOrderByDateDesc();
}
