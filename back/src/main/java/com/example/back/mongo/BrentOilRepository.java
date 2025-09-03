package com.example.back.mongo;

import org.springframework.data.mongodb.repository.MongoRepository;

public interface BrentOilRepository extends MongoRepository<BrentOil, String> {
    BrentOil findTopByOrderByDateDesc();
}
