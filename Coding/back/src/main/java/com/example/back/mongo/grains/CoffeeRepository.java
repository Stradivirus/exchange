package com.example.back.mongo.grains;

import org.springframework.data.mongodb.repository.MongoRepository;

public interface CoffeeRepository extends MongoRepository<Coffee, String> {
    Coffee findTopByOrderByDateDesc();
}
