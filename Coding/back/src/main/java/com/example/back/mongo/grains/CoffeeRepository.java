package com.example.back.mongo.grains;

import org.springframework.data.mongodb.repository.MongoRepository;
import java.util.List; // 필수 추가

public interface CoffeeRepository extends MongoRepository<Coffee, String> {
    Coffee findTopByOrderByDateDesc();

    List<Coffee> findTop30ByOrderByDateDesc();
}
