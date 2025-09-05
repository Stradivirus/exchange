package com.example.back.mongo.commodities_index;

import org.springframework.data.mongodb.repository.MongoRepository;

public interface DxyRepository extends MongoRepository<Dxy, String> {
    Dxy findTopByOrderByDateDesc();
}
