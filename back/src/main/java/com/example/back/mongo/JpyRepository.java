package com.example.back.mongo;

import org.springframework.data.mongodb.repository.MongoRepository;

public interface JpyRepository extends MongoRepository<Jpy, String> {
    Jpy findTopByOrderByDateDesc();
}
