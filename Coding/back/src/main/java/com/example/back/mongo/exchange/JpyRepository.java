package com.example.back.mongo.exchange;

import org.springframework.data.mongodb.repository.MongoRepository;
import java.util.List;

public interface JpyRepository extends MongoRepository<Jpy, String> {
    Jpy findTopByOrderByDateDesc();

    List<Jpy> findTop30ByOrderByDateDesc();
}
