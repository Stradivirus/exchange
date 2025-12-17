package com.example.back.mongo.commodities;

import org.springframework.data.mongodb.repository.MongoRepository;
import java.util.List;
public interface CopperRepository extends MongoRepository<Copper, String> {
    Copper findTopByOrderByDateDesc();

    List<Copper> findTop30ByOrderByDateDesc();
}
