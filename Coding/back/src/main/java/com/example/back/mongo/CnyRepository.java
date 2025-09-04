package com.example.back.mongo;

import org.springframework.data.mongodb.repository.MongoRepository;

public interface CnyRepository extends MongoRepository<Cny, String> {
    Cny findTopByOrderByDateDesc();
}
