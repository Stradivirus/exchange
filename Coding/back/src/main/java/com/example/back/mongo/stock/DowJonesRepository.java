package com.example.back.mongo.stock;

import org.springframework.data.mongodb.repository.MongoRepository;

public interface DowJonesRepository extends MongoRepository<DowJones, String> {
    DowJones findTopByOrderByDateDesc();
}
