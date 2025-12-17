package com.example.back.mongo.commodities_index;

import org.springframework.data.mongodb.repository.MongoRepository;
import java.util.List;

public interface VixRepository extends MongoRepository<Vix, String> {
    Vix findTopByOrderByDateDesc();

    List<Vix> findTop30ByOrderByDateDesc();
}
