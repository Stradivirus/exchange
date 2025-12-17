package com.example.back.mongo.stock;

import org.springframework.data.mongodb.repository.MongoRepository;
import java.util.List;

public interface NasdaqRepository extends MongoRepository<Nasdaq, String> {
    Nasdaq findTopByOrderByDateDesc();

    List<Nasdaq> findTop30ByOrderByDateDesc();
}
