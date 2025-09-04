package com.example.back.mongo;

import org.springframework.data.mongodb.repository.MongoRepository;

public interface KospiRepository extends MongoRepository<Kospi, String> {
    Kospi findTopByOrderByDateDesc();
}
