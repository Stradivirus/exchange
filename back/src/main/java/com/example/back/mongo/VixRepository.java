package com.example.back.mongo;

import org.springframework.data.mongodb.repository.MongoRepository;

public interface VixRepository extends MongoRepository<Vix, String> {
    Vix findTopByOrderByDateDesc();
}
