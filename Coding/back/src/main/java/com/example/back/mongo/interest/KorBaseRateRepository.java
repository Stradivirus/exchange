package com.example.back.mongo.interest;

import org.springframework.data.mongodb.repository.MongoRepository;
import java.util.List;

public interface KorBaseRateRepository extends MongoRepository<KorBaseRate, String> {
    KorBaseRate findTopByOrderByDateDesc();

    List<KorBaseRate> findTop30ByOrderByDateDesc();
}
