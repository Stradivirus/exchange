package com.example.back.mongo.stock;

import org.springframework.data.mongodb.repository.MongoRepository;

public interface NasdaqRepository extends MongoRepository<Nasdaq, String> {
    Nasdaq findTopByOrderByDateDesc();
}
