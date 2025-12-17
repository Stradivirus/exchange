package com.example.back.mongo.commodities;

import org.springframework.data.mongodb.repository.MongoRepository;
import java.util.List;
public interface BrentOilRepository extends MongoRepository<BrentOil, String> {
    BrentOil findTopByOrderByDateDesc();

    List<BrentOil> findTop30ByOrderByDateDesc();
}
