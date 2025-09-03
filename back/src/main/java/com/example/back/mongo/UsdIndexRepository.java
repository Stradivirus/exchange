package com.example.back.mongo;

import org.springframework.data.mongodb.repository.MongoRepository;

public interface UsdIndexRepository extends MongoRepository<UsdIndex, String> {
    UsdIndex findTopByOrderByDateDesc();
}
