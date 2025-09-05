package com.example.back.mongo.grains;

import org.springframework.data.mongodb.repository.MongoRepository;

public interface RiceRepository extends MongoRepository<Rice, String> {
    Rice findTopByOrderByDateDesc();
}
