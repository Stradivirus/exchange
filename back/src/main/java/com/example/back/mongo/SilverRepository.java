package com.example.back.mongo;

import org.springframework.data.mongodb.repository.MongoRepository;

public interface SilverRepository extends MongoRepository<Silver, String> {
    Silver findTopByOrderByDateDesc();
}
