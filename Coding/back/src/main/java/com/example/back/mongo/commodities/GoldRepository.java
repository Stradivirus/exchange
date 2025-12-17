package com.example.back.mongo.commodities;

import org.springframework.data.mongodb.repository.MongoRepository;
import java.util.List;

public interface GoldRepository extends MongoRepository<Gold, String> {
    Gold findTopByOrderByDateDesc();

    List<Gold> findTop30ByOrderByDateDesc();
}
