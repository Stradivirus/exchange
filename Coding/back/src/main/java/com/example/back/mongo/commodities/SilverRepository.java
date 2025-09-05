package com.example.back.mongo.commodities;

import org.springframework.data.mongodb.repository.MongoRepository;

public interface SilverRepository extends MongoRepository<Silver, String> {
    Silver findTopByOrderByDateDesc();
}
