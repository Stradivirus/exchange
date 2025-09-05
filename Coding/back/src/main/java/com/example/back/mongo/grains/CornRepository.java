package com.example.back.mongo.grains;

import org.springframework.data.mongodb.repository.MongoRepository;

public interface CornRepository extends MongoRepository<Corn, String> {
    Corn findTopByOrderByDateDesc();
}
