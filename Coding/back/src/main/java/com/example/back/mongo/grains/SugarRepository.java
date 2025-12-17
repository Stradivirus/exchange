package com.example.back.mongo.grains;

import org.springframework.data.mongodb.repository.MongoRepository;
import java.util.List; // 필수 추가

public interface SugarRepository extends MongoRepository<Sugar, String> {
    Sugar findTopByOrderByDateDesc();

    List<Sugar> findTop30ByOrderByDateDesc();
}
