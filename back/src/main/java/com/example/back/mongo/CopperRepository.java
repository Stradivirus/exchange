package com.example.back.mongo;

import org.springframework.data.mongodb.repository.MongoRepository;

public interface CopperRepository extends MongoRepository<Copper, String> {
    Copper findTopByOrderByDateDesc();
}
