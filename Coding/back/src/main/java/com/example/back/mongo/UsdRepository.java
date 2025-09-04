package com.example.back.mongo;

import org.springframework.data.mongodb.repository.MongoRepository;

public interface UsdRepository extends MongoRepository<Usd, String> {
    Usd findTopByOrderByDateDesc();
}
