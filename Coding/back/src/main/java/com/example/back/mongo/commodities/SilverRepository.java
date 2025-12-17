package com.example.back.mongo.commodities;

import org.springframework.data.mongodb.repository.MongoRepository;
import java.util.List;

public interface SilverRepository extends MongoRepository<Silver, String> {
    Silver findTopByOrderByDateDesc();

    List<Silver> findTop30ByOrderByDateDesc();
}
