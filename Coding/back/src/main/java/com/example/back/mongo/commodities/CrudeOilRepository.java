package com.example.back.mongo.commodities;

import org.springframework.data.mongodb.repository.MongoRepository;
import java.util.List;

public interface CrudeOilRepository extends MongoRepository<CrudeOil, String> {
    CrudeOil findTopByOrderByDateDesc();

    List<CrudeOil> findTop30ByOrderByDateDesc();
}
