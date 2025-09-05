package com.example.back.mongo.stock;

import org.springframework.data.mongodb.repository.MongoRepository;

public interface KospiRepository extends MongoRepository<Kospi, String> {
    Kospi findTopByOrderByDateDesc();
}
