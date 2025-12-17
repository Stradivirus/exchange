package com.example.back.mongo.stock;

import org.springframework.data.mongodb.repository.MongoRepository;
import java.util.List;

public interface Sp500Repository extends MongoRepository<Sp500, String> {
    Sp500 findTopByOrderByDateDesc();

    List<Sp500> findTop30ByOrderByDateDesc();
}
