package com.example.back.mongo.commodities;

import org.springframework.data.mongodb.repository.MongoRepository;

public interface CrudeOilRepository extends MongoRepository<CrudeOil, String> {
    CrudeOil findTopByOrderByDateDesc();
}
