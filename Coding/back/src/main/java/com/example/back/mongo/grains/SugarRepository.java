package com.example.back.mongo.grains;

import org.springframework.data.mongodb.repository.MongoRepository;

public interface SugarRepository extends MongoRepository<Sugar, String> {
    Sugar findTopByOrderByDateDesc();
}
