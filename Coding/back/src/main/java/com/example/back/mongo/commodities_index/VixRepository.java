package com.example.back.mongo.commodities_index;

import org.springframework.data.mongodb.repository.MongoRepository;

public interface VixRepository extends MongoRepository<Vix, String> {
    Vix findTopByOrderByDateDesc();
}
