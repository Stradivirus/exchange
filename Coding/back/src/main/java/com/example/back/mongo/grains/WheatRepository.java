package com.example.back.mongo.grains;

import org.springframework.data.mongodb.repository.MongoRepository;

public interface WheatRepository extends MongoRepository<Wheat, String> {
    Wheat findTopByOrderByDateDesc();
}
