package com.example.back.mongo;

import org.springframework.data.mongodb.repository.MongoRepository;

public interface KosdaqRepository extends MongoRepository<Kosdaq, String> {
    Kosdaq findTopByOrderByDateDesc();
}
