package com.example.back.mongo.commodities_index;

import org.springframework.data.mongodb.repository.MongoRepository;
import java.util.List;

public interface DxyRepository extends MongoRepository<Dxy, String> {
    Dxy findTopByOrderByDateDesc();

    List<Dxy> findTop30ByOrderByDateDesc();
}
