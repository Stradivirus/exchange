package com.example.back.mongo.exchange;

import org.springframework.data.mongodb.repository.MongoRepository;

public interface EurRepository extends MongoRepository<Eur, String> {
    Eur findTopByOrderByDateDesc();
}
