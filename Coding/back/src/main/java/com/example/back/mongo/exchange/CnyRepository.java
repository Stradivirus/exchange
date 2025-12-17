package com.example.back.mongo.exchange;

import org.springframework.data.mongodb.repository.MongoRepository;
import java.util.List;

public interface CnyRepository extends MongoRepository<Cny, String> {
    Cny findTopByOrderByDateDesc();

    List<Cny> findTop30ByOrderByDateDesc();
}
