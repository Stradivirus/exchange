package com.example.back.mongo;

import org.springframework.data.mongodb.repository.MongoRepository;

public interface DowJonesRepository extends MongoRepository<DowJones, String> {
    DowJones findTopByOrderByDateDesc();
}
