package com.example.back.mongo.exchange;

import org.springframework.data.mongodb.repository.MongoRepository;

public interface CnyRepository extends MongoRepository<Cny, String> {
    Cny findTopByOrderByDateDesc();
}
