package com.example.back.mongo.interest;

import org.springframework.data.mongodb.repository.MongoRepository;

public interface KorBaseRateRepository extends MongoRepository<KorBaseRate, String> {
    KorBaseRate findTopByOrderByDateDesc();
}
