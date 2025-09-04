package com.example.back.mongo;

import org.springframework.data.mongodb.repository.MongoRepository;

public interface CrudeOilRepository extends MongoRepository<CrudeOil, String> {
    CrudeOil findTopByOrderByDateDesc();
}
