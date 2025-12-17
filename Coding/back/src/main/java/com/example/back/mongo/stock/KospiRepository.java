package com.example.back.mongo.stock;

import org.springframework.data.mongodb.repository.MongoRepository;
import java.util.List;

public interface KospiRepository extends MongoRepository<Kospi, String> {
    Kospi findTopByOrderByDateDesc();

    List<Kospi> findTop30ByOrderByDateDesc();
}
