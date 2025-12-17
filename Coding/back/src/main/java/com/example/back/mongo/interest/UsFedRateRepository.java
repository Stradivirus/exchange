package com.example.back.mongo.interest;

import org.springframework.data.mongodb.repository.MongoRepository;
import java.util.List;

public interface UsFedRateRepository extends MongoRepository<UsFedRate, String> {
    UsFedRate findTopByOrderByDateDesc();

    List<UsFedRate> findTop30ByOrderByDateDesc();
}
