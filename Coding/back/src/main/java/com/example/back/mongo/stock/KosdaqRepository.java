package com.example.back.mongo.stock;

import org.springframework.data.mongodb.repository.MongoRepository;
import java.util.List;

public interface KosdaqRepository extends MongoRepository<Kosdaq, String> {
    Kosdaq findTopByOrderByDateDesc();

    List<Kosdaq> findTop30ByOrderByDateDesc();
}
