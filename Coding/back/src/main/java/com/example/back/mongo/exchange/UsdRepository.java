package com.example.back.mongo.exchange;

import org.springframework.data.mongodb.repository.MongoRepository;
import java.util.List;

public interface UsdRepository extends MongoRepository<Usd, String> {
    Usd findTopByOrderByDateDesc();

    List<Usd> findTop30ByOrderByDateDesc();
}
