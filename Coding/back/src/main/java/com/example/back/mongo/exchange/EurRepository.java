package com.example.back.mongo.exchange;

import org.springframework.data.mongodb.repository.MongoRepository;
import java.util.List;

public interface EurRepository extends MongoRepository<Eur, String> {
    Eur findTopByOrderByDateDesc();

    List<Eur> findTop30ByOrderByDateDesc();
}
