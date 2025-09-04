package com.example.back.mongo;

import org.springframework.data.mongodb.repository.MongoRepository;

public interface DxyRepository extends MongoRepository<Dxy, String> {
    Dxy findTopByOrderByDateDesc();
}
