package com.example.back.mongo.commodities;

import org.springframework.data.mongodb.repository.MongoRepository;

public interface BrentOilRepository extends MongoRepository<BrentOil, String> {
    BrentOil findTopByOrderByDateDesc();
}
