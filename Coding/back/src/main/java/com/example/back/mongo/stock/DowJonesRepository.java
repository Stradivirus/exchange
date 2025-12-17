package com.example.back.mongo.stock;

import org.springframework.data.mongodb.repository.MongoRepository;
import java.util.List;

public interface DowJonesRepository extends MongoRepository<DowJones, String> {
    DowJones findTopByOrderByDateDesc();

    List<DowJones> findTop30ByOrderByDateDesc();
}
