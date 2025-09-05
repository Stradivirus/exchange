package com.example.back.mongo.interest;

import org.springframework.data.mongodb.repository.MongoRepository;

public interface UsFedRateRepository extends MongoRepository<UsFedRate, String> {
    UsFedRate findTopByOrderByDateDesc();
}
