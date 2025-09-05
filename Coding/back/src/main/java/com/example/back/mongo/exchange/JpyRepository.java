package com.example.back.mongo.exchange;

import org.springframework.data.mongodb.repository.MongoRepository;

public interface JpyRepository extends MongoRepository<Jpy, String> {
    Jpy findTopByOrderByDateDesc();
}
